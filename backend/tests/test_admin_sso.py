# ruff: noqa: F811
import json
import time
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from test_account_security import browser, login  # noqa: F401
from test_api_flows import client, register  # noqa: F401
from test_social_providers import configuration

from app.api.deps import get_social_identity_provider
from app.application.errors import UseCaseError
from app.application.use_cases.admin_sso import provision
from app.core.config import settings
from app.domain.entities.enums import UserRole
from app.domain.services.authentication import totp
from app.infrastructure.database.models import (
    AccountToken,
    SocialIdentity,
    User,
    UserSession,
)
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.security.accounts import AccountSecurity
from app.infrastructure.security.social import SocialIdentityProvider

SECRET = "JBSWY3DPEHPK3PXP"


class Workspace:
    def configured(self, provider): return provider == "workspace"
    def authorization_url(self, provider, state, challenge, nonce):
        assert provider == "workspace" and len(challenge) == 43 and len(nonce) == 64
        return f"https://accounts.example.com/authorize?state={state}"
    def exchange(self, provider, code, verifier, nonce):
        assert provider == "workspace" and len(verifier) >= 43
        return {"subject": "staff-sub", "email": "staff@example.com", "name": "Staff"}


@pytest.fixture
def corporate(browser, monkeypatch):
    monkeypatch.setattr(settings, "workspace_domain", "example.com")
    browser.app.dependency_overrides[get_social_identity_provider] = lambda: Workspace()
    return browser


def staff(corporate, mfa=False, bind=True):
    account, headers = register(corporate, "staff")
    with corporate.session_factory() as db:
        user = db.get(User, account["id"])
        user.role = UserRole.ADMIN
        user.mfa_enabled = mfa
        if mfa: user.mfa_secret = AccountSecurity().encrypt_secret(SECRET)
        db.commit()
        if bind: provision(SqlAlchemyUnitOfWork(db), account["email"], "staff-sub")
    return account, headers


def begin(corporate):
    result = corporate.post("/api/v1/auth/admin-sso/start")
    assert result.status_code == 200, result.text
    assert "HttpOnly" in result.headers["set-cookie"]
    return parse_qs(urlsplit(result.json()["url"]).query)["state"][0]


def finish(corporate, state):
    return corporate.get("/api/v1/auth/admin-sso/callback", params={"state": state, "code": "valid"}, follow_redirects=False)


def test_sso_only_admits_provisioned_subjects_and_never_creates_or_promotes_accounts(corporate):
    account, _ = staff(corporate, bind=False)
    assert "status=failed" in finish(corporate, begin(corporate)).headers["location"]
    assert corporate.post("/api/v1/auth/social/workspace/start").status_code == 503
    with corporate.session_factory() as db:
        assert db.query(User).count() == 1 and db.query(SocialIdentity).count() == 0
        provision(SqlAlchemyUnitOfWork(db), account["email"], "staff-sub")
    state = begin(corporate)
    # Candidate callback cannot consume an administrative attempt.
    assert "status=failed" in corporate.get("/api/v1/auth/social/workspace/callback", params={"state": state, "code": "valid"}, follow_redirects=False).headers["location"]
    result = finish(corporate, state)
    assert result.headers["location"].endswith("/seguridad")
    assert corporate.get("/api/v1/auth/me").json()["role"] == "admin"
    assert corporate.get("/api/v1/admin/stats").status_code == 403
    assert "status=failed" in finish(corporate, state).headers["location"]
    with corporate.session_factory() as db:
        assert db.query(UserSession).one().authentication_method == "workspace"


def test_admin_sso_requires_the_bound_browser_and_rejects_untrusted_origins(corporate):
    staff(corporate)
    assert corporate.post("/api/v1/auth/admin-sso/start", headers={"Origin": "https://attacker.invalid"}).status_code == 403
    state = begin(corporate)
    corporate.cookies.delete("talentsync_admin_sso_browser")
    assert "status=failed" in finish(corporate, state).headers["location"]
    assert corporate.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("fault", [None, "expired", "revoked", "domain", "role"])
def test_admin_mfa_is_separate_one_time_and_rechecks_provisioning(corporate, monkeypatch, fault):
    account, _ = staff(corporate, mfa=True)
    monkeypatch.setattr(settings, "admin_sso_required", True)
    result = finish(corporate, begin(corporate))
    assert result.headers["location"].endswith("/acceso-corporativo?status=mfa")
    assert corporate.cookies.get("talentsync_session") is None
    assert corporate.post("/api/v1/auth/social/complete", json={"code": totp(SECRET, int(time.time() // 30))}).status_code == 401
    with corporate.session_factory() as db:
        if fault == "expired": db.query(AccountToken).filter_by(purpose="admin_sso_mfa").one().expires_at = datetime.utcnow() - timedelta(seconds=1)
        if fault == "role": db.get(User, account["id"]).role = UserRole.CANDIDATE
        if fault == "revoked": provision(SqlAlchemyUnitOfWork(db), account["email"])
        db.commit()
    if fault == "domain": monkeypatch.setattr(settings, "workspace_domain", "other.example.com")
    result = corporate.post("/api/v1/auth/admin-sso/complete", json={"code": totp(SECRET, int(time.time() // 30))})
    if fault:
        assert result.status_code in {401, 403}
        assert corporate.cookies.get("talentsync_session") is None
    else:
        assert result.status_code == 200, result.text
        assert corporate.get("/api/v1/admin/stats").status_code == 200
        assert corporate.post("/api/v1/auth/admin-sso/complete", json={"code": totp(SECRET, int(time.time() // 30))}).status_code == 401
        with corporate.session_factory() as db:
            session = db.query(UserSession).one()
            assert session.authentication_method == "workspace" and session.mfa_verified is True


def test_required_sso_disables_password_existing_sessions_and_legacy_admin_tokens(corporate, monkeypatch):
    account, headers = staff(corporate)
    result = corporate.post("/api/v1/auth/session/admin/login", json={"email": account["email"], "password": "Test-password-2026!"})
    assert result.status_code == 200, result.text
    monkeypatch.setattr(settings, "admin_sso_required", True)
    assert corporate.get("/api/v1/auth/me").status_code == 401
    assert corporate.post("/api/v1/auth/session/admin/login", json={"email": account["email"], "password": "Test-password-2026!"}).status_code == 403
    corporate.cookies.clear()
    monkeypatch.setattr(settings, "session_auth_enabled", False)
    assert corporate.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert corporate.post("/api/v1/auth/admin/login", json={"email": account["email"], "password": "Test-password-2026!"}).status_code == 410


def test_local_provisioning_cannot_promote_candidates_or_transfer_bindings(corporate):
    account, _ = staff(corporate)
    register(corporate, "unprivileged")
    with corporate.session_factory() as db:
        uow = SqlAlchemyUnitOfWork(db)
        with pytest.raises(UseCaseError) as error: provision(uow, "unprivileged@example.com", "other-sub")
        assert error.value.status_code == 422
        with pytest.raises(UseCaseError) as error: provision(uow, account["email"], "other-sub")
        assert error.value.status_code == 409


@pytest.mark.parametrize("domain", ["example.com", "other.example.com", None])
def test_workspace_verifies_hosted_domain_in_signed_claims(domain):
    config = configuration(oauth_workspace_client_id="workspace-id", oauth_workspace_client_secret="secret", workspace_domain="example.com")
    adapter = SocialIdentityProvider(config)
    query = parse_qs(urlsplit(adapter.authorization_url("workspace", "state", "challenge", "nonce")).query)
    assert query["hd"] == ["example.com"] and query["redirect_uri"][0].endswith("/auth/admin-sso/callback")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    public.update(kid="key-1", alg="RS256", use="sig")
    claims = {"sub": "staff-sub", "iss": "https://accounts.google.com", "aud": "workspace-id", "iat": int(time.time()),
              "exp": int(time.time()) + 300, "nonce": "nonce", "email": "staff@example.com", "email_verified": True}
    if domain: claims["hd"] = domain
    token = jwt.encode(claims, key, algorithm="RS256", headers={"kid": "key-1"})
    adapter.transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"id_token": token} if request.url.path == "/token" else {"keys": [public]}))
    if domain == "example.com":
        assert adapter.exchange("workspace", "code", "verifier", "nonce")["subject"] == "staff-sub"
    else:
        with pytest.raises(UseCaseError): adapter.exchange("workspace", "code", "verifier", "nonce")
