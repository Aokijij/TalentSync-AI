# ruff: noqa: F811
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest
from test_account_security import browser, csrf  # noqa: F401
from test_api_flows import client, register  # noqa: F401

from app.api.deps import get_social_identity_provider
from app.application.errors import UseCaseError
from app.domain.services.authentication import token_digest
from app.infrastructure.database.models import (
    OAuthAttempt,
    SocialIdentity,
    User,
    UserSession,
)
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


class FakeProvider:
    calls = 0

    def configured(self, provider):
        return provider in {"github", "google"}

    def authorization_url(self, provider, state, challenge, nonce):
        assert len(challenge) == 43
        assert nonce == token_digest(state)
        return f"https://{provider}.example/authorize?state={state}"

    def exchange(self, provider, code, verifier, nonce):
        self.calls += 1
        assert len(verifier) >= 43 and len(nonce) == 64
        if code == "outage":
            raise UseCaseError(status_code=502, detail="No disponible")
        return {"subject": "immutable-123", "email": "social@example.com", "name": "Persona social"}


@pytest.fixture
def social(browser):
    provider = FakeProvider()
    browser.app.dependency_overrides[get_social_identity_provider] = lambda: provider
    browser.social_provider = provider
    return browser


def start(social, provider="github"):
    response = social.post(f"/api/v1/auth/social/{provider}/start")
    assert response.status_code == 200, response.text
    assert "HttpOnly" in response.headers["set-cookie"]
    return parse_qs(urlsplit(response.json()["url"]).query)["state"][0]


def callback(social, state, provider="github", code="valid"):
    return social.get(f"/api/v1/auth/social/{provider}/callback", params={"state": state, "code": code}, follow_redirects=False)


def test_disabled_provider_origin_and_options(social):
    options = social.get("/api/v1/auth/options").json()
    assert [row["id"] for row in options["providers"] if row["enabled"]] == ["google", "github"]
    assert social.post("/api/v1/auth/social/linkedin/start").status_code == 503
    assert social.post("/api/v1/auth/social/github/start", headers={"Origin": "https://attacker.invalid"}).status_code == 403


def test_new_account_cookie_session_returning_identity_and_deletion(social):
    state = start(social)
    binding = social.cookies.get("talentsync_oauth_browser")
    with social.session_factory() as db:
        row = db.query(OAuthAttempt).one()
        assert row.state_hash == token_digest(state) and row.browser_hash == token_digest(binding)
        assert len(row.verifier_cipher) > 100
    response = callback(social, state)
    assert response.status_code == 303 and response.headers["location"].endswith("/bienvenida")
    assert response.headers["cache-control"] == "no-store"
    assert "social@example.com" not in response.headers["location"]
    assert social.cookies.get("talentsync_oauth_browser") is None
    me = social.get("/api/v1/auth/me").json()
    assert me["role"] == "candidate" and me["email_verified"] is True
    assert social.get("/api/v1/profiles/me").json()["skills"] == []
    assert social.put("/api/v1/account/privacy", headers=csrf(social), json={"share_evidence": False, "notify_new_skills": False, "personalize_recommendations": False}).status_code == 200
    social.cookies.set("talentsync_oauth_browser", binding, domain="testserver.local", path="/")
    assert "status=failed" in callback(social, state).headers["location"]
    assert social.social_provider.calls == 1
    with social.session_factory() as db:
        assert db.query(OAuthAttempt).one().verifier_cipher == ""
        assert db.query(UserSession).count() == 1
    assert callback(social, start(social)).headers["location"].endswith("/candidato")
    with social.session_factory() as db:
        user = db.query(User).filter_by(email="social@example.com").one()
        assert db.query(SocialIdentity).count() == 1
        uow = SqlAlchemyUnitOfWork(db)
        uow.delete(user)
        uow.commit()
        assert db.query(SocialIdentity).count() == 0


@pytest.mark.parametrize("reason", ["wrong_browser", "expired", "provider_swap", "no_state"])
def test_browser_state_expiry_and_provider_binding(social, reason):
    state = start(social)
    if reason == "wrong_browser":
        social.cookies.clear()
    elif reason == "expired":
        with social.session_factory() as db:
            db.query(OAuthAttempt).one().expires_at = datetime.utcnow() - timedelta(seconds=1)
            db.commit()
    response = callback(social, "" if reason == "no_state" else state,
                        provider="google" if reason == "provider_swap" else "github")
    assert "status=failed" in response.headers["location"]
    assert social.social_provider.calls == 0
    assert social.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("code", ["", "outage"])
def test_cancelled_or_failed_exchange_consumes_state(social, code):
    state = start(social)
    response = callback(social, state, code=code)
    assert "status=failed" in response.headers["location"]
    with social.session_factory() as db:
        row = db.query(OAuthAttempt).one()
        assert row.used_at is not None and row.verifier_cipher == ""
        assert db.query(SocialIdentity).count() == 0


@pytest.mark.parametrize("role", ["candidate", "company"])
def test_existing_email_does_not_link_or_change_role(social, role):
    register(social, "social", role, **({"company_name": "Empresa", "nit": "SOCIAL-1"} if role == "company" else {}))
    response = callback(social, start(social))
    assert "status=existing" in response.headers["location"]
    with social.session_factory() as db:
        assert db.query(User).one().role.value == role
        assert db.query(SocialIdentity).count() == 0
        assert db.query(UserSession).count() == 0


def test_social_login_preserves_mfa_and_consumes_pending_challenge(social):
    callback(social, start(social))
    recovery = "one-use-recovery"
    with social.session_factory() as db:
        user = db.query(User).one()
        user.mfa_enabled = True
        user.recovery_codes = [token_digest(recovery)]
        from app.infrastructure.security.accounts import AccountSecurity
        user.mfa_secret = AccountSecurity().encrypt_secret("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ")
        db.commit()
    response = callback(social, start(social))
    assert "status=mfa" in response.headers["location"]
    assert social.cookies.get("talentsync_session") is None
    assert social.get("/api/v1/auth/me").status_code == 401
    pending = social.cookies.get("talentsync_social_mfa")
    assert social.post("/api/v1/auth/social/complete", json={"code": "wrong-code"}).status_code == 401
    assert social.post("/api/v1/auth/social/complete", json={"code": recovery}).status_code == 200
    assert social.get("/api/v1/auth/me").json()["mfa_enabled"] is True
    social.cookies.set("talentsync_social_mfa", pending, domain="testserver.local", path="/")
    assert social.post("/api/v1/auth/social/complete", json={"code": recovery}).status_code == 401
    with social.session_factory() as db:
        assert db.query(UserSession).count() == 2


def test_returning_subject_does_not_overwrite_email(social):
    callback(social, start(social))
    social.social_provider.exchange = lambda *args: {"subject": "immutable-123", "email": "changed@example.com", "name": "Cambio"}
    assert callback(social, start(social)).headers["location"].endswith("/candidato")
    assert social.get("/api/v1/auth/me").json()["email"] == "social@example.com"
