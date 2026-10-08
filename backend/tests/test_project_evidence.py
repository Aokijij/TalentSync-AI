# ruff: noqa: F811
import json
import time

import pytest
from test_account_security import browser, csrf, login  # noqa: F401
from test_api_flows import client, company_account, create_job, register  # noqa: F401
from test_project_inspector import archive

from app.infrastructure.database.models import EventLog, User
from app.infrastructure.security.accounts import AccountSecurity


def preview(client, headers=None):
    blob = archive({"src/main.py": "SECRET-CODE", "requirements.txt": "fastapi>=0.1"})
    response = client.post("/api/v1/matching/projects/preview", headers=headers or {}, files={"file": ("local.zip", blob, "application/zip")})
    assert response.status_code == 200, response.text
    return response.json()


def save_payload(preview, **overrides):
    return {"preview_token": preview["preview_token"], "title": "Mi proyecto", "description": "Desarrollé una API y escribí sus pruebas.",
            "skills": ["python"], "confirm_ownership": True, **overrides}


def test_preview_then_save_preserves_unverified_evidence_and_opt_in(client):
    _, company = company_account(client)
    job = create_job(client, company)
    _, user = register(client, "projects", skills=["Java"])
    before = client.get(f"/api/v1/matching/jobs/{job['id']}", headers=user).json()
    report = preview(client, user)
    assert client.get("/api/v1/matching/evidence", headers=user).json() == []
    assert "SECRET-CODE" not in json.dumps(report)
    response = client.post("/api/v1/matching/projects/evidence", headers=user, json=save_payload(report))
    assert response.status_code == 200, response.text
    evidence = response.json()[0]
    assert evidence["verified"] is False and evidence["analysis"]["version"] == "local-project-inspector-v1"
    assert client.get("/api/v1/profiles/me", headers=user).json()["skills"] == ["java"]
    after = client.get(f"/api/v1/matching/jobs/{job['id']}", headers=user).json()
    assert after["overall_score"] == before["overall_score"]
    assert after["input_version"] != before["input_version"]
    assert client.post("/api/v1/matching/projects/evidence", headers=user, json=save_payload(report)).status_code == 409
    assert client.delete(f"/api/v1/matching/evidence/{evidence['id']}", headers=user).status_code == 204
    response = client.post("/api/v1/matching/projects/evidence", headers=user, json=save_payload(report, add_to_profile=True))
    assert response.status_code == 200
    assert "python" in client.get("/api/v1/profiles/me", headers=user).json()["skills"]
    with client.session_factory() as db:
        events = db.query(EventLog).filter_by(event_type="profile.project_analyzed").all()
        assert all(row.details == {"source": "local_zip", "version": "local-project-inspector-v1"} for row in events)


@pytest.mark.parametrize("fault", ["other_owner", "altered", "expired", "unknown_skill", "no_ownership"])
def test_previews_are_owner_bound_authenticated_and_skills_cannot_be_forged(client, fault):
    _, user = register(client, "projects")
    report = preview(client, user)
    payload = save_payload(report)
    if fault == "other_owner":
        _, user = register(client, "other-projects")
    elif fault == "altered":
        payload["preview_token"] = "x" * 100
    elif fault == "expired":
        security = AccountSecurity()
        envelope = json.loads(security.decrypt_secret(payload["preview_token"]))
        envelope["expires_at"] = int(time.time()) - 1
        payload["preview_token"] = security.encrypt_secret(json.dumps(envelope))
    elif fault == "unknown_skill":
        payload["skills"] = ["microservicios"]
    else:
        payload["confirm_ownership"] = False
    assert client.post("/api/v1/matching/projects/evidence", headers=user, json=payload).status_code == 422
    assert client.get("/api/v1/matching/evidence", headers=user).json() == []


def test_browser_csrf_and_candidate_only_access(browser):
    register(browser, "alex")
    login(browser)
    blob = archive({"main.py": ""})
    assert browser.post("/api/v1/matching/projects/preview", files={"file": ("project.zip", blob)}).status_code == 403
    preview(browser, csrf(browser))
    with browser.session_factory() as db:
        from app.domain.entities.enums import UserRole
        db.query(User).one().role = UserRole.COMPANY
        db.commit()
    assert browser.post("/api/v1/matching/projects/preview", headers=csrf(browser), files={"file": ("project.zip", blob)}).status_code == 403


def test_manual_evidence_cannot_forge_a_server_analysis(client):
    _, user = register(client, "manual-projects")
    response = client.post("/api/v1/matching/evidence", headers=user, json={"title": "Declaración manual", "kind": "repository",
        "description": "Contribución descrita manualmente", "skills": ["python"], "verified": True, "analysis": {"version": "forged"}})
    assert response.status_code == 200
    assert response.json()[0]["verified"] is False and "analysis" not in response.json()[0]


def test_full_portfolio_does_not_mutate_skills_or_add_events(client):
    _, user = register(client, "full-projects", skills=["Java"])
    report = preview(client, user)
    with client.session_factory() as db:
        owner = db.query(User).one()
        owner.profile.evidence = [{"id": str(index), "skills": ["java"]} for index in range(50)]
        db.commit()
    response = client.post("/api/v1/matching/projects/evidence", headers=user, json=save_payload(report, add_to_profile=True))
    assert response.status_code == 422
    assert client.get("/api/v1/profiles/me", headers=user).json()["skills"] == ["java"]
    with client.session_factory() as db:
        assert db.query(EventLog).filter_by(event_type="profile.project_analyzed").count() == 0
