import json
import time
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.application.errors import UseCaseError
from app.infrastructure.security.social import SocialIdentityProvider


def configuration(**overrides):
    return SimpleNamespace(environment="development", session_auth_enabled=True,
        public_app_url="http://127.0.0.1:5173", oauth_github_client_id="github-id", oauth_github_client_secret="secret",
        oauth_google_client_id="google-id", oauth_google_client_secret="secret", **overrides)


def test_authorize_only_known_providers_pkce_scopes_and_local_callback():
    adapter = SocialIdentityProvider(configuration())
    for provider in ("github", "google"):
        query = parse_qs(urlsplit(adapter.authorization_url(provider, "state", "challenge", "nonce")).query)
        assert query["code_challenge_method"] == ["S256"]
        assert query["redirect_uri"] == [f"http://127.0.0.1:5173/api/v1/auth/social/{provider}/callback"]
        assert "repo" not in query["scope"][0]
    assert adapter.configured("https://attacker.invalid") is False
    adapter.settings.public_app_url = "http://remote.example.com"
    assert adapter.configured("github") is False
    for invalid_url in ("https:///", "http://[", "https://example.com:invalid", "https://user:password@example.com", "https://example.com/?next=other"):
        adapter.settings.public_app_url = invalid_url
        assert adapter.configured("github") is False
    adapter.settings.public_app_url = "https://app.example.com"
    adapter.settings.session_auth_enabled = False
    assert adapter.configured("google") is False


@pytest.mark.parametrize("verified", [True, False])
def test_github_requires_primary_verified_email_and_sends_verifier(verified):
    calls = []
    def handle(request):
        calls.append(request)
        if request.url.path.endswith("access_token"):
            form = parse_qs(request.content.decode())
            assert form["code_verifier"] == ["pkce-secret"] and form["code"] == ["code"]
            return httpx.Response(200, json={"access_token": "private-token"})
        assert request.headers["Authorization"] == "Bearer private-token"
        if request.url.path == "/user":
            return httpx.Response(200, json={"id": 42, "login": "usuario", "email": "ignored@example.com"})
        return httpx.Response(200, json=[{"email": "verified@example.com", "verified": verified, "primary": True}])
    adapter = SocialIdentityProvider(configuration(), httpx.MockTransport(handle))
    if verified:
        assert adapter.exchange("github", "code", "pkce-secret", "nonce") == {"subject": "42", "email": "verified@example.com", "name": "usuario"}
    else:
        with pytest.raises(UseCaseError):
            adapter.exchange("github", "code", "pkce-secret", "nonce")
    assert len(calls) == 3


@pytest.mark.parametrize("fault", [None, "nonce", "audience", "expired", "issuer", "unverified", "signature", "multiple_audiences", "authorized_party"])
def test_google_verifies_signature_claims_nonce_and_email(fault):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    public.update(kid="key-1", alg="RS256", use="sig")
    claims = {"sub": "google-sub", "iss": "https://accounts.google.com", "aud": "google-id", "iat": int(time.time()),
              "exp": int(time.time()) + 300, "nonce": "nonce", "email": "google@example.com", "email_verified": True}
    if fault == "nonce": claims["nonce"] = "other"
    if fault == "audience": claims["aud"] = "other-id"
    if fault == "issuer": claims["iss"] = "https://attacker.invalid"
    if fault == "expired": claims["exp"] = int(time.time()) - 1
    if fault == "unverified": claims["email_verified"] = False
    if fault == "multiple_audiences": claims["aud"] = ["google-id", "other-client"]
    if fault == "authorized_party": claims["azp"] = "other-client"
    token = jwt.encode(claims, other_key if fault == "signature" else key, algorithm="RS256", headers={"kid": "key-1"})
    def handle(request):
        if request.url.path == "/token":
            assert parse_qs(request.content.decode())["code_verifier"] == ["verifier"]
            return httpx.Response(200, json={"id_token": token})
        assert request.url.host == "www.googleapis.com"
        return httpx.Response(200, json={"keys": [public]})
    adapter = SocialIdentityProvider(configuration(), httpx.MockTransport(handle))
    if fault:
        with pytest.raises(UseCaseError) as error:
            adapter.exchange("google", "code", "verifier", "nonce")
        assert error.value.status_code == 502 and token not in error.value.detail
    else:
        assert adapter.exchange("google", "code", "verifier", "nonce")["subject"] == "google-sub"


def test_provider_failure_is_sanitized():
    adapter = SocialIdentityProvider(configuration(), httpx.MockTransport(lambda request: httpx.Response(400, json={"error": "secret-token"})))
    with pytest.raises(UseCaseError) as error:
        adapter.exchange("github", "code-secret", "verifier-secret", "nonce")
    assert "secret" not in error.value.detail
