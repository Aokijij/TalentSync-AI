import re
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from test_api_flows import client, register  # noqa: F401

from app.core.config import settings
from app.domain.services.authentication import token_digest, totp, verify_totp
from app.infrastructure.database.models import AccountToken, User, UserSession


@pytest.fixture
def browser(client, monkeypatch):  # noqa: F811
    monkeypatch.setattr(settings, "session_auth_enabled", True)
    monkeypatch.setattr(settings, "session_cookie_secure", False)
    monkeypatch.setattr(settings, "local_mail_enabled", True)
    monkeypatch.setattr(settings, "database_url", "sqlite://")
    return client


def login(browser, email="alex@example.com", **options):
    return browser.post("/api/v1/auth/session/login", json={"email": email, "password": "Test-password-2026!", **options})


def csrf(browser):
    return {"X-CSRF-Token": browser.cookies.get("talentsync_csrf")}


def action_token(browser):
    messages = browser.get("/api/v1/dev/mailbox").json()
    link = re.search(r"https?://\S+", messages[0]["body"]).group()
    return parse_qs(urlparse(link).query)["token"][0]


def test_session_cookie_csrf_expiry_and_revocation(browser):
    register(browser, "alex")
    response = login(browser)
    assert response.status_code == 200
    assert "access_token" not in response.json()
    assert "HttpOnly" in response.headers["set-cookie"]
    assert browser.get("/api/v1/auth/me").status_code == 200
    assert browser.put("/api/v1/account/privacy", json={"share_evidence": False, "notify_new_skills": False, "personalize_recommendations": False}).status_code == 403
    assert browser.put("/api/v1/account/privacy", headers=csrf(browser), json={"share_evidence": False, "notify_new_skills": False, "personalize_recommendations": False}).status_code == 200
    with browser.session_factory() as db:
        session = db.query(UserSession).one()
        assert session.token_hash == token_digest(browser.cookies.get("talentsync_session"))
        session.last_seen_at = datetime.utcnow() - timedelta(days=8)
        db.commit()
    assert browser.get("/api/v1/auth/me").status_code == 401
    assert login(browser).status_code == 200
    old_cookie = browser.cookies.get("talentsync_session")
    assert browser.post("/api/v1/auth/session/logout", headers=csrf(browser)).status_code == 200
    browser.cookies.set("talentsync_session", old_cookie)
    assert browser.get("/api/v1/auth/me").status_code == 401


def test_recovery_is_one_use_and_revokes_all_sessions(browser):
    register(browser, "alex")
    login(browser)
    response = browser.post("/api/v1/auth/password/request", json={"email": "alex@example.com"})
    unknown = browser.post("/api/v1/auth/password/request", json={"email": "unknown@example.com"})
    assert response.json() == unknown.json()
    token = action_token(browser)
    with browser.session_factory() as db:
        assert db.query(AccountToken).filter_by(token_hash=token_digest(token)).count() == 1
    payload = {"purpose": "reset", "token": token, "password": "A-new-password-2026!"}
    assert browser.post("/api/v1/auth/action/confirm", json=payload).status_code == 200
    assert browser.post("/api/v1/auth/action/confirm", json=payload).status_code == 400
    assert browser.get("/api/v1/auth/me").status_code == 401
    assert login(browser).status_code == 401
    assert browser.post("/api/v1/auth/session/login", json={"email": "alex@example.com", "password": "A-new-password-2026!"}).status_code == 200


def test_email_confirmation_and_production_mailbox_is_hidden(browser, monkeypatch):
    register(browser, "alex")
    token = action_token(browser)
    assert browser.post("/api/v1/auth/action/confirm", json={"purpose": "verify", "token": token}).status_code == 200
    login(browser)
    assert browser.get("/api/v1/auth/me").json()["email_verified"] is True
    monkeypatch.setattr(settings, "environment", "production")
    assert browser.get("/api/v1/dev/mailbox").status_code == 404


def test_mfa_enrollment_encryption_recovery_and_staff_gate(browser):
    register(browser, "nexo", "company", company_name="Nexo", nit="TEST-1")
    response = login(browser, "nexo@example.com")
    assert response.json()["mfa_setup_required"] is True
    assert browser.get("/api/v1/companies/me").status_code == 403
    setup = browser.post("/api/v1/account/mfa/setup", headers=csrf(browser), json={"password": "Test-password-2026!"}).json()
    import time
    code = totp(setup["secret"], int(time.time() // 30))
    result = browser.post("/api/v1/account/mfa/confirm", headers=csrf(browser), json={"code": code})
    assert result.status_code == 200
    recovery = result.json()["recovery_codes"][0]
    with browser.session_factory() as db:
        user = db.query(User).filter_by(email="nexo@example.com").one()
        assert user.mfa_secret != setup["secret"]
        assert recovery not in user.recovery_codes
    assert browser.get("/api/v1/companies/me").status_code == 200
    browser.post("/api/v1/auth/session/logout", headers=csrf(browser))
    assert login(browser, "nexo@example.com").json() == {"mfa_required": True}
    assert login(browser, "nexo@example.com", code=recovery).status_code == 200
    assert login(browser, "nexo@example.com", code=recovery).status_code == 401
    assert browser.post("/api/v1/auth/login", json={"email": "nexo@example.com", "password": "Test-password-2026!"}).status_code == 410


def test_totp_reference_vector_and_replay_protection():
    secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
    assert totp(secret, 1) == "287082"
    assert verify_totp(secret, "287082", now=59) == 1
    assert verify_totp(secret, "287082", last_counter=1, now=59) is None


def test_origin_and_session_ownership(browser):
    register(browser, "alex")
    assert browser.post("/api/v1/auth/session/login", headers={"Origin": "https://attacker.invalid"}, json={"email": "alex@example.com", "password": "Test-password-2026!"}).status_code == 403
    login(browser)
    assert browser.delete("/api/v1/account/sessions/999", headers=csrf(browser)).status_code == 404
