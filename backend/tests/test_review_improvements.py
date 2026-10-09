# ruff: noqa: F811
from datetime import datetime
from types import SimpleNamespace

import pytest
from test_account_security import browser, csrf  # noqa: F401
from test_api_flows import client, register  # noqa: F401

from app.core.config import settings
from app.domain.entities.enums import UserRole
from app.domain.services.job_quality import assess_quality
from app.infrastructure.database.models import Company, CompanyMember, User, UserSession


@pytest.mark.parametrize("environment,database,waived", [("development", "sqlite://", True), ("production", "sqlite://", False), ("development", "postgresql://localhost/db", False)])
def test_admin_review_waiver_is_local_only(monkeypatch, environment, database, waived):
    monkeypatch.setattr(settings, "local_admin_review_enabled", True)
    monkeypatch.setattr(settings, "environment", environment)
    monkeypatch.setattr(settings, "database_url", database)
    assert settings.admin_mfa_required is not waived


def test_local_admin_login_preserves_enrolled_authenticator(browser, monkeypatch):
    monkeypatch.setattr(settings, "local_admin_review_enabled", True)
    monkeypatch.setattr(settings, "environment", "development")
    user, _ = register(browser, "local-review-admin")
    with browser.session_factory() as db:
        row = db.get(User, user["id"])
        row.role = UserRole.ADMIN
        row.mfa_enabled = True
        row.mfa_secret = "preserved-secret"
        db.commit()
    result = browser.post("/api/v1/auth/session/admin/login", json={"email": user["email"], "password": "Test-password-2026!"})
    assert result.status_code == 200, result.text
    assert not result.json().get("mfa_required") and not result.json()["mfa_setup_required"]
    assert browser.get("/api/v1/admin/stats").status_code == 200
    with browser.session_factory() as db:
        assert db.get(User, user["id"]).mfa_secret == "preserved-secret"
        assert db.query(UserSession).filter_by(user_id=user["id"]).one().mfa_verified is False
    monkeypatch.setattr(settings, "local_admin_review_enabled", False)
    assert browser.get("/api/v1/admin/stats").status_code == 403


def test_external_certificate_needs_completed_owned_plan_and_proof(client):
    _, headers = register(client, "external-certificate", skills=["python"])
    endpoint = "/api/v1/learning/plans/microsoft-data-analytics/certificate"
    payload = {"name": "Certificado de análisis", "credential_url": "https://example.com/credentials/test", "year": datetime.utcnow().year, "has_certificate": True}
    assert client.post(endpoint, headers=headers, json=payload).status_code == 404
    assert client.put("/api/v1/learning/plans/microsoft-data-analytics", headers=headers, json={"status": "in_progress"}).status_code == 200
    assert client.post(endpoint, headers=headers, json=payload).status_code == 409
    assert client.put("/api/v1/learning/plans/microsoft-data-analytics", headers=headers, json={"status": "completed"}).status_code == 200
    assert client.post(endpoint, headers=headers, json={**payload, "has_certificate": False}).status_code == 422
    assert client.post(endpoint, headers=headers, json={**payload, "credential_url": "http://127.0.0.1/proof"}).status_code == 422
    assert client.post(endpoint, headers=headers, json=payload).status_code == 200
    assert client.post(endpoint, headers=headers, json=payload).status_code == 200
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    assert profile["skills"] == ["python"]
    assert len(profile["certifications"]) == 1 and profile["certifications"][0]["verified"] is False
    evidence = client.get("/api/v1/matching/evidence", headers=headers).json()
    assert len(evidence) == 1 and evidence[0]["kind"] == "certificate"
    _, other = register(client, "other-certificate")
    assert client.post(endpoint, headers=other, json=payload).status_code == 404


def test_revoked_member_can_read_notice_before_mfa_but_not_company_data(browser):
    owner, _ = register(browser, "notice-owner", "company", company_name="Notice company", nit="NOTICE-123")
    member, _ = register(browser, "notice-member", "company", company_name="Other company", nit="NOTICE-456")
    with browser.session_factory() as db:
        company = db.query(Company).filter_by(owner_user_id=owner["id"]).one()
        db.add(CompanyMember(company_id=company.id, user_id=member["id"], role="recruiter", active=False, assigned_job_ids=[]))
        db.commit()
    login = browser.post("/api/v1/auth/session/company/login", json={"email": member["email"], "password": "Test-password-2026!"})
    assert login.status_code == 200 and login.json()["mfa_setup_required"]
    access = browser.get("/api/v1/organization/access")
    assert access.status_code == 200 and access.json()["active"] is False
    assert "applications" not in access.json()
    assert browser.get("/api/v1/organization/me").status_code == 403
    assert browser.get("/api/v1/organization/assignments").status_code == 403
    notice = browser.post("/api/v1/organization/access-review", headers=csrf(browser), json={"message": "Solicito al propietario una revisión de mi acceso retirado."})
    assert notice.status_code == 200, notice.text


def test_quality_does_not_reward_long_generic_copy():
    job = SimpleNamespace(id=1, title="Asesor comercial", description="Una gran oportunidad para crecer. " * 8, requirements="Te esperamos en esta maravillosa oportunidad. " * 5,
                          salary=None, sector="Comercio", modality="remote", location=None, skills=["ventas"], skill_requirements=[{"skill": "ventas", "essential": True, "weight": 3}], response_days=7, blind_hiring=True)
    report = assess_quality(job, [])
    checks = {row["key"]: row for row in report["checks"]}
    assert not checks["description"]["passed"] and not checks["requirements"]["passed"]
    assert report["completeness"] <= 45
    assert sum(row["weight"] for row in report["checks"]) == 100
    assert report["next_actions"][0]["priority"] == "Alta"
