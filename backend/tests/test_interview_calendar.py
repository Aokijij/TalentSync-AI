# ruff: noqa: F811
from datetime import datetime, timedelta, timezone

import pytest
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.api.schemas.application import ApplicationStatusUpdate
from app.domain.services.interview_calendar import interview_calendar
from app.infrastructure.database.models import Application


def _appointment(client):
    _, company = company_account(client, "calendar-company")
    job = create_job(client, company)
    _, candidate = register(client, "calendar-candidate")
    application = client.post("/api/v1/applications", headers=candidate, json={"job_id": job["id"]}).json()
    when = (datetime.now(timezone.utc) + timedelta(days=5)).replace(second=0, microsecond=0)
    update = client.put(f"/api/v1/applications/{application['id']}/status", headers=company,
                        json={"status": "technical_interview", "interview_at": when.isoformat(),
                              "recruiter_notes": "PRIVATE-RECRUITER-NOTE"})
    assert update.status_code == 200, update.text
    return update.json(), company, candidate, when


def _unfold(content):
    return content.decode("utf-8").replace("\r\n ", "")


def test_calendar_authorization_private_content_and_no_side_effects(client):
    application, company, candidate, when = _appointment(client)
    url = f"/api/v1/workflow/applications/{application['id']}/interview.ics"
    _, stranger = register(client, "calendar-stranger")
    _, other_company = company_account(client, "calendar-other-company")
    assert client.get(url).status_code == 401
    assert client.get(url, headers=stranger).status_code == 403
    assert client.get(url, headers=other_company).status_code == 403
    assert client.get("/api/v1/workflow/applications/999999/interview.ics", headers=candidate).status_code == 404
    for headers in (candidate, company):
        response = client.get(url, headers=headers)
        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"
        assert "no-store" in response.headers["cache-control"]
        assert "attachment;" in response.headers["content-disposition"]
        content = _unfold(response.content)
        assert f"DTSTART:{when.strftime('%Y%m%dT%H%M%SZ')}" in content
        assert "CLASS:PRIVATE" in content
        assert "TRIGGER:-PT30M" in content
        assert "PRIVATE-RECRUITER-NOTE" not in content
        assert "calendar-candidate" not in content
        assert "ATTENDEE" not in content and "ORGANIZER" not in content
        assert "DTEND" not in content and "LOCATION" not in content
        assert "access_token" not in content
    with client.session_factory() as db:
        assert db.get(Application, application["id"]).version == application["version"]


def test_rescheduling_keeps_event_identity_and_exports_current_schedule(client):
    application, company, candidate, when = _appointment(client)
    url = f"/api/v1/workflow/applications/{application['id']}/interview.ics"
    first = _unfold(client.get(url, headers=candidate).content)
    new_time = when + timedelta(days=2)
    result = client.put(f"/api/v1/applications/{application['id']}/status", headers=company,
                        json={"interview_at": new_time.isoformat(), "expected_version": application["version"]})
    assert result.status_code == 200, result.text
    second = _unfold(client.get(url, headers=candidate).content)
    def uid(value):
        return next(line for line in value.splitlines() if line.startswith("UID:"))
    assert uid(first) == uid(second)
    assert f"SEQUENCE:{result.json()['version']}" in second
    assert f"DTSTART:{new_time.strftime('%Y%m%dT%H%M%SZ')}" in second
    # Caller-provided timezones are normalized before naive UTC persistence.
    offset = new_time.astimezone(timezone(timedelta(hours=-5)))
    assert client.put(f"/api/v1/applications/{application['id']}/status", headers=company,
                      json={"interview_at": offset.isoformat()}).status_code == 200
    third = _unfold(client.get(url, headers=candidate).content)
    assert f"DTSTART:{new_time.strftime('%Y%m%dT%H%M%SZ')}" in third


@pytest.mark.parametrize("state", ["missing", "past", "withdrawn", "rejected", "accepted", "hired"])
def test_inactive_or_missing_appointments_cannot_be_exported(client, state):
    application, company, candidate, _ = _appointment(client)
    if state in {"missing", "past"}:
        when = None if state == "missing" else (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        assert client.put(f"/api/v1/applications/{application['id']}/status", headers=company,
                          json={"interview_at": when}).status_code == 200
    elif state == "withdrawn":
        assert client.post(f"/api/v1/workflow/applications/{application['id']}/withdraw", headers=candidate).status_code == 200
    else:
        assert client.put(f"/api/v1/applications/{application['id']}/status", headers=company,
                          json={"status": state}).status_code == 200
    response = client.get(f"/api/v1/workflow/applications/{application['id']}/interview.ics", headers=candidate)
    assert response.status_code == 409, response.text


def test_icalendar_folds_utf8_and_escapes_property_injection():
    title = "Análisis de integración " * 12 + "\\;\r\nEND:VEVENT\nBEGIN:VEVENT, test"
    when = datetime(2026, 10, 30, 9, 0, tzinfo=timezone(timedelta(hours=-5)))
    content = interview_calendar(application_id=42, created_at=when, interview_at=when,
                                 job_title=title, company_name="Compañía; Uno, Dos", version=3,
                                 process_url="https://example.com/procesos/42", now=when)
    assert content.endswith(b"\r\n")
    assert all(len(line) <= 75 for line in content.split(b"\r\n"))
    assert all(line.decode("utf-8") is not None for line in content.split(b"\r\n"))
    unfolded = _unfold(content)
    assert unfolded.count("\r\nBEGIN:VEVENT\r\n") == 1
    assert unfolded.count("\r\nEND:VEVENT\r\n") == 1
    assert "DTSTART:20261030T140000Z" in unfolded
    assert "Compañía\\; Uno\\, Dos" in unfolded
    assert "\\nEND:VEVENT\\nBEGIN:VEVENT\\, test" in unfolded
    assert "DTEND" not in unfolded


def test_interview_schema_normalizes_offsets_and_preserves_explicit_cancellation():
    assert ApplicationStatusUpdate(interview_at="2026-10-30T09:00:00-05:00").interview_at == datetime(2026, 10, 30, 14)
    assert ApplicationStatusUpdate(interview_at=None).model_dump(exclude_unset=True) == {"interview_at": None}
    assert ApplicationStatusUpdate().model_dump(exclude_unset=True) == {}


def test_interview_notifications_use_colombia_time_and_explain_calendar_updates(client):
    application, company, candidate, when = _appointment(client)
    endpoint = f"/api/v1/applications/{application['id']}/status"
    notifications = "/api/v1/notifications?unread_only=false"
    before = client.get(notifications, headers=candidate).json()
    # Saving the same instant in another timezone does not announce a reschedule.
    assert client.put(endpoint, headers=company, json={"interview_at": when.astimezone(timezone(timedelta(hours=-5))).isoformat()}).status_code == 200
    assert client.get(notifications, headers=candidate).json() == before
    new_time = (when + timedelta(days=1)).replace(hour=14, minute=0)
    assert client.put(endpoint, headers=company, json={"interview_at": new_time.isoformat()}).status_code == 200
    items = client.get(notifications, headers=candidate).json()
    rescheduled = next(row for row in items if row["title"] == "Entrevista reprogramada")
    assert "09:00 (hora de Colombia)" in rescheduled["body"]
    assert "actualiza tu calendario" in rescheduled["body"]
    assert client.put(endpoint, headers=company, json={"interview_at": None}).status_code == 200
    items = client.get(notifications, headers=candidate).json()
    canceled = next(row for row in items if row["title"] == "Entrevista cancelada")
    assert "elimina la cita de tu calendario" in canceled["body"]
