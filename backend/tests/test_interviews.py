# ruff: noqa: F811
from datetime import datetime, timedelta

from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import CompanyMember, InterviewParticipant, User


def prepared(client):
    _, company = company_account(client)
    job = create_job(client, company)
    candidate, headers = register(client, "interview-candidate")
    application = client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"]}).json()
    assert client.post("/api/v1/interviews/rooms", headers=company, json={"application_id": application["id"]}).status_code == 409
    assert client.put(f"/api/v1/applications/{application['id']}/status", headers=company, json={"status": "technical_interview"}).status_code == 200
    response = client.post("/api/v1/interviews/rooms", headers=company, json={"application_id": application["id"]})
    assert response.status_code == 201, response.text
    return response.json(), company, headers, candidate, job


def test_interview_document_scope_conflicts_and_closed_rooms(client):
    room, company, candidate, _, _ = prepared(client)
    endpoint = f"/api/v1/interviews/rooms/{room['id']}"
    _, outsider = register(client, "interview-outsider")
    assert client.get(endpoint, headers=outsider).status_code == 404
    assert client.get("/api/v1/interviews/rooms", headers=outsider).json() == []
    assert client.post("/api/v1/interviews/rooms", headers=candidate, json={"application_id": room["application_id"]}).status_code == 403
    payload = {"expected_version": room["version"], "code": "print('shared')", "whiteboard": [{"points": [{"x": 20, "y": 30}, {"x": 40, "y": 50}]}]}
    saved = client.put(endpoint, headers=candidate, json=payload)
    assert saved.status_code == 200
    assert client.get(endpoint, headers=company).json()["code"] == "print('shared')"
    assert client.put(endpoint, headers=company, json=payload).status_code == 409
    assert client.put(endpoint, headers=company, json={**payload, "whiteboard": [{"points": [{"x": 2000, "y": 0}]}]}).status_code == 422
    assert client.post(endpoint + "/close", headers=candidate).status_code == 403
    assert client.post(endpoint + "/close", headers=company).json()["closed"] is True
    assert client.post(endpoint + "/connect", headers=candidate).status_code == 409
    assert client.get(endpoint, headers=candidate).json()["execution_enabled"] is False


def test_ephemeral_signaling_is_bound_to_participant_and_room(client):
    room, company, candidate, _, _ = prepared(client)
    endpoint = f"/api/v1/interviews/rooms/{room['id']}"
    first = client.post(endpoint + "/connect", headers=company).json()["participant_id"]
    second = client.post(endpoint + "/connect", headers=candidate).json()["participant_id"]
    assert client.post(endpoint + "/connect", headers=company).status_code == 409
    signal = {"recipient_id": second, "kind": "offer", "payload": {"type": "offer", "sdp": "LOCAL-SDP"}}
    assert client.post(endpoint + f"/participants/{first}/signal", headers=candidate, json=signal).status_code == 404
    assert client.post(endpoint + f"/participants/{first}/signal", headers=company, json=signal).status_code == 200
    response = client.post(endpoint + "/presence", headers=candidate, json={"participant_id": second, "after_id": 0}).json()
    assert response["signals"][0]["payload"]["sdp"] == "LOCAL-SDP"
    assert client.post(endpoint + "/presence", headers=company, json={"participant_id": first}).json()["signals"] == []
    assert client.post(endpoint + "/presence", headers=candidate, json={"participant_id": second, "after_id": response['signals'][0]['id']}).json()["signals"] == []
    assert client.post(endpoint + f"/participants/{first}/signal", headers=company, json={**signal, "payload": {"type": "offer", "sdp": "x" * 65000}}).status_code == 422
    with client.session_factory() as db:
        db.get(InterviewParticipant, first).expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.post(endpoint + "/presence", headers=company, json={"participant_id": first}).status_code == 404
    assert client.post(endpoint + "/connect", headers=company).status_code == 200
    assert client.delete(endpoint + f"/participants/{second}", headers=candidate).status_code == 200


def test_interviewer_access_follows_current_assignment(client):
    room, _, _, _, job = prepared(client)
    user, interviewer = register(client, "assigned-interviewer")
    with client.session_factory() as db:
        db.get(User, user["id"]).role = UserRole.COMPANY
        db.add(CompanyMember(company_id=job["company_id"], user_id=user["id"], role="interviewer", assigned_job_ids=[job["id"]], active=True))
        db.commit()
    endpoint = f"/api/v1/interviews/rooms/{room['id']}"
    assert client.get(endpoint, headers=interviewer).status_code == 200
    with client.session_factory() as db:
        member = db.query(CompanyMember).filter_by(user_id=user["id"]).one()
        member.assigned_job_ids = []
        db.commit()
    assert client.get(endpoint, headers=interviewer).status_code == 404
