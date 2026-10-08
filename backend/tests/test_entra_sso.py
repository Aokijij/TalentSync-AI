# ruff: noqa: F811
import json
import time
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from test_account_security import browser  # noqa: F401
from test_admin_sso import SECRET, begin, finish
from test_api_flows import client, register  # noqa: F401
from test_social_providers import configuration

from app.api.deps import get_corporate_configuration, get_social_identity_provider
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

TENANT = "10000000-0000-4000-8000-000000000001"
CLIENT = "20000000-0000-4000-8000-000000000002"
OBJECT = "30000000-0000-4000-8000-000000000003"
SUBJECT = f"{TENANT}:{OBJECT}"
OTHER = "40000000-0000-4000-8000-000000000004"


def config(**overrides):
    values = {"entra_tenant_id": TENANT, "oauth_entra_client_id": CLIENT, "oauth_entra_client_secret": "only-test-secret"}
    return configuration(**{**values, **overrides})


@pytest.mark.parametrize("tenant", ["common", "organizations", "consumers", "https://attacker.invalid", "not-a-guid", "{" + TENANT + "}"])
def test_entra_accepts_only_canonical_tenant_guids(tenant):
    assert SocialIdentityProvider(config(entra_tenant_id=tenant)).configured("entra") is False


def test_entra_authorization_is_tenant_specific_minimal_and_uses_admin_callback():
    adapter = SocialIdentityProvider(config())
    url = urlsplit(adapter.authorization_url("entra", "state", "challenge", "nonce"))
    params = parse_qs(url.query)
    assert url.netloc == "login.microsoftonline.com"
    assert url.path == f"/{TENANT}/oauth2/v2.0/authorize"
    assert params["scope"] == ["openid profile"]
    assert params["nonce"] == ["nonce"] and params["code_challenge_method"] == ["S256"]
    assert params["redirect_uri"] == ["http://127.0.0.1:5173/api/v1/auth/admin-sso/callback"]
    assert SocialIdentityProvider(config(oauth_entra_client_id="not-an-application-guid")).configured("entra") is False
    adapter.settings.public_app_url = "http://[::1]:5173"
    assert adapter.configured("entra") is False


@pytest.mark.parametrize("fault", [None, "signature", "nonce", "tenant", "object", "subject", "issuer", "audience", "audiences", "version", "expired", "future", "missing_nbf", "key_issuer", "key_use", "key_algorithm", "algorithm"])
def test_entra_validates_signed_identity_and_does_not_authorize_using_email(fault):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    public.update(kid="key-1", alg="RS256", use="sig", issuer="https://login.microsoftonline.com/{tenantid}/v2.0")
    now = int(time.time())
    claims = {"iss": f"https://login.microsoftonline.com/{TENANT}/v2.0", "aud": CLIENT, "sub": "pairwise-user", "tid": TENANT,
              "oid": OBJECT, "ver": "2.0", "nonce": "nonce", "iat": now, "nbf": now-1, "exp": now+300,
              "preferred_username": "mutable@example.com"}
    if fault == "nonce": claims["nonce"] = "other"
    if fault == "tenant": claims["tid"] = OTHER
    if fault == "object": claims["oid"] = "mutable@example.com"
    if fault == "subject": del claims["sub"]
    if fault == "issuer": claims["iss"] = f"https://login.microsoftonline.com/{OTHER}/v2.0"
    if fault == "audience": claims["aud"] = OTHER
    if fault == "audiences": claims["aud"] = [CLIENT, OTHER]; claims["azp"] = CLIENT
    if fault == "version": claims["ver"] = "1.0"
    if fault == "expired": claims["exp"] = now-1
    if fault == "future": claims["nbf"] = now+60
    if fault == "missing_nbf": del claims["nbf"]
    if fault == "key_issuer": public["issuer"] = f"https://login.microsoftonline.com/{OTHER}/v2.0"
    if fault == "key_use": public["use"] = "enc"
    if fault == "key_algorithm": public["alg"] = "RS512"
    signer = rsa.generate_private_key(public_exponent=65537, key_size=2048) if fault == "signature" else key
    token = jwt.encode(claims, "only-test-hmac-secret" if fault == "algorithm" else signer,
                       algorithm="HS256" if fault == "algorithm" else "RS256", headers={"kid": "key-1"})
    requests = []
    def handle(request):
        requests.append(request)
        assert request.url.host == "login.microsoftonline.com"
        if request.url.path.endswith("/token"):
            assert parse_qs(request.content.decode())["code_verifier"] == ["verifier"]
            return httpx.Response(200, json={"id_token": token, "access_token": "unused-and-not-stored"})
        assert request.url.path == f"/{TENANT}/discovery/v2.0/keys"
        return httpx.Response(200, json={"keys": [public]})
    adapter = SocialIdentityProvider(config(), httpx.MockTransport(handle))
    if fault:
        with pytest.raises(UseCaseError) as error: adapter.exchange("entra", "code", "verifier", "nonce")
        assert error.value.status_code == 502 and token not in error.value.detail
    else:
        assert adapter.exchange("entra", "code", "verifier", "nonce")["subject"] == SUBJECT
        assert len(requests) == 2  # No Graph, userinfo, email lookup or refresh token.


class Entra:
    def configured(self, provider): return provider == "entra"
    def authorization_url(self, provider, state, challenge, nonce):
        assert provider == "entra" and len(challenge) == 43 and len(nonce) == 64
        return f"https://accounts.example.com/authorize?state={state}"
    def exchange(self, provider, code, verifier, nonce):
        assert provider == "entra" and len(verifier) >= 43
        return {"subject": SUBJECT, "email": None, "name": "Staff"}


@pytest.fixture
def entra(browser, monkeypatch):
    monkeypatch.setattr(settings, "admin_sso_provider", "entra")
    monkeypatch.setattr(settings, "entra_tenant_id", TENANT)
    monkeypatch.setattr(settings, "oauth_entra_client_id", CLIENT)
    browser.app.dependency_overrides[get_social_identity_provider] = lambda: Entra()
    return browser


def staff(entra, *, bind=True, mfa=True):
    account, headers = register(entra, "entra-staff")
    with entra.session_factory() as db:
        user = db.get(User, account["id"])
        user.role = UserRole.ADMIN
        user.mfa_enabled = mfa
        if mfa: user.mfa_secret = AccountSecurity().encrypt_secret(SECRET)
        db.commit()
        if bind: provision(SqlAlchemyUnitOfWork(db), account["email"], SUBJECT, provider="entra")
    return account, headers


def test_entra_never_autobinds_by_email_or_promotes_accounts(entra):
    account, _ = staff(entra, bind=False, mfa=False)
    assert entra.get("/api/v1/auth/admin-sso/options").json()["provider"] == "Microsoft Entra ID"
    assert "status=failed" in finish(entra, begin(entra)).headers["location"]
    assert entra.post("/api/v1/auth/social/entra/start").status_code == 503
    with entra.session_factory() as db:
        assert db.query(User).count() == 1 and db.query(SocialIdentity).count() == 0
        provision(SqlAlchemyUnitOfWork(db), account["email"], SUBJECT, provider="entra")
    assert finish(entra, begin(entra)).headers["location"].endswith("/seguridad")
    assert entra.get("/api/v1/admin/stats").status_code == 403


@pytest.mark.parametrize("fault", [None, "tenant", "client", "provider", "revoked", "role", "expired"])
def test_entra_mfa_rechecks_provider_authority_role_and_binding(entra, monkeypatch, fault):
    account, _ = staff(entra)
    monkeypatch.setattr(settings, "admin_sso_required", True)
    state = begin(entra)
    assert finish(entra, state).headers["location"].endswith("?status=mfa")
    assert entra.cookies.get("talentsync_session") is None
    if fault == "tenant": monkeypatch.setattr(settings, "entra_tenant_id", OTHER)
    if fault == "client": monkeypatch.setattr(settings, "oauth_entra_client_id", OTHER)
    if fault == "provider": monkeypatch.setattr(settings, "admin_sso_provider", "workspace")
    with entra.session_factory() as db:
        if fault == "revoked": provision(SqlAlchemyUnitOfWork(db), account["email"], provider="entra")
        if fault == "role": db.get(User, account["id"]).role = UserRole.CANDIDATE
        if fault == "expired": db.query(AccountToken).filter_by(purpose="admin_sso_mfa").one().expires_at = datetime.utcnow()-timedelta(seconds=1)
        db.commit()
    code = totp(SECRET, int(time.time() // 30))
    result = entra.post("/api/v1/auth/admin-sso/complete", json={"code": code})
    if fault:
        assert result.status_code in {401, 403, 503}
        assert entra.cookies.get("talentsync_session") is None
    else:
        assert result.status_code == 200, result.text
        assert entra.get("/api/v1/admin/stats").status_code == 200
        with entra.session_factory() as db:
            session = db.query(UserSession).one()
            assert session.authentication_method == "entra"
            assert session.authentication_authority == get_corporate_configuration()["authority"]
        assert entra.post("/api/v1/auth/admin-sso/complete", json={"code": code}).status_code == 401


@pytest.mark.parametrize("fault", ["tenant", "client", "provider"])
def test_callback_rejects_configuration_changed_during_authorization(entra, monkeypatch, fault):
    staff(entra)
    state = begin(entra)
    if fault == "tenant": monkeypatch.setattr(settings, "entra_tenant_id", OTHER)
    if fault == "client": monkeypatch.setattr(settings, "oauth_entra_client_id", OTHER)
    if fault == "provider": monkeypatch.setattr(settings, "admin_sso_provider", "workspace")
    result = finish(entra, state)
    assert any(value in result.headers["location"] for value in ("status=failed", "status=unavailable"))
    assert entra.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("fault", ["tenant", "client", "provider"])
def test_corporate_session_cannot_survive_configuration_switch(entra, monkeypatch, fault):
    staff(entra, mfa=False)
    assert finish(entra, begin(entra)).headers["location"].endswith("/seguridad")
    assert entra.get("/api/v1/auth/me").status_code == 200
    if fault == "tenant": monkeypatch.setattr(settings, "entra_tenant_id", OTHER)
    if fault == "client": monkeypatch.setattr(settings, "oauth_entra_client_id", OTHER)
    if fault == "provider": monkeypatch.setattr(settings, "admin_sso_provider", "workspace")
    assert entra.get("/api/v1/auth/me").status_code == 401
    with entra.session_factory() as db:
        assert db.query(UserSession).one().revoked_at is not None
    monkeypatch.setattr(settings, "entra_tenant_id", TENANT)
    monkeypatch.setattr(settings, "oauth_entra_client_id", CLIENT)
    monkeypatch.setattr(settings, "admin_sso_provider", "entra")
    assert entra.get("/api/v1/auth/me").status_code == 401


def test_provisioning_preserves_provider_namespaces_and_rejects_mutable_subjects(entra):
    account, _ = staff(entra)
    candidate, _ = register(entra, "entra-candidate")
    with entra.session_factory() as db:
        uow = SqlAlchemyUnitOfWork(db)
        for email, subject, provider in [(candidate["email"], SUBJECT, "entra"), (account["email"], "email@example.com", "entra"), (account["email"], SUBJECT, "google")]:
            with pytest.raises(UseCaseError): provision(uow, email, subject, provider=provider)
        with pytest.raises(UseCaseError): provision(uow, account["email"], SUBJECT, provider="entra")
        provision(uow, account["email"], "workspace-sub", provider="workspace")
        provision(uow, account["email"], provider="entra")
        assert db.query(SocialIdentity).one().provider == "workspace"
