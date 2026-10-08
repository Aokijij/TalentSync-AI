import pytest
from test_api_flows import client, register  # noqa: F401

from app.core.config import settings
from app.infrastructure.database.models import User, UserSession


@pytest.mark.parametrize("session_mode", [False, True])
@pytest.mark.parametrize("role,portal", [("candidate", "company"), ("company", "candidate")])
def test_portal_rejects_other_role_before_mfa_or_session(client, monkeypatch, session_mode, role, portal):  # noqa: F811
    user, _ = register(client, f"portal-{role}", role, company_name="Portal local", nit="PORTAL-1")
    with client.session_factory() as db:
        db.get(User, user["id"]).mfa_enabled = True
        db.commit()
    monkeypatch.setattr(settings, "session_auth_enabled", session_mode)
    prefix = "/api/v1/auth/session" if session_mode else "/api/v1/auth"
    result = client.post(f"{prefix}/{portal}/login", json={"email": user["email"], "password": "Test-password-2026!", "portal": role})
    assert result.status_code == 401
    assert "mfa_required" not in result.json()
    assert "set-cookie" not in result.headers
    with client.session_factory() as db:
        assert db.query(UserSession).count() == 0


@pytest.mark.parametrize("role", ["candidate", "company"])
def test_separate_registration_routes_reject_forged_role(client, role):  # noqa: F811
    other = "candidate" if role == "company" else "company"
    payload = {"name": "Cuenta local", "email": "portal-new@example.com", "password": "Test-password-2026!", "role": other, "company_name": "Portal local", "nit": "PORTAL-NEW"}
    assert client.post(f"/api/v1/auth/{role}/register", json=payload).status_code == 422
    payload["role"] = role
    result = client.post(f"/api/v1/auth/{role}/register", json=payload)
    assert result.status_code == 201 and result.json()["role"] == role
    logged = client.post(f"/api/v1/auth/{role}/login", json={"email": payload["email"], "password": payload["password"]})
    assert logged.status_code == 200
