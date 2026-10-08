import json
import time
from urllib.parse import parse_qs, urlsplit

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from test_account_security import browser  # noqa: F401
from test_api_flows import client  # noqa: F401
from test_social_access import callback, social, start  # noqa: F401
from test_social_providers import configuration

from app.application.errors import UseCaseError
from app.infrastructure.security.social import SocialIdentityProvider


def configured():
    settings = configuration(oauth_linkedin_client_id="linkedin-id", oauth_linkedin_client_secret="secret")
    settings.public_app_url = "https://app.example.com"
    return settings


def test_linkedin_authorization_is_fixed_and_requires_https():
    settings = configured()
    adapter = SocialIdentityProvider(settings)
    url = urlsplit(adapter.authorization_url("linkedin", "state", "challenge", "nonce"))
    assert url.hostname == "www.linkedin.com" and url.path == "/oauth/v2/authorization"
    query = parse_qs(url.query)
    assert query["scope"] == ["openid email profile"] and query["nonce"] == ["nonce"]
    assert query["code_challenge_method"] == ["S256"]
    settings.public_app_url = "http://127.0.0.1:5173"
    assert adapter.configured("linkedin") is False


def test_linkedin_uses_existing_one_time_browser_bound_candidate_flow(social):  # noqa: F811
    social.social_provider.configured = lambda provider: provider == "linkedin"
    state = start(social, provider="linkedin")
    assert callback(social, state, provider="linkedin").headers["location"].endswith("/bienvenida")
    assert social.get("/api/v1/auth/me").json()["role"] == "candidate"
    assert social.get("/api/v1/account/social-identities").json()[0]["provider"] == "linkedin"
    assert "status=failed" in callback(social, state, provider="linkedin").headers["location"]


@pytest.mark.parametrize("fault", [None, "signature", "issuer", "audience", "nonce", "missing_nonce", "expired", "subject", "missing_email", "unverified_email"])
def test_linkedin_validates_id_token_and_subject_bound_userinfo(fault):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    public.update(kid="key-1", alg="RS256", use="sig")
    claims = {"sub": "linked-sub", "iss": "https://www.linkedin.com", "aud": "linkedin-id", "iat": int(time.time()),
              "exp": int(time.time()) + 300, "nonce": "nonce"}
    if fault == "issuer": claims["iss"] = "https://accounts.google.com"
    if fault == "audience": claims["aud"] = "other-client"
    if fault == "nonce": claims["nonce"] = "other-nonce"
    if fault == "missing_nonce": claims.pop("nonce")
    if fault == "expired": claims["exp"] = int(time.time()) - 1
    signer = rsa.generate_private_key(public_exponent=65537, key_size=2048) if fault == "signature" else key
    token = jwt.encode(claims, signer, algorithm="RS256", headers={"kid": "key-1"})
    def handle(request):
        if request.url.path.endswith("accessToken"):
            assert parse_qs(request.content.decode())["code_verifier"] == ["verifier"]
            return httpx.Response(200, json={"id_token": token, "access_token": "transient-token"})
        if request.url.path == "/oauth/openid/jwks":
            return httpx.Response(200, json={"keys": [public]})
        assert request.url.host == "api.linkedin.com" and request.url.path == "/v2/userinfo"
        assert request.headers["Authorization"] == "Bearer transient-token"
        info = {"sub": "other-sub" if fault == "subject" else "linked-sub", "email": "linkedin@example.com", "email_verified": fault != "unverified_email", "name": "Persona"}
        if fault == "missing_email": info.pop("email")
        return httpx.Response(200, json=info)
    adapter = SocialIdentityProvider(configured(), httpx.MockTransport(handle))
    if fault:
        with pytest.raises(UseCaseError) as error:
            adapter.exchange("linkedin", "code", "verifier", "nonce")
        assert error.value.status_code == 502 and "transient-token" not in error.value.detail
    else:
        assert adapter.exchange("linkedin", "code", "verifier", "nonce")["subject"] == "linked-sub"
