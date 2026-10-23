# ruff: noqa: F811
from datetime import datetime, timedelta

from test_api_flows import client, company_account, register  # noqa: F401
from test_recruitment_workspace import seed
from test_workflow import process

from app.application.use_cases.workflow import deadline_cycle
from app.domain.entities.enums import ApplicationStatus
from app.domain.services.response_deadlines import add_workdays, interview_deadline
from app.infrastructure.database.models import Application, Notification
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_platform_workdays_observe_colombia_weekends():
    assert add_workdays(datetime(2026, 10, 23, 14), 1) == datetime(2026, 10, 26, 14)
    assert add_workdays(datetime(2026, 10, 26, 2), 1) == datetime(2026, 10, 27, 2)
    assert add_workdays(datetime(2026, 10, 26, 14), -3) == datetime(2026, 10, 21, 14)


def test_overdue_pause_extension_and_final_decision_preserve_candidate_and_feedback(client):
    row, company, candidate = process(client)
    now = datetime.utcnow()
    with client.session_factory() as db:
        stored = db.get(Application, row["id"])
        stored.response_due_at = now - timedelta(days=1)
        stored.candidate_feedback = {"source": "company", "reason_code": "other", "message": "Seguimos revisando tus evidencias profesionales."}
        db.commit()
        assert deadline_cycle(SqlAlchemyUnitOfWork(db), now=now)["overdue"] == 1
        assert deadline_cycle(SqlAlchemyUnitOfWork(db), now=now)["overdue"] == 0
        first_missed = stored.deadline_missed_at
        assert stored.status == ApplicationStatus.SUBMITTED and stored.released_at is None
        assert deadline_cycle(SqlAlchemyUnitOfWork(db), now=add_workdays(now, 3))["paused"] == 1
        assert deadline_cycle(SqlAlchemyUnitOfWork(db), now=add_workdays(now, 4))["paused"] == 0
        assert db.query(Notification).filter_by(user_id=stored.user_id, type="application_response_overdue").count() == 1
        assert db.query(Notification).filter_by(user_id=stored.user_id, type="application_response_paused").count() == 1
    path = f"/api/v1/workflow/applications/{row['id']}"
    current = client.get(path, headers=company).json()
    assert current["response_state"] == "paused" and current["feedback"]["source"] == "company"
    payload = {"expected_version": current["version"], "due_at": add_workdays(now, 2).isoformat(), "reason": "El equipo técnico necesita contrastar las evidencias antes de comunicar la decisión."}
    assert client.post(path + "/deadline-extension", headers=candidate, json=payload).status_code == 403
    _, stranger = company_account(client, "deadline-outsider")
    assert client.post(path + "/deadline-extension", headers=stranger, json=payload).status_code == 403
    assert client.post(path + "/deadline-extension", headers=company, json={**payload, "expected_version": 1}).status_code == 409
    assert client.post(path + "/deadline-extension", headers=company, json={**payload, "reason": " " * 30}).status_code == 422
    assert client.post(path + "/deadline-extension", headers=company, json={**payload, "due_at": add_workdays(now, 8).isoformat()}).status_code == 422
    extended = client.post(path + "/deadline-extension", headers=company, json=payload)
    assert extended.status_code == 200, extended.text
    data = extended.json()
    assert data["response_state"] == "on_time" and data["response_paused_at"] is None
    assert data["deadline_extension_count"] == 1 and data["stage"] == "submitted"
    assert next(event for event in data["events"] if event["type"] == "application.deadline_extended")["extension_reason"] == payload["reason"]
    assert client.post(path + "/deadline-extension", headers=company, json={**payload, "expected_version": data["version"]}).status_code == 409
    status = f"/api/v1/applications/{row['id']}/status"
    notes = client.put(status, headers=company, json={"recruiter_notes": "Solo revisión interna", "expected_version": data["version"]}).json()
    assert notes["response_due_at"] == data["response_due_at"] and notes["deadline_extension_count"] == 1
    advanced = client.put(status, headers=company, json={"pipeline_stage": "reviewing", "expected_version": notes["version"]})
    assert advanced.status_code == 200 and advanced.json()["deadline_extension_count"] == 0
    with client.session_factory() as db:
        assert db.get(Application, row["id"]).deadline_missed_at == first_missed
    assert client.put(status, headers=company, json={"status": "rejected"}).status_code == 200
    assert client.post(path + "/deadline-extension", headers=company, json=payload).status_code == 409


def test_future_interview_rechecks_protection_before_delaying_or_pausing(client):
    row, company, candidate = process(client)
    now = datetime.utcnow()
    with client.session_factory() as db:
        stored = db.get(Application, row["id"])
        stored.status, stored.pipeline_stage = ApplicationStatus.TECHNICAL_INTERVIEW, "interview"
        stored.interview_at = now + timedelta(days=20)
        stored.interview_details = {"minutes": 60}
        stored.response_due_at = now - timedelta(days=2)
        db.commit()
        protected = interview_deadline(stored)
        result = deadline_cycle(SqlAlchemyUnitOfWork(db), now=now)
        assert result["protected"] == 1 and result["overdue"] == result["paused"] == 0
        assert stored.response_due_at == protected and stored.deadline_missed_at is None
        assert deadline_cycle(SqlAlchemyUnitOfWork(db), now=now)["protected"] == 0


def test_unexpired_grace_periods_do_not_starve_later_overdue_applicants(client):
    job, company = seed(client, 510)
    now = datetime.utcnow()
    with client.session_factory() as db:
        rows = db.query(Application).filter_by(job_id=job["id"]).order_by(Application.id).all()
        for row in rows:
            row.response_due_at = now - timedelta(days=2)
        for row in rows[:500]:
            row.response_overdue_at = now
        db.commit()
        result = deadline_cycle(SqlAlchemyUnitOfWork(db), now=now)
        assert result["overdue"] == 8 and result["released"] == result["paused"] == 0
        assert db.query(Application).filter(Application.response_overdue_at.is_not(None)).count() == 508
