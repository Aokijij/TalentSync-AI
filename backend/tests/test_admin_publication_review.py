# ruff: noqa: F811
from datetime import datetime, timedelta

import pytest
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import EventLog, Job, Recommendation, User
from app.infrastructure.security.jwt import create_access_token


def admin(client):
    user, _ = register(client, "review-administrator")
    with client.session_factory() as db:
        db.get(User, user["id"]).role = UserRole.ADMIN
        db.commit()
    return {"Authorization": "Bearer " + create_access_token(str(user["id"]), "admin")}


def external(client):
    _, company = company_account(client, "review-employer")
    job = create_job(client, company)
    with client.session_factory() as db:
        row = db.get(Job, job["id"])
        row.source_kind = "external"
        row.source_name = "greenhouse"
        row.external_url = "https://job-boards.greenhouse.io/example/jobs/123"
        row.external_check_state = "verified"
        row.external_verified_at = datetime.utcnow()
        row.external_published_at = datetime.utcnow() - timedelta(days=2)
        row.external_content = {"admission": {"clarity_passed": True}}
        row.skills = ["python", "sql", "excel"]
        db.commit()
    return job["id"], company


def test_editorial_hold_is_persistent_hides_public_lists_matching_and_detail_and_is_audited(client):
    headers = admin(client)
    job_id, _ = external(client)
    endpoint = f"/api/v1/admin/jobs/{job_id}/review"
    user_id = client.get("/api/v1/auth/me", headers=headers).json()["id"]
    with client.session_factory() as db:
        db.add(Recommendation(user_id=user_id, job_id=job_id, match_percentage=99))
        db.commit()
    detail = client.get(endpoint, headers=headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["review"]["can_publish"] and detail.json()["description"]
    held = client.patch(endpoint, headers=headers, json={"status": "held", "note": "Revisar las condiciones antes de publicar", "revision": 0})
    assert held.status_code == 200, held.text
    assert held.json()["moderation_revision"] == 1 and not held.json()["external_available"]
    held_list = client.get("/api/v1/admin/jobs", headers=headers, params={"scope": "all", "status_filter": "held"}).json()
    assert [item["id"] for item in held_list["items"]] == [job_id]
    assert client.get(f"/api/v1/jobs/{job_id}").status_code == 404
    with client.session_factory() as db:
        from app.infrastructure.repositories.jobs import JobRepository
        repository = JobRepository(db, Job)
        assert job_id not in [row.id for row in repository.active_for_matching()]
        from app.infrastructure.repositories.recommendations import (
            RecommendationRepository,
        )
        assert RecommendationRepository(db, Recommendation).for_user_active(user_id) == []
        # Refreshing the source cannot override a separate editorial decision.
        row = db.get(Job, job_id)
        row.status = "active"
        row.external_content = {"admission": {"clarity_passed": True}}
        row.external_verified_at = datetime.utcnow()
        db.commit()
    assert not client.get(endpoint, headers=headers).json()["external_available"]
    assert client.patch(endpoint, headers=headers, json={"status": "approved", "note": "Condiciones revisadas", "revision": 0}).status_code == 409
    approved = client.patch(endpoint, headers=headers, json={"status": "approved", "note": "Condiciones revisadas", "revision": 1})
    assert approved.status_code == 200, approved.text
    assert approved.json()["external_available"] and approved.json()["moderation_revision"] == 2
    with client.session_factory() as db:
        assert db.query(EventLog).filter_by(event_type="job.publication_reviewed", entity_id=job_id).count() == 2


@pytest.mark.parametrize("invalid", ["stale", "unclear", "closed"])
def test_editorial_approval_cannot_bypass_source_readiness(client, invalid):
    headers = admin(client)
    job_id, _ = external(client)
    with client.session_factory() as db:
        row = db.get(Job, job_id)
        if invalid == "stale": row.external_verified_at = datetime.utcnow() - timedelta(days=5)
        if invalid == "unclear": row.external_content = {"admission": {"clarity_passed": False}}
        if invalid == "closed": row.status = "closed"
        db.commit()
    response = client.patch(f"/api/v1/admin/jobs/{job_id}/review", headers=headers, json={"status": "approved", "revision": 0, "note": "Revisión de la oferta"})
    assert response.status_code == 422


def test_records_require_admin_and_never_disclose_authentication_secrets(client):
    headers = admin(client)
    user, candidate = register(client, "review-candidate", profession="Analista", skills=["sql"])
    job_id, company = external(client)
    company_id = client.get(f"/api/v1/admin/jobs/{job_id}/review", headers=headers).json()["company_id"]
    for endpoint in [f"/api/v1/admin/users/{user['id']}", f"/api/v1/admin/companies/{company_id}", f"/api/v1/admin/jobs/{job_id}/review"]:
        assert client.get(endpoint, headers=candidate).status_code == 403
        assert client.get(endpoint, headers=company).status_code == 403
        assert client.get(endpoint).status_code == 401
        response = client.get(endpoint, headers=headers)
        assert response.status_code == 200, response.text
        assert not any(secret in response.text for secret in ["password_hash", "mfa_secret", "recovery_codes", "refresh_token", "embedding"])
    endpoint = f"/api/v1/admin/jobs/{job_id}/review"
    assert client.patch(endpoint, headers=candidate, json={"status": "held", "note": "Revisión", "revision": 0}).status_code == 403
    assert client.patch(endpoint, headers=headers, json={"status": "held", "note": "   ", "revision": 0}).status_code == 422
    assert client.patch(endpoint, headers=headers, json={"status": "held", "note": "Revisión", "revision": 0, "company_id": 999}).status_code == 422
    assert client.patch(f"/api/v1/jobs/{job_id}", headers=headers, json={"status": "active"}).status_code == 422


def test_internal_record_supports_the_existing_status_workflow(client):
    headers = admin(client)
    _, company = company_account(client, "native-review")
    job = create_job(client, company)
    endpoint = f"/api/v1/admin/jobs/{job['id']}/review"
    response = client.get(endpoint, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["source_kind"] == "internal" and response.json()["review"]["checks"]
    paused = client.patch(f"/api/v1/jobs/{job['id']}", headers=headers, json={"status": "paused"})
    assert paused.status_code == 200, paused.text
    response = client.get(endpoint, headers=headers)
    assert response.json()["status"] == "paused" and response.json()["history"]
    assert client.patch(endpoint, headers=headers, json={"status": "held", "note": "Revisión", "revision": 0}).status_code == 422
