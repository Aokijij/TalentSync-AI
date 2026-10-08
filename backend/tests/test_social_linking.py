# ruff: noqa: F811
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest
from test_account_security import csrf, login
from test_api_flows import register
from test_social_access import browser, callback, client, social, start  # noqa: F401

from app.domain.services.authentication import token_digest
from app.infrastructure.database.models import (
    AccountToken,
    EventLog,
    OAuthAttempt,
    SocialIdentity,
    User,
    UserSession,
)
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.security.accounts import AccountSecurity

PASSWORD = "Test-password-2026!"


def prepare(social):
    user, _ = register(social, "alex")
    assert login(social).status_code == 200
    return user


def begin_link(social, provider="github", **credentials):
    response = social.post(f"/api/v1/account/social-identities/{provider}/link", headers=csrf(social),
                           json={"password": PASSWORD, **credentials})
    assert response.status_code == 200, response.text
    return parse_qs(urlsplit(response.json()["url"]).query)["state"][0]


def unlink(social, provider="github", **credentials):
    return social.request("DELETE", f"/api/v1/account/social-identities/{provider}", headers=csrf(social),
                          json={"password": PASSWORD, **credentials})


def test_link_proves_both_accounts_without_changing_profile_or_session(social):
    local = prepare(social)
    session_cookie = social.cookies.get("talentsync_session")
    csrf_cookie = social.cookies.get("talentsync_csrf")
    assert social.get("/api/v1/account/social-identities").json() == []
    state = begin_link(social)
    with social.session_factory() as db:
        row = db.query(OAuthAttempt).one()
        assert row.purpose == "link" and row.link_user_id == local["id"]
        assert row.link_session_id == db.query(UserSession).one().id
    response = callback(social, state)
    assert response.headers["location"].endswith("/seguridad?social=linked")
    assert social.cookies.get("talentsync_session") == session_cookie
    assert social.cookies.get("talentsync_csrf") == csrf_cookie
    connections = social.get("/api/v1/account/social-identities").json()
    assert len(connections) == 1 and set(connections[0]) == {"provider", "created_at"}
    me = social.get("/api/v1/auth/me").json()
    assert me["id"] == local["id"] and me["email"] == "alex@example.com" and me["name"] == "alex"
    with social.session_factory() as db:
        assert db.query(User).count() == 1 and db.query(UserSession).count() == 1
        event = db.query(EventLog).filter_by(event_type="account.social_linked").one()
        assert event.details == {"source": "github"}
    assert social.post("/api/v1/auth/session/logout", headers=csrf(social)).status_code == 200
    assert callback(social, start(social)).headers["location"].endswith("/candidato")
    assert social.get("/api/v1/auth/me").json()["id"] == local["id"]


def test_link_requires_password_csrf_and_allowed_origin(social):
    prepare(social)
    path = "/api/v1/account/social-identities/github/link"
    assert social.post(path, json={"password": PASSWORD}).status_code == 403
    assert social.post(path, headers=csrf(social), json={"password": "incorrect"}).status_code == 401
    assert social.post(path, headers={**csrf(social), "Origin": "https://attacker.invalid"}, json={"password": PASSWORD}).status_code == 403
    social.cookies.clear()
    assert social.post(path, json={"password": PASSWORD}).status_code == 401


@pytest.mark.parametrize("interruption", ["logout", "new_session", "expired", "during_exchange"])
def test_link_cannot_complete_after_session_changes(social, interruption):
    prepare(social)
    state = begin_link(social)
    if interruption == "logout":
        social.post("/api/v1/auth/session/logout", headers=csrf(social))
    elif interruption == "new_session":
        login(social)
    elif interruption == "expired":
        with social.session_factory() as db:
            db.query(UserSession).one().expires_at = datetime.utcnow() - timedelta(seconds=1)
            db.commit()
    else:
        original = social.social_provider.exchange
        def revoke_during_exchange(*args):
            with social.session_factory() as db:
                db.query(UserSession).one().revoked_at = datetime.utcnow()
                db.commit()
            return original(*args)
        social.social_provider.exchange = revoke_during_exchange
    assert "status=failed" in callback(social, state).headers["location"]
    with social.session_factory() as db:
        assert db.query(SocialIdentity).count() == 0


def test_link_cannot_take_identity_of_another_account_or_replace_provider(social):
    callback(social, start(social))
    other_id = social.get("/api/v1/auth/me").json()["id"]
    prepare(social)
    assert "status=existing" in callback(social, begin_link(social)).headers["location"]
    with social.session_factory() as db:
        assert db.query(SocialIdentity).one().user_id == other_id
    social.social_provider.exchange = lambda *args: {"subject": "different-id", "email": "different@example.com", "name": "Otra"}
    assert callback(social, begin_link(social)).headers["location"].endswith("/seguridad?social=linked")
    assert social.post("/api/v1/account/social-identities/github/link", headers=csrf(social), json={"password": PASSWORD}).status_code == 409


def test_link_and_unlink_require_fresh_mfa_and_cancel_other_access(social):
    prepare(social)
    callback(social, begin_link(social))
    login(social)  # A second session that must be closed by unlink.
    with social.session_factory() as db:
        user = db.query(User).one()
        user.mfa_enabled = True
        user.mfa_secret = AccountSecurity().encrypt_secret("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ")
        user.recovery_codes = [token_digest("link-code-once"), token_digest("unlink-code-once")]
        db.query(UserSession).update({UserSession.mfa_verified: True})
        db.add(AccountToken(user_id=user.id, token_hash=token_digest("pending-token"), purpose="social_mfa",
                            expires_at=datetime.utcnow() + timedelta(minutes=5)))
        db.commit()
    path = "/api/v1/account/social-identities/google/link"
    assert social.post(path, headers=csrf(social), json={"password": PASSWORD}).status_code == 401
    pending_state = begin_link(social, "google", code="link-code-once")
    assert unlink(social).status_code == 401
    assert unlink(social, code="link-code-once").status_code == 401
    assert unlink(social, code="unlink-code-once").status_code == 200
    assert social.get("/api/v1/auth/me").status_code == 200
    assert social.get("/api/v1/account/social-identities").json() == []
    assert "status=failed" in callback(social, pending_state, provider="google").headers["location"]
    with social.session_factory() as db:
        assert db.query(UserSession).filter_by(revoked_at=None).count() == 1
        assert db.query(AccountToken).filter_by(purpose="social_mfa").one().used_at is not None
        assert db.query(OAuthAttempt).filter_by(state_hash=token_digest(pending_state)).one().verifier_cipher == ""


def test_unlink_works_when_provider_is_disabled_and_requires_owner_password(social):
    prepare(social)
    callback(social, begin_link(social))
    social.social_provider.configured = lambda provider: False
    assert unlink(social, password="incorrect").status_code == 401
    assert len(social.get("/api/v1/account/social-identities").json()) == 1
    assert unlink(social).status_code == 200
    assert unlink(social).status_code == 404
    assert login(social).status_code == 200  # Password access remains available.


def test_connection_list_and_unlink_are_scoped_to_owner(social):
    prepare(social)
    callback(social, begin_link(social))
    register(social, "other")
    login(social, "other@example.com")
    assert social.get("/api/v1/account/social-identities").json() == []
    assert unlink(social).status_code == 404
    with social.session_factory() as db:
        assert db.query(SocialIdentity).count() == 1


def test_deleting_user_removes_link_transactions_without_sqlite_foreign_keys(social):
    prepare(social)
    begin_link(social)
    with social.session_factory() as db:
        uow = SqlAlchemyUnitOfWork(db)
        uow.delete(db.query(User).one())
        uow.commit()
        assert db.query(OAuthAttempt).count() == 0


@pytest.mark.parametrize("role", ["company", "admin"])
def test_social_account_management_is_exclusive_to_candidates(social, role):
    prepare(social)
    from app.domain.entities.enums import UserRole
    with social.session_factory() as db:
        db.query(User).one().role = UserRole(role)
        db.commit()
    assert social.get("/api/v1/account/social-identities").status_code == 403
    assert social.post("/api/v1/account/social-identities/github/link", headers=csrf(social), json={"password": PASSWORD}).status_code == 403
