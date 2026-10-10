# ruff: noqa: F811
from datetime import datetime
from types import SimpleNamespace

from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.domain.entities.enums import UserRole
from app.domain.services.reputation import company_health
from app.infrastructure.database.models import TrustIncident, User


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


def test_incident_queue_pages_beyond_200_and_keeps_private_detail_separate(client):
    _, company = company_account(client)
    job = create_job(client, company)
    candidate, candidate_headers = register(client, "queue-reporter")
    application = client.post("/api/v1/applications", headers=candidate_headers, json={"job_id": job["id"]}).json()
    with client.session_factory() as db:
        rows = [TrustIncident(company_id=job["company_id"], application_id=application["id"], reporter_user_id=candidate["id"],
            category="ghosting", details="PRIVATE-QUEUE: hechos reservados para la revisión.", status="open", appeal={}) for _ in range(205)]
        db.add_all(rows)
        db.commit()
        first, last = rows[0].id, rows[-1].id
    admin = administrator(client)
    endpoint = "/api/v1/admin/incident-queue"
    assert client.get(endpoint, headers=company).status_code == 403
    assert client.get(endpoint, headers=candidate_headers).status_code == 403
    response = client.get(endpoint, headers=admin)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["total"] == 205 and result["counts"] == {"open": 205}
    assert len(result["items"]) == 8 and result["items"][0]["id"] == first
    assert "PRIVATE-QUEUE" not in response.text and "reporter_user_id" not in response.text
    assert "history" not in response.text and "shared_summary" not in response.text
    tail = client.get(endpoint, headers=admin, params={"page": 26}).json()
    assert len(tail["items"]) == 5 and tail["items"][-1]["id"] == last
    beyond = client.get(endpoint, headers=admin, params={"page": 100}).json()
    assert beyond["page"] == 26
    found = client.get(endpoint, headers=admin, params={"search": f"#{last}"}).json()
    assert found["total"] == 1 and found["items"][0]["id"] == last
    assert client.get(endpoint, headers=admin, params={"search": "%"}).json()["total"] == 0
    assert client.get(endpoint, headers=admin, params={"search": job["title"]}).json()["total"] == 205
    assert client.get(endpoint, headers=admin, params={"category": "discrimination"}).json()["total"] == 0
    assert client.get(endpoint, headers=admin, params={"page_size": 51}).status_code == 422
    assert client.get(endpoint, headers=admin, params={"page": 0}).status_code == 422
    detail = f"/api/v1/admin/incidents/{last}"
    assert client.get(detail, headers=candidate_headers).status_code == 403
    assert client.get(detail, headers=company).status_code == 403
    assert "PRIVATE-QUEUE" in client.get(detail, headers=admin).text
    assert client.get("/api/v1/admin/incidents/999999", headers=admin).status_code == 404


def test_incident_queue_filters_resolutions_and_prioritizes_appeals(client):
    _, company = company_account(client)
    job = create_job(client, company)
    candidate, _ = register(client, "queue-states")
    with client.session_factory() as db:
        for state in ["open", "in_review", "confirmed", "dismissed", "appealed"]:
            db.add(TrustIncident(company_id=job["company_id"], reporter_user_id=candidate["id"], category="other", status=state, details="Hechos concretos para revisar el proceso.", appeal={}))
        db.commit()
    admin = administrator(client)
    endpoint = "/api/v1/admin/incident-queue"
    pending = client.get(endpoint, headers=admin).json()
    assert [row["status"] for row in pending["items"]] == ["appealed", "open", "in_review"]
    assert pending["total"] == 3 and sum(pending["counts"].values()) == 5
    assert client.get(endpoint, headers=admin, params={"bucket": "resolved"}).json()["total"] == 2
    assert client.get(endpoint, headers=admin, params={"bucket": "all"}).json()["total"] == 5
    only_appeal = client.get(endpoint, headers=admin, params={"status": "appealed"}).json()
    assert only_appeal["total"] == 1
    assert client.get(endpoint, headers=admin, params={"sort": "newest"}).json()["items"][0]["status"] == "appealed"
    assert client.get(endpoint, headers=admin, params={"sort": "oldest"}).json()["items"][0]["status"] == "open"
    incident_id = only_appeal["items"][0]["id"]
    assert client.patch(f"/api/v1/admin/incidents/{incident_id}", headers=admin, json={"status": "dismissed", "shared_summary": "Se revisaron los hechos y se desestimó por el motivo indicado."}).status_code == 200
    refreshed = client.get(endpoint, headers=admin).json()
    assert refreshed["total"] == 2 and refreshed["counts"]["dismissed"] == 2
