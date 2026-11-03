# ruff: noqa: F811
import io
import json
import zipfile
from datetime import datetime, timedelta
from types import SimpleNamespace

from test_account_security import browser, csrf, login  # noqa: F401
from test_api_flows import client, create_job, register  # noqa: F401
from test_ecosystem import administrator

from app.api.deps import get_account_files, get_resume_reader
from app.application.use_cases.account_data import process_erasure
from app.core.operations import RequestMetrics
from app.infrastructure.database.models import (
    Application,
    AssessmentAttempt,
    CalendarConnection,
    CareerCoachState,
    FileErasureTask,
    ResumeVersion,
    User,
    UserSession,
)
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.private_account_files import PrivateAccountFiles

PASSWORD = "Test-password-2026!"


def test_export_is_owner_scoped_excludes_credentials_and_company_notes(client):
    person, headers = register(client, "export-person")
    other, _ = register(client, "other-private-person")
    _, owner = register(client, "export-owner", "company", company_name="Export", nit="EXPORT-1")
    job = create_job(client, owner)
    with client.session_factory() as db:
        db.add(Application(user_id=person["id"], job_id=job["id"], recruiter_notes="HIDDEN EMPLOYER NOTE", interview_evaluations=[{"text": "PRIVATE RATING"}], screening_answers=[{"question": "Pregunta", "answer": "Respuesta propia", "rating": 3, "internal_note": "SECRET RATING"}]))
        db.add(CareerCoachState(user_id=person["id"], content={"own_draft": "Mi borrador"}))
        db.add(AssessmentAttempt(id="f" * 32, user_id=person["id"], assessment_id="test", skill="python", version="1", snapshot=[{"id": "q", "prompt": "Pregunta del reto", "choices": ["A", "B"], "answer": 1, "feedback": "PRIVATE SOLUTION"}], expires_at=datetime.utcnow() + timedelta(minutes=10)))
        db.add(CalendarConnection(user_id=person["id"], refresh_cipher="PRIVATE REFRESH TOKEN"))
        db.add(ResumeVersion(id="a" * 32, user_id=person["id"], request_key="owned-key", request_digest="digest", source_version="source", snapshot={}, filename="CV.pdf", pdf_sha256="hash", pdf=b"%PDF-owned"))
        db.add(ResumeVersion(id="b" * 32, user_id=other["id"], request_key="other-key", request_digest="digest", source_version="source", snapshot={}, filename="Other.pdf", pdf_sha256="hash", pdf=b"%PDF-OTHER PRIVATE"))
        db.commit()
    client.app.dependency_overrides[get_account_files] = lambda: SimpleNamespace(export=lambda user_id: [("files/cv.pdf", b"%PDF-original")])
    assert client.post("/api/v1/account/data/export", headers=headers, json={"password": "wrong"}).status_code == 401
    result = client.post("/api/v1/account/data/export", headers=headers, json={"password": PASSWORD})
    assert result.status_code == 200, result.text[:200]
    with zipfile.ZipFile(io.BytesIO(result.content)) as archive:
        raw = archive.read("datos.json").decode()
        data = json.loads(raw)
        assert data["account"]["legal_acceptance"]["terms_accepted"] is True
        assert data["account"]["legal_acceptance"]["accepted_at"]
        assert "Mi borrador" in raw and "Respuesta propia" in raw
        assert all(value not in raw for value in ("password_hash", "HIDDEN EMPLOYER NOTE", "PRIVATE RATING", "PRIVATE REFRESH TOKEN", "SECRET RATING", "PRIVATE SOLUTION", "other-private-person"))
        assert archive.read("cv/" + "a" * 32 + ".pdf") == b"%PDF-owned"
        assert len(archive.namelist()) == 3
        assert data["manifest"]["original_cv_available"] is True


def test_delete_requires_csrf_password_confirmation_and_revokes_everything(browser):
    person, _ = register(browser, "erase-person")
    login(browser, "erase-person@example.com")
    seen = []
    browser.app.dependency_overrides[get_account_files] = lambda: SimpleNamespace(erase=lambda identifier: seen.append(identifier))
    payload = {"password": PASSWORD, "confirmation": "ELIMINAR"}
    assert browser.post("/api/v1/account/data/erase", json=payload).status_code == 403
    assert browser.post("/api/v1/account/data/erase", headers=csrf(browser), json={**payload, "password": "wrong"}).status_code == 401
    assert browser.post("/api/v1/account/data/erase", headers=csrf(browser), json={**payload, "confirmation": "no"}).status_code == 422
    with browser.session_factory() as db:
        db.add(CareerCoachState(user_id=person["id"], content={"private": True}))
        db.add(CalendarConnection(user_id=person["id"], refresh_cipher="private"))
        db.commit()
    result = browser.post("/api/v1/account/data/erase", headers=csrf(browser), json=payload)
    assert result.status_code == 200, result.text
    assert result.json()["files_pending"] is False and seen == [person["id"]]
    assert browser.get("/api/v1/auth/me").status_code == 401
    with browser.session_factory() as db:
        assert db.get(User, person["id"]) is None
        assert db.query(UserSession).count() == db.query(CareerCoachState).count() == db.query(CalendarConnection).count() == 0
        task = db.query(FileErasureTask).one()
        assert task.owner_id is None and task.state == "completed"


def test_owner_and_last_administrator_are_protected(client):
    _, owner = register(client, "erase-owner", "company", company_name="Owner", nit="OWNER-001")
    response = client.post("/api/v1/account/data/erase", headers=owner, json={"password": PASSWORD, "confirmation": "ELIMINAR"})
    assert response.status_code == 409 and "organización" in response.json()["detail"]
    admin = administrator(client)
    assert client.get("/api/v1/account/data", headers=admin).json()["deletion_block"]


def test_private_file_failure_is_durable_retry_not_false_success(client):
    person, headers = register(client, "retry-erasure")
    def unavailable(identifier):
        raise OSError("PRIVATE PATH AND SECRET")
    client.app.dependency_overrides[get_account_files] = lambda: SimpleNamespace(erase=unavailable)
    result = client.post("/api/v1/account/data/erase", headers=headers, json={"password": PASSWORD, "confirmation": "ELIMINAR"})
    assert result.status_code == 200 and result.json()["files_pending"] is True
    assert "SECRET" not in result.text
    with client.session_factory() as session:
        db = SqlAlchemyUnitOfWork(session)
        task = session.query(FileErasureTask).one()
        assert task.owner_id == person["id"] and task.state == "retry"
        task.next_attempt_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
        assert process_erasure(db, task, SimpleNamespace(erase=lambda identifier: None))
        assert task.owner_id is None


def test_local_private_files_never_cross_owner_prefix(tmp_path):
    (tmp_path / "profile_photos").mkdir()
    for name in ("user_1_cv.pdf", "user_10_cv.pdf"):
        (tmp_path / name).write_bytes(b"%PDF-synthetic")
    (tmp_path / "profile_photos/user_1_photo.png").write_bytes(b"synthetic")
    files = PrivateAccountFiles(SimpleNamespace(upload_dir=str(tmp_path), azure_storage_account_url=""))
    assert len(files.export(1)) == 2
    files.erase(1)
    assert (tmp_path / "user_10_cv.pdf").exists() and not (tmp_path / "user_1_cv.pdf").exists()


def test_withdrawal_removes_submitted_documents_and_room_without_touching_other_candidates(client):
    from app.infrastructure.database.models import (
        CalendarEvent,
        InterviewParticipant,
        InterviewRoom,
        Notification,
        TrustIncident,
    )
    person, headers = register(client, "withdraw-person")
    other, _ = register(client, "remaining-person")
    employer, owner = register(client, "withdraw-company", "company", company_name="Withdrawal", nit="WITHDRAW-01")
    job = create_job(client, owner)
    with client.session_factory() as session:
        application = Application(user_id=person["id"], job_id=job["id"], coach_snapshot={"name": "Submitted private CV"})
        remaining = Application(user_id=other["id"], job_id=job["id"], recruiter_notes="Preserved private note")
        session.add_all([application, remaining])
        session.flush()
        identifier, remaining_id = application.id, remaining.id
        session.add(InterviewRoom(id="1" * 32, application_id=identifier, creator_user_id=employer["id"], title="Synthetic"))
        session.flush()
        session.add(InterviewParticipant(id="2" * 32, room_id="1" * 32, user_id=employer["id"], slot=0, expires_at=datetime.utcnow() + timedelta(hours=1)))
        session.add(CalendarEvent(id="3" * 32, user_id=employer["id"], application_id=identifier, remote_id="ts0123"))
        session.add(TrustIncident(reporter_user_id=other["id"], company_id=job["company_id"], application_id=identifier, category="other", details="Withdrawn personal text"))
        session.add(Notification(user_id=employer["id"], type="application_received", title="Postulación", body=f"{person['name']} se postuló a {job['title']}.", action_url=f"/empresa/postulaciones?job={job['id']}"))
        session.commit()
    client.app.dependency_overrides[get_account_files] = lambda: SimpleNamespace(erase=lambda identifier: None)
    result = client.post("/api/v1/account/data/erase", headers=headers, json={"password": PASSWORD, "confirmation": "ELIMINAR"})
    assert result.status_code == 200, result.text
    with client.session_factory() as session:
        assert session.get(Application, identifier) is None
        assert session.get(Application, remaining_id).recruiter_notes == "Preserved private note"
        assert session.get(User, employer["id"]) and session.get(User, other["id"])
        assert session.query(CalendarEvent).count() == session.query(InterviewRoom).count() == session.query(InterviewParticipant).count() == session.query(TrustIncident).count() == 0
        assert person["name"] not in session.query(Notification).filter_by(user_id=employer["id"]).one().body


def test_readiness_fails_closed_and_metrics_hide_ids(client):
    client.app.dependency_overrides[get_resume_reader] = lambda: SimpleNamespace(storage_available=lambda: False)
    assert client.get("/health/live").status_code == 200
    response = client.get("/health/ready")
    assert response.status_code == 503 and response.json()["checks"]["private_storage"] is False
    assert "x-request-id" in response.headers
    assert client.get("/api/v1/admin/operations").status_code == 401
    _, headers = register(client, "metrics-person")
    assert client.get("/api/v1/admin/operations", headers=headers).status_code == 403
    result = client.get("/api/v1/admin/operations", headers=administrator(client))
    assert result.status_code == 200 and result.json()["alerts"]
    assert "metrics-person" not in result.text
    metrics = RequestMetrics()
    for _ in range(600):
        metrics.observe("GET", "/users/{user_id}", 500, 42)
    snapshot = metrics.snapshot()
    assert snapshot["routes"][0] == {"method": "GET", "route": "/users/{user_id}", "samples": 512, "errors": 512, "p95_ms": 42}


def test_retention_removes_only_expired_metadata(client):
    person, _ = register(client, "retention-person")
    with client.session_factory() as session:
        db = SqlAlchemyUnitOfWork(session)
        old = datetime.utcnow() - timedelta(days=200)
        session.add(FileErasureTask(id="c" * 32, owner_id=None, state="completed", created_at=old, completed_at=old))
        session.add(FileErasureTask(id="d" * 32, owner_id=98765, state="retry", created_at=old))
        db.commit()
        counts = db.account_data.retain(datetime.utcnow() - timedelta(days=90))
        db.commit()
        assert counts["receipts"] == 1 and session.get(FileErasureTask, "d" * 32)
        assert session.get(User, person["id"])


def test_expired_cleanup_worker_cannot_overwrite_reclaimed_task(client):
    with client.session_factory() as session:
        db = SqlAlchemyUnitOfWork(session)
        task = db.account_data.erasure_task(12345)
        db.commit()
        now = datetime.utcnow()
        assert db.account_data.claim_erasure(task.id, "old-worker", now)
        db.commit()
        assert not db.account_data.claim_erasure(task.id, "early-worker", now)
        assert db.account_data.claim_erasure(task.id, "replacement-worker", now + timedelta(minutes=11))
        db.commit()
        assert not db.account_data.finish_erasure(task.id, "old-worker", {"state": "retry"})
        assert db.account_data.finish_erasure(task.id, "replacement-worker", {"state": "completed", "owner_id": None})
        db.commit()
        db.refresh(task)
        assert task.state == "completed" and task.owner_id is None
