# ruff: noqa: F811
import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from test_account_security import browser, csrf, login  # noqa: F401
from test_api_flows import client, create_job, register  # noqa: F401
from test_mail_delivery import cycle, inspect_message, queue

from app.api.deps import get_account_security, get_calendar_gateway
from app.application.calendar_errors import CalendarProviderError
from app.application.errors import UseCaseError
from app.application.use_cases import calendars
from app.core.config import settings
from app.domain.entities.enums import ApplicationStatus
from app.domain.services.mail_webhooks import verify_event
from app.infrastructure.database.models import (
    Application,
    CalendarConnection,
    CalendarEvent,
    MailDeliveryEvent,
    User,
)
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.google_calendar import SCOPE, GoogleCalendar

SECRET = "whsec_" + base64.b64encode(b"synthetic-webhook-secret-2026").decode()


def signed(event="email.delivered", identifier="msg_001", at=None, created=None):
    stamp = str(int(time.time()) if at is None else at)
    body = json.dumps({"type": event, "created_at": created or datetime.utcnow().isoformat() + "Z", "data": {"email_id": "provider_001"}}).encode()
    digest = base64.b64encode(hmac.new(base64.b64decode(SECRET[6:]), identifier.encode() + b"." + stamp.encode() + b"." + body, hashlib.sha256).digest()).decode()
    return body, {"svix-id": identifier, "svix-timestamp": stamp, "svix-signature": "v1," + digest}


def test_webhook_requires_exact_signature_and_recent_timestamp(client, monkeypatch):
    monkeypatch.setattr(settings, "resend_webhook_secret", SECRET)
    body, headers = signed()
    assert verify_event(body, headers, SECRET)["provider_message_id"] == "provider_001"
    assert client.post("/api/v1/webhooks/resend", content=body + b" ", headers=headers).status_code == 400
    old, old_headers = signed(at=int(time.time()) - 301)
    assert client.post("/api/v1/webhooks/resend", content=old, headers=old_headers).status_code == 400
    assert client.post("/api/v1/webhooks/resend", content=b"x" * 65537).status_code == 413
    assert client.post("/api/v1/webhooks/resend", content=body, headers=headers).status_code == 200
    assert client.post("/api/v1/webhooks/resend", content=body, headers=headers).status_code == 200
    with client.session_factory() as db:
        assert db.query(MailDeliveryEvent).count() == 1


def test_early_webhook_reconciles_and_older_events_do_not_regress_delivery(client, monkeypatch):
    monkeypatch.setattr(settings, "resend_webhook_secret", SECRET)
    delivered = datetime.utcnow()
    body, headers = signed(created=delivered.isoformat() + "Z")
    client.post("/api/v1/webhooks/resend", content=body, headers=headers)
    identifier = queue(client)
    cycle(client, SimpleNamespace(send=lambda **kwargs: "provider_001"))
    assert inspect_message(client, identifier).transport_status == "delivered"
    body, headers = signed("email.sent", "msg_002", created=(delivered - timedelta(minutes=1)).isoformat() + "Z")
    client.post("/api/v1/webhooks/resend", content=body, headers=headers)
    assert inspect_message(client, identifier).transport_status == "delivered"
    assert client.get("/api/v1/admin/mail-delivery").status_code == 401


def google_settings():
    return SimpleNamespace(calendar_sync_enabled=True, session_auth_enabled=True, calendar_google_client_id="test-client", calendar_google_client_secret="synthetic-secret", public_app_url="https://example.test", environment="staging")


def test_google_scope_pkce_fixed_endpoints_and_idempotent_event_retry():
    calls = []
    def transport(request):
        calls.append(request)
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "access-token-synthetic", "refresh_token": "refresh-token-synthetic", "scope": SCOPE})
        return httpx.Response(409 if request.method == "POST" else 200, json={})
    gateway = GoogleCalendar(google_settings(), httpx.MockTransport(transport))
    query = parse_qs(urlsplit(gateway.authorization_url("state", "challenge")).query)
    assert query["scope"] == [SCOPE] and query["code_challenge_method"] == ["S256"]
    assert gateway.exchange("code", "verifier") == "refresh-token-synthetic"
    assert b"code_verifier=verifier" in calls[0].content
    gateway.sync("access", "ts0123abc", {"summary": "Entrevista"}, True)
    assert [call.method for call in calls[1:]] == ["POST", "PATCH"]
    assert calls[1].url.host == "www.googleapis.com" and calls[1].url.params["sendUpdates"] == "none"
    with pytest.raises(CalendarProviderError):
        gateway.sync("access", "../bad", {}, True)


def test_calendar_browser_state_cannot_be_reused_or_crossed(browser):
    register(browser, "calendar-person")
    login(browser, "calendar-person@example.com")
    gateway = SimpleNamespace(configured=True, authorization_url=lambda state, challenge: "https://accounts.google.com/?" + "state=" + state, exchange=lambda *args: "private-refresh-value")
    browser.app.dependency_overrides[get_calendar_gateway] = lambda: gateway
    result = browser.post("/api/v1/account/calendar/google/connect", headers=csrf(browser))
    assert result.status_code == 200
    state = parse_qs(urlsplit(result.json()["url"]).query)["state"][0]
    response = browser.get("/api/v1/account/calendar/google/callback", params={"state": state, "code": "authorized"}, follow_redirects=False)
    assert "calendar=connected" in response.headers["location"]
    replay = browser.get("/api/v1/account/calendar/google/callback", params={"state": state, "code": "authorized"}, follow_redirects=False)
    assert "calendar=not_connected" in replay.headers["location"]
    with browser.session_factory() as db:
        assert db.query(CalendarConnection).one().refresh_cipher != "private-refresh-value"
    assert "refresh" not in browser.get("/api/v1/account/calendar").text


def calendar_fixture(client):
    candidate, headers = register(client, "calendar-candidate")
    _, company_headers = register(client, "calendar-company", "company", company_name="Calendar", nit="CAL-001")
    job = create_job(client, company_headers)
    with client.session_factory() as session:
        row = Application(user_id=candidate["id"], job_id=job["id"], interview_at=datetime.utcnow() + timedelta(days=2), recruiter_notes="PRIVATE COMPANY NOTES")
        session.add(row)
        session.commit()
        return candidate["id"], row.id


def test_event_sync_updates_cancels_and_excludes_private_notes(client):
    user_id, application_id = calendar_fixture(client)
    security = get_account_security()
    sent = []
    gateway = SimpleNamespace(configured=True, refresh=lambda value: ("access", None), sync=lambda *args, **kwargs: sent.append((args, kwargs)))
    with client.session_factory() as session:
        db = SqlAlchemyUnitOfWork(session)
        user = session.get(User, user_id)
        db.calendars.connect(user.id, security.encrypt_secret("refresh"))
        db.commit()
        calendars.enqueue(db, user, application_id, 45, gateway)
        row = db.calendars.event(user.id, application_id)
        assert calendars.process_event(db, row, user, gateway, security, public_app_url="https://example.test")
        assert row.state == "synced" and sent[0][1]["create"] is True
        payload = sent[0][0][2]
        assert "PRIVATE COMPANY NOTES" not in json.dumps(payload) and "attendees" not in payload
        assert payload["visibility"] == "private"
        app = session.get(Application, application_id)
        app.interview_at += timedelta(hours=2)
        db.commit()
        assert calendars.event_status(db, user, application_id)["state"] == "needs_sync"
        assert len(db.calendars.due(datetime.utcnow())) == 1
        calendars.process_event(db, row, user, gateway, security, public_app_url="https://example.test")
        assert sent[-1][1]["create"] is False
        app.status = ApplicationStatus.REJECTED
        db.commit()
        calendars.process_event(db, row, user, gateway, security, public_app_url="https://example.test")
        assert row.state == "cancelled" and sent[-1][0][2] is None


def test_revoked_calendar_stops_and_reconnect_requeues(client):
    user_id, application_id = calendar_fixture(client)
    security = get_account_security()
    def revoked(value):
        raise CalendarProviderError("authorization")
    gateway = SimpleNamespace(configured=True, refresh=revoked)
    with client.session_factory() as session:
        db = SqlAlchemyUnitOfWork(session)
        user = session.get(User, user_id)
        db.calendars.connect(user.id, security.encrypt_secret("refresh"))
        db.commit()
        calendars.enqueue(db, user, application_id, 45, gateway)
        row = db.calendars.event(user.id, application_id)
        calendars.process_event(db, row, user, gateway, security, public_app_url="https://example.test")
        assert row.state == "failed" and not db.calendars.due(datetime.utcnow())
        db.calendars.connect(user.id, security.encrypt_secret("replacement"))
        db.commit()
        assert len(db.calendars.due(datetime.utcnow())) == 1
        db.calendars.disconnect(user.id)
        db.commit()
        assert not session.query(CalendarEvent).count()


def test_manual_calendar_change_cannot_overwrite_inflight_worker(client):
    user_id, application_id = calendar_fixture(client)
    security = get_account_security()
    gateway = SimpleNamespace(configured=True)
    with client.session_factory() as session:
        db = SqlAlchemyUnitOfWork(session)
        user = session.get(User, user_id)
        db.calendars.connect(user.id, security.encrypt_secret("refresh"))
        db.commit()
        calendars.enqueue(db, user, application_id, 45, gateway)
        row = db.calendars.event(user.id, application_id)
        assert db.calendars.claim(row.id, "active-worker", datetime.utcnow())
        db.commit()
        with pytest.raises(UseCaseError) as failure:
            calendars.enqueue(db, user, application_id, 90, gateway)
        assert failure.value.status_code == 409
        db.refresh(row)
        assert row.minutes == 45 and row.lease_token == "active-worker"
