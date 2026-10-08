# ruff: noqa: F811
from datetime import timedelta

import pytest
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.application.errors import UseCaseError
from app.application.use_cases.workflow import deadline_cycle
from app.infrastructure.database.models import Application
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def process(client):
    _, company = company_account(client)
    job = create_job(client, company)
    _, candidate = register(client, "process-user")
    response = client.post("/api/v1/applications", headers=candidate, json={"job_id": job["id"]})
    assert response.status_code == 201
    return response.json(), company, candidate


def test_timeline_private_notes_feedback_withdrawal_and_optimistic_updates(client):  # noqa: F811
    row, company, candidate = process(client)
    endpoint = f"/api/v1/applications/{row['id']}/status"
    timeline = f"/api/v1/workflow/applications/{row['id']}"
    assert row["response_due_at"] is not None
    result = client.put(endpoint, headers=company, json={"status": "reviewing", "recruiter_notes": "INTERNAL-PRIVATE-NOTE", "expected_version": row["version"], "candidate_feedback": {"reason_code": "other", "message": "Revisamos tu proyecto y agendaremos una conversación."}})
    assert result.status_code == 200
    assert client.put(endpoint, headers=company, json={"status": "hired", "expected_version": row["version"]}).status_code == 409
    data = client.get(timeline, headers=candidate)
    assert "INTERNAL-PRIVATE-NOTE" not in data.text
    assert data.json()["feedback"]["source"] == "company"
    assert len(data.json()["events"]) == 3
    _, other = register(client, "other-process")
    assert client.get(timeline, headers=other).status_code == 403
    assert client.post(timeline + "/withdraw", headers=candidate).status_code == 200
    assert client.get(timeline, headers=candidate).json()["response_due_at"] is None
    assert client.put(endpoint, headers=company, json={"status": "hired"}).status_code == 409


def test_deadline_reminders_release_once_and_conflicting_update(client):
    row, company, candidate = process(client)
    with client.session_factory() as db:
        application = db.get(Application, row["id"])
        due = application.response_due_at
        uow = SqlAlchemyUnitOfWork(db)
        assert deadline_cycle(uow, now=due - timedelta(hours=12)) == {"released": 0, "reminders": 1}
        assert deadline_cycle(uow, now=due - timedelta(hours=6)) == {"released": 0, "reminders": 0}
    with client.session_factory() as stale:
        outdated = stale.get(Application, row["id"])
        with client.session_factory() as db:
            assert deadline_cycle(SqlAlchemyUnitOfWork(db), now=due + timedelta(seconds=1))["released"] == 1
            assert deadline_cycle(SqlAlchemyUnitOfWork(db), now=due + timedelta(seconds=2))["released"] == 0
        outdated.recruiter_notes = "An update after the deadline"
        with pytest.raises(UseCaseError, match="") as failure:
            SqlAlchemyUnitOfWork(stale).commit()
        assert failure.value.status_code == 409
    response = client.get(f"/api/v1/workflow/applications/{row['id']}", headers=candidate).json()
    assert response["status"] == "rejected"
    assert response["feedback"]["reason_code"] == "response_deadline"
    assert len([item for item in response["events"] if item["type"] == "application.deadline_released"]) == 1


def test_company_cannot_erase_process_history_with_legacy_delete_endpoints(client):
    application, company, candidate = process(client)
    assert client.delete(f"/api/v1/applications/{application['id']}", headers=company).status_code == 403
    assert client.delete(f"/api/v1/jobs/{application['job_id']}", headers=company).status_code == 409
    assert client.put(f"/api/v1/applications/{application['id']}/status", headers=company, json={"status": "rejected"}).status_code == 200
    assert client.get(f"/api/v1/workflow/applications/{application['id']}", headers=candidate).json()["status"] == "rejected"
