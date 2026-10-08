# ruff: noqa: F811
from datetime import datetime
from types import SimpleNamespace

from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.domain.entities.enums import UserRole
from app.domain.services.reputation import company_health
from app.infrastructure.database.models import User


def administrator(client):
    user, headers = register(client, "ecosystem-admin")
    with client.session_factory() as db:
        db.get(User, user["id"]).role = UserRole.ADMIN
        db.commit()
    return headers


def test_reports_are_private_reviewed_and_appealable(client):
    _, company = company_account(client)
    _, outsider = company_account(client, "unrelated-company")
    job = create_job(client, company)
    _, candidate = register(client, "reporter")
    _, other = register(client, "other-reporter")
    application = client.post("/api/v1/applications", headers=candidate, json={"job_id": job["id"]}).json()
    payload = {"application_id": application["id"], "category": "inappropriate_interview", "details": "PRIVATE-DETAILS: relato reservado del candidato."}
    assert client.post("/api/v1/trust/incidents", headers=other, json=payload).status_code == 404
    incident = client.post("/api/v1/trust/incidents", headers=candidate, json=payload)
    assert incident.status_code == 200
    incident_id = incident.json()["id"]
    assert client.post("/api/v1/trust/incidents", headers=candidate, json=payload).status_code == 409
    assert "PRIVATE-DETAILS" in client.get("/api/v1/trust/incidents/me", headers=candidate).text
    organization = client.get("/api/v1/trust/organization/incidents", headers=company)
    assert "PRIVATE-DETAILS" not in organization.text
    assert "reporter_user_id" not in organization.text
    assert client.get(f"/api/v1/trust/companies/{job['company_id']}", headers=candidate).json()["score"] is None
    admin = administrator(client)
    endpoint = f"/api/v1/admin/incidents/{incident_id}"
    review = {"status": "confirmed", "shared_summary": "Se confirmó una conducta inadecuada en la entrevista."}
    assert client.patch(endpoint, headers=candidate, json=review).status_code == 403
    assert client.patch(endpoint, headers=admin, json=review).status_code == 200
    appeal = f"/api/v1/trust/incidents/{incident_id}/appeal"
    assert client.post(appeal, headers=outsider, json={"message": "Solicitamos revisar la evidencia registrada."}).status_code == 404
    assert client.post(appeal, headers=company, json={"message": "Solicitamos revisar la evidencia registrada."}).status_code == 200
    assert client.get(f"/api/v1/trust/companies/{job['company_id']}", headers=candidate).json()["confirmed_incidents"] == 1
    assert client.patch(endpoint, headers=admin, json={**review, "status": "dismissed"}).status_code == 200
    assert client.get(f"/api/v1/trust/companies/{job['company_id']}", headers=candidate).json()["score"] is None


def test_trust_requires_observations_and_ignores_pending_reports():
    now = datetime.utcnow()
    applications = [SimpleNamespace(created_at=now, first_response_at=None, resolution_reason="response_deadline") for _ in range(6)]
    company = SimpleNamespace(jobs=[SimpleNamespace(applications=applications)], incidents=[SimpleNamespace(status="open", created_at=now)])
    report = company_health(company, now=now)
    assert report["missed_deadlines"] == 6
    assert report["confirmed_incidents"] == 0
    assert report["visibility_reduced"] is True
    assert company_health(SimpleNamespace(jobs=[], incidents=[]))["score"] is None


def test_audit_has_versioned_metrics_and_no_predictive_claim(client):
    _, company = company_account(client)
    create_job(client, company)
    register(client, "audit-candidate", skills=["Python", "SQL"], profession="Desarrollador Python")
    admin = administrator(client)
    assert client.post("/api/v1/admin/ecosystem/audit", headers=company).status_code == 403
    audit = client.post("/api/v1/admin/ecosystem/audit", headers=admin)
    assert audit.status_code == 200, audit.text
    metrics = audit.json()
    assert metrics["pair_count"] > 0
    assert metrics["identity_invariance_violations"] == 0
    assert metrics["demographic_fairness"] == "unavailable_no_consented_demographic_dataset"
    assert metrics["distribution_psi"] is None
    dashboard = client.get("/api/v1/admin/ecosystem", headers=admin).json()
    assert len(dashboard["audits"]) == 1
    assert dashboard["audits"][0]["version"]
    assert dashboard["skills"]
