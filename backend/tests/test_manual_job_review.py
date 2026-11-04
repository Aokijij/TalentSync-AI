# ruff: noqa: F811
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from test_admin_publication_review import admin, external
from test_api_flows import client  # noqa: F401

from app.application.use_cases.job_availability import check_job
from app.domain.services.job_freshness import externally_available, verification_method
from app.infrastructure.database.models import EventLog, Job
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.job_availability import Availability
from app.infrastructure.repositories.jobs import JobRepository


def publish(client, headers, job_id, **changes):
    payload = {"status": "active", "revision": 0, "note": "Oferta original abierta y formulario de postulación disponible.",
               "manual_verification": {"source_url": "https://job-boards.greenhouse.io/example/jobs/123", "confirmed_open": True,
                                       "note": "Oferta original abierta y formulario de postulación disponible."}}
    return client.patch(f"/api/v1/admin/jobs/{job_id}/catalog-status", headers=headers, json={**payload, **changes})


def test_manual_review_publishes_in_catalog_and_matching_without_forging_api_check(client):
    headers = admin(client)
    job_id, _ = external(client)
    with client.session_factory() as session:
        job = session.get(Job, job_id)
        job.external_check_state = "unknown"
        job.external_verified_at = None
        job.external_checked_at = datetime.utcnow() - timedelta(hours=1)
        session.commit()
    assert publish(client, headers, job_id, manual_verification=None).status_code == 422
    response = publish(client, headers, job_id)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["external_available"] and data["review"]["can_publish"]
    assert data["external_check_state"] == "unknown" and data["external_verification_method"] == "manual"
    with client.session_factory() as session:
        job = session.get(Job, job_id)
        assert job.external_verified_at is None
        assert job.external_manual_verified_by and job.external_manual_note
        assert job in JobRepository(session, Job).active_for_matching()
        event = session.query(EventLog).filter_by(event_type="job.manual_verified").one()
        assert event.actor_user_id == job.external_manual_verified_by and event.details["source"] == "original_listing"
    public = client.get(f"/api/v1/jobs/{job_id}").json()
    assert public["external_verification_method"] == "manual"
    assert "external_manual_note" not in public and "external_manual_verified_by" not in public
    assert publish(client, headers, job_id).status_code == 409


@pytest.mark.parametrize("failure", ["wrong_source", "not_confirmed", "missing_note", "poor_content", "expired", "old_publication"])
def test_invalid_manual_publication_rolls_back_review_and_revision(client, failure):
    headers = admin(client)
    job_id, _ = external(client)
    with client.session_factory() as session:
        job = session.get(Job, job_id)
        job.external_check_state = "unknown"
        if failure == "poor_content":
            job.external_content = {"admission": {"clarity_passed": False}}
        if failure == "expired":
            job.expires_at = datetime.utcnow() - timedelta(days=1)
        if failure == "old_publication":
            job.external_published_at = datetime.utcnow() - timedelta(days=150)
        session.commit()
    manual = {"source_url": "https://job-boards.greenhouse.io/example/jobs/123", "confirmed_open": True, "note": "Confirmé que la oferta original permite enviar postulaciones."}
    if failure == "wrong_source":
        manual["source_url"] = "https://example.com/other"
    if failure == "not_confirmed":
        manual["confirmed_open"] = False
    if failure == "missing_note":
        manual["note"] = ""
    assert publish(client, headers, job_id, manual_verification=manual).status_code == 422
    with client.session_factory() as session:
        job = session.get(Job, job_id)
        assert job.moderation_revision == 0 and job.external_manual_verified_at is None


def test_later_source_closure_revokes_manual_review_but_temporary_failure_does_not(client):
    headers = admin(client)
    job_id, _ = external(client)
    assert publish(client, headers, job_id).status_code == 200
    with client.session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        job = uow.jobs.get(job_id)
        now = datetime.utcnow() + timedelta(minutes=1)
        for state in ("unknown", "unavailable", "closed"):
            gateway = SimpleNamespace(check=lambda *args, **kwargs: Availability(state, "source_removed" if state == "closed" else "unconfirmed"))
            result = check_job(uow, job, gateway, now=now)
            assert result["available"] is (state != "closed")
        assert job.external_manual_verified_until == now
        # A subsequent import or failed check must not resurrect the old review.
        job.external_check_state = "pending"
        assert verification_method(job, now) == "unconfirmed"
        assert not externally_available(job, now)


def test_manual_expiry_source_change_and_future_dates_match_sql_visibility(client):
    headers = admin(client)
    job_id, _ = external(client)
    assert publish(client, headers, job_id).status_code == 200
    with client.session_factory() as session:
        job = session.get(Job, job_id)
        job.external_check_state = "unknown"
        job.external_verified_at = None
        now = datetime.utcnow()
        assert externally_available(job, now)
        assert not externally_available(job, job.external_manual_verified_until)
        assert session.query(Job).filter(Job.id == job_id, JobRepository.fresh_external(job.external_manual_verified_until)).count() == 0
        job.external_url = "https://example.com/different"
        session.flush()
        assert not externally_available(job, now)
        assert session.query(Job).filter(Job.id == job_id, JobRepository.fresh_external(now)).count() == 0
