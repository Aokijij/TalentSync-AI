# ruff: noqa: F811
from datetime import datetime, timedelta

from sqlalchemy import event
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.domain.entities.enums import ApplicationStatus, UserRole
from app.infrastructure.database.models import (
    Application,
    CompanyMember,
    Profile,
    Recommendation,
    User,
)
from app.infrastructure.security.jwt import create_access_token


def seed(client, amount=400):
    _, owner = company_account(client, "workspace-owner")
    job = create_job(client, owner)
    with client.session_factory() as db:
        users = [User(name=f"Persona {i:03}", email=f"review-{i}@example.test", password_hash="synthetic-not-a-login", role=UserRole.CANDIDATE) for i in range(amount)]
        db.add_all(users); db.flush()
        for i, user in enumerate(users):
            db.add(Profile(user_id=user.id, profession="Analista de operaciones", skills=["python"], experiences=[], educations=[], certifications=[]))
            status = ApplicationStatus.SUBMITTED if i < amount - 4 else ApplicationStatus.REVIEWING if i < amount - 2 else ApplicationStatus.HIRED if i == amount - 2 else ApplicationStatus.REJECTED
            db.add(Application(user_id=user.id, job_id=job["id"], status=status, pipeline_stage="submitted" if status == ApplicationStatus.SUBMITTED else "reviewing" if status == ApplicationStatus.REVIEWING else "hired" if status == ApplicationStatus.HIRED else "rejected", created_at=datetime(2026, 1, 1) + timedelta(minutes=i), recruiter_notes="PRIVATE TEAM NOTE"))
            if i % 5:
                db.add(Recommendation(user_id=user.id, job_id=job["id"], match_percentage=float(i % 100), reasons=[]))
        db.commit()
    return job, owner


def test_mass_inbox_is_paged_ranked_and_keeps_all_buckets(client):
    job, owner = seed(client)
    url = f"/api/v1/applications/jobs/{job['id']}/workspace"
    statements = []
    engine = client.session_factory.kw["bind"]
    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    event.listen(engine, "before_cursor_execute", capture)
    try:
        response = client.get(url, headers=owner)
    finally:
        event.remove(engine, "before_cursor_execute", capture)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["counts"] == {"inbox": 396, "active": 2, "closed": 2, "interviews": 0}
    assert data["hired_count"] == 1 and data["unreviewed"] == 396
    assert len(data["items"]) == 25 and data["total"] == 396
    assert all(row["adjusted_match_percentage"] is not None for row in data["items"])
    assert [row["adjusted_match_percentage"] for row in data["items"]] == sorted((row["adjusted_match_percentage"] for row in data["items"]), reverse=True)
    assert "PRIVATE TEAM NOTE" not in response.text and "screening_answers" not in response.text
    # A bounded number of queries regardless of applicant count; authorization
    # must not eagerly load every organization's jobs and applications.
    assert len(statements) < 25, len(statements)
    second = client.get(url, params={"page": 2}, headers=owner).json()
    assert not {row["id"] for row in data["items"]} & {row["id"] for row in second["items"]}
    assert client.get(url, params={"score_filter": "missing"}, headers=owner).json()["total"] == 80
    assert all(row["adjusted_match_percentage"] >= 85 for row in client.get(url, params={"score_filter": "strong"}, headers=owner).json()["items"])
    assert client.get(url, params={"search": "Persona 001"}, headers=owner).json()["total"] == 1
    assert client.get(url, params={"search": "%"}, headers=owner).json()["total"] == 0
    assert client.get(url, params={"page_size": 1000}, headers=owner).status_code == 422
    assert client.get(url, params={"bucket": "active", "stage": "reviewing"}, headers=owner).json()["total"] == 2
    assert client.get(url, params={"page": 9999}, headers=owner).json()["page"] == 16


def test_individual_review_is_explicit_private_idempotent_and_versioned(client):
    job, owner = seed(client, 10)
    url = f"/api/v1/applications/jobs/{job['id']}/workspace"
    row = client.get(url, headers=owner).json()["items"][0]
    detail = client.get(f"/api/v1/applications/{row['id']}/review", headers=owner)
    assert detail.status_code == 200, detail.text
    assert detail.json()["application"]["reviewed_at"] is None
    assert detail.json()["profile"]["profession"] == "Analista de operaciones"
    assert "password_hash" not in detail.text and "cv_text" not in detail.text and "email" not in detail.json()["profile"]
    endpoint = f"/api/v1/applications/{row['id']}/reviewed"
    assert client.post(endpoint, headers=owner, json={"expected_version": 9999}).status_code == 409
    result = client.post(endpoint, headers=owner, json={"expected_version": row["version"]})
    assert result.status_code == 200 and result.json()["first_review"] is True
    repeat = client.post(endpoint, headers=owner, json={"expected_version": row["version"]})
    assert repeat.json()["first_review"] is False
    fresh = client.get(url, headers=owner).json()
    assert fresh["unreviewed"] == 5 and fresh["counts"]["inbox"] == 6
    with client.session_factory() as db:
        stored = db.get(Application, row["id"])
        assert stored.status == ApplicationStatus.SUBMITTED and stored.pipeline_stage == "submitted"
    update = client.put(f"/api/v1/applications/{row['id']}/status", headers=owner, json={"pipeline_stage": "reviewing", "expected_version": result.json()["version"]})
    assert update.status_code == 200, update.text
    assert update.json()["reviewed_at"] is not None
    assert client.get(url, headers=owner).json()["counts"]["active"] == 3
    _, stranger = company_account(client, "workspace-stranger")
    _, candidate = register(client, "workspace-candidate")
    for path in (url, f"/api/v1/applications/{row['id']}/review"):
        assert client.get(path, headers=stranger).status_code == 403
        assert client.get(path, headers=candidate).status_code == 403
    assert client.post(endpoint, headers=stranger, json={"expected_version": 1}).status_code == 403
    viewer, _ = register(client, "workspace-interviewer")
    with client.session_factory() as db:
        db.get(User, viewer["id"]).role = UserRole.COMPANY
        db.add(CompanyMember(user_id=viewer["id"], company_id=job["company_id"], role="interviewer", assigned_job_ids=[job["id"]], active=True))
        db.commit()
    assigned = {"Authorization": f"Bearer {create_access_token(str(viewer['id']), 'company')}"}
    assert client.get(url, headers=assigned).status_code == 403
    assert client.get(f"/api/v1/applications/{row['id']}/review", headers=assigned).status_code == 403
    assert client.get(f"/api/v1/workflow/applications/{row['id']}", headers=assigned).status_code == 200
