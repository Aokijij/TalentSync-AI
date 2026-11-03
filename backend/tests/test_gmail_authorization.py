import importlib.util
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

spec = importlib.util.spec_from_file_location("gmail_authorize_setup", Path(__file__).resolve().parents[2] / "scripts/gmail_authorize.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def authorization():
    return module.Authorization({"installed": {"client_id": "synthetic.apps.googleusercontent.com", "client_secret": "PRIVATE-CLIENT"}}, "sender@example.com", "http://127.0.0.1:8765/callback")


def test_authorization_uses_send_only_pkce_offline_and_the_intended_account():
    auth = authorization()
    query = parse_qs(urlsplit(auth.url()).query)
    assert query["scope"][0].split() == ["openid", "email", module.SEND_SCOPE]
    assert query["include_granted_scopes"] == ["false"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["access_type"] == ["offline"]
    assert query["login_hint"] == ["sender@example.com"]
    assert auth.verifier not in auth.url() and auth.client_secret not in auth.url()


@pytest.mark.parametrize("email,verified,scopes,refresh", [
    ("other@example.com", True, module.SEND_SCOPE, "PRIVATE-REFRESH"),
    ("sender@example.com", False, module.SEND_SCOPE, "PRIVATE-REFRESH"),
    ("sender@example.com", True, "openid email", "PRIVATE-REFRESH"),
    ("sender@example.com", True, module.SEND_SCOPE + " https://mail.google.com/", "PRIVATE-REFRESH"),
    ("sender@example.com", True, module.SEND_SCOPE, None),
])
def test_wrong_accounts_or_broader_permissions_cannot_be_saved(email, verified, scopes, refresh):
    auth = authorization()
    def handler(request):
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "PRIVATE-ACCESS", "refresh_token": refresh, "scope": scopes})
        return httpx.Response(200, json={"email": email, "email_verified": verified})
    with pytest.raises(ValueError):
        auth.complete("synthetic-code", auth.state, transport=httpx.MockTransport(handler))


def test_csrf_state_and_single_use_are_enforced_before_any_network_request():
    auth = authorization()
    def handler(request):
        pytest.fail("No request should be made for an invalid state")
    with pytest.raises(ValueError, match="invalid_or_used"):
        auth.complete("synthetic-code", "wrong-state", transport=httpx.MockTransport(handler))
    assert not auth.used


def test_successful_authorization_returns_private_deployment_values_and_cannot_be_replayed():
    auth = authorization()
    def handler(request):
        if request.url.host == "oauth2.googleapis.com":
            assert b"code_verifier=" in request.content
            return httpx.Response(200, json={"access_token": "PRIVATE-ACCESS", "refresh_token": "PRIVATE-REFRESH", "scope": "openid email " + module.SEND_SCOPE})
        assert request.url == "https://openidconnect.googleapis.com/v1/userinfo"
        return httpx.Response(200, json={"email": "sender@example.com", "email_verified": True})
    transport = httpx.MockTransport(handler)
    result = auth.complete("synthetic-code", auth.state, transport=transport)
    assert result["GMAIL_MAIL_REFRESH_TOKEN"] == "PRIVATE-REFRESH"
    assert result["GMAIL_MAIL_SENDER"] == "sender@example.com"
    assert result["LOCAL_MAIL_ENABLED"] == result["RESEND_ENABLED"] == result["SMTP_ENABLED"] == "false"
    with pytest.raises(ValueError, match="invalid_or_used"):
        auth.complete("synthetic-code", auth.state, transport=transport)
