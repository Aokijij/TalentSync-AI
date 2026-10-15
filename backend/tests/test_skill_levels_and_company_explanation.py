# ruff: noqa: F811
from types import SimpleNamespace as Row

import pytest
from sqlalchemy import select
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.application.use_cases import matching
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.domain.services.requirement_analysis import requirement_rows, requirement_score
from app.infrastructure.database.models import Application, EventLog, Job, User


def sample(level=None, required="advanced"):
    return Row(skills=["python"], experiences=[], evidence=[], preferences={"skill_levels": {"python": level} if level else {}}), Row(skills=["python"], skill_requirements=[{"skill": "python", "weight": 1, "essential": True, "level": required}])


@pytest.mark.parametrize("level,expected", [(None, 50), ("basic", 33.33), ("intermediate", 66.67), ("advanced", 100), ("expert", 100), ("learning", 16.67)])
def test_proficiency_is_compared_to_requested_level_without_inventing_legacy_levels(level, expected):
    profile, job = sample(level)
    rows = requirement_rows(profile, job)
    assert requirement_score(rows) == expected
    assert rows[0]["covered"] == (expected == 100)
    assert rows[0]["declared_level"] == (level or "unspecified")


def test_legacy_presence_is_unchanged_and_declared_learning_never_claims_mastery():
    profile, job = sample(required="unspecified")
    assert requirement_score(requirement_rows(profile, job)) == 100
    profile.preferences["skill_levels"] = {"python": "learning"}
    assert requirement_score(requirement_rows(profile, job)) == 35


def test_profile_levels_persist_normalize_and_invalidate_matching_cache(client):
    user, headers = register(client, "levels-owner", skills=["Python", "administración"])
    _, company = company_account(client, "levels-company")
    job = create_job(client, company)
    client.patch(f"/api/v1/jobs/{job['id']}", headers=company, json={"skill_requirements": [{"skill": "python", "level": "advanced"}]}).raise_for_status()
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    assert profile["skill_levels"] == {}
    endpoint = f"/api/v1/jobs/{job['id']}/match"
    first = client.post(endpoint, headers=headers).json()
    profile["skill_levels"] = {"Python": "advanced", "administración": "intermediate"}
    client.put("/api/v1/profiles/me", headers=headers, json=profile).raise_for_status()
    saved = client.get("/api/v1/profiles/me", headers=headers).json()
    assert saved["skill_levels"] == {"python": "advanced", "administracion": "intermediate"}
    second = client.post(endpoint, headers=headers).json()
    assert second["match_details"]["input_version"] != first["match_details"]["input_version"]
    assert second["skill_match_percentage"] > first["skill_match_percentage"]
    saved.pop("skill_levels")  # Older clients must preserve declared levels.
    client.put("/api/v1/profiles/me", headers=headers, json=saved).raise_for_status()
    assert client.get("/api/v1/profiles/me", headers=headers).json()["skill_levels"]["python"] == "advanced"
    saved["skills"] = ["administración"]
    client.put("/api/v1/profiles/me", headers=headers, json=saved).raise_for_status()
    assert "python" not in client.get("/api/v1/profiles/me", headers=headers).json()["skill_levels"]


def test_company_explanation_is_scoped_private_and_evaluates_only_one_candidate(client, monkeypatch):
    _, company = company_account(client, "explain-owner")
    _, stranger = company_account(client, "explain-stranger")
    job = create_job(client, company)
    user, headers = register(client, "explain-person", skills=["python"])
    with client.session_factory() as db:
        db.get(Job, job["id"]).blind_hiring = True
        db.commit()
    endpoint = f"/api/v1/recommendations/jobs/{job['id']}/candidates/{user['id']}/explanation"
    assert client.get(endpoint, headers=company).status_code == 403
    client.post("/api/v1/matching/evidence", headers=headers, json={"kind": "project", "title": "PRIVATE-EVIDENCE-TITLE", "description": "Implementé python para preparar consultas de prueba.", "skills": ["python"], "add_to_profile": False}).raise_for_status()
    client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"]}).raise_for_status()
    calls = []
    original = matching._candidate_match
    def tracked(profile, target, **kwargs):
        calls.append(profile.user_id)
        return original(profile, target, **kwargs)
    monkeypatch.setattr(matching, "_candidate_match", tracked)
    response = client.get(endpoint, headers=company)
    assert response.status_code == 200, response.text
    assert response.json()["match_details"]["components"]
    assert response.json()["match_details"]["requirements"]
    assert "PRIVATE-EVIDENCE-TITLE" not in response.text
    assert calls == [user["id"]]
    assert client.get(endpoint, headers=stranger).status_code == 403
    assert client.get(endpoint, headers=headers).status_code == 403
    calls.clear()
    assert client.get(endpoint, headers=company).status_code == 200 and not calls
    with client.session_factory() as db:
        db.get(Job, job["id"]).blind_hiring = False
        db.get(User, user["id"]).privacy_preferences = {"share_evidence": False}
        db.commit()
    assert "PRIVATE-EVIDENCE-TITLE" not in client.get(endpoint, headers=company).text
    with client.session_factory() as db:
        db.get(User, user["id"]).privacy_preferences = {"share_evidence": True}
        db.commit()
    assert "PRIVATE-EVIDENCE-TITLE" in client.get(endpoint, headers=company).text


def test_fixture_levels_are_idempotent_and_preserve_personal_profiles_and_edited_jobs(client):
    from scripts.seed_skill_levels import populate
    fixture, _ = register(client, "levels-fixture", skills=["python"])
    personal, _ = register(client, "levels-personal", skills=["python"])
    _, company = company_account(client, "levels-fixture-company")
    first = create_job(client, company)
    edited = create_job(client, company)
    with client.session_factory() as db:
        db.get(User, fixture["id"]).profile.preferences = {"local_fixture": True}
        for identifier in [first["id"], edited["id"]]:
            job = db.get(Job, identifier)
            job.source_name = "local-realistic"
            job.external_id = f"co-test-role-{identifier}-v2"
            job.skill_requirements = [{"skill": "python", "essential": True, "weight": 2}]
            job.quality_details = {"seniority": "senior"}
            job.quality_revision = 1 if identifier == first["id"] else 9
        db.commit()
        before = dict(db.get(User, personal["id"]).profile.preferences or {})
        assert populate(db) == {"profiles_with_declared_levels": 1, "jobs_with_minimum_levels": 1}
        db.commit()
        assert populate(db) == {"profiles_with_declared_levels": 0, "jobs_with_minimum_levels": 0}
        assert db.get(User, personal["id"]).profile.preferences == before
        assert db.get(Job, first["id"]).skill_requirements[0]["level"] == "advanced"
        assert "level" not in db.get(Job, edited["id"]).skill_requirements[0]


def test_admin_vacancy_actions_are_authorized_logged_and_explain_real_process_effects(client):
    admin, _ = register(client, "vacancy-admin")
    person, candidate_headers = register(client, "vacancy-person")
    _, owner = company_account(client, "vacancy-owner")
    _, other = company_account(client, "vacancy-other")
    job = create_job(client, owner)
    application = client.post("/api/v1/applications", headers=candidate_headers, json={"job_id": job["id"]}).json()
    with client.session_factory() as db:
        db.get(User, admin["id"]).role = UserRole.ADMIN
        db.commit()
    login = client.post("/api/v1/auth/admin/login", json={"email": admin["email"], "password": "Test-password-2026!"}).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    endpoint = f"/api/v1/jobs/{job['id']}"
    assert client.patch(endpoint, headers=other, json={"status": "paused"}).status_code == 403
    assert client.patch(endpoint, headers=candidate_headers, json={"status": "paused"}).status_code == 403
    for status in ["paused", "active", "closed"]:
        response = client.patch(endpoint, headers=headers, json={"status": status})
        assert response.status_code == 200, response.text
        with client.session_factory() as db:
            saved = db.get(Application, application["id"])
            assert saved.user_id == person["id"]
            assert saved.status == (ApplicationStatus.REJECTED if status == "closed" else ApplicationStatus.SUBMITTED)
    with client.session_factory() as db:
        events = list(db.scalars(select(EventLog).where(EventLog.event_type == "job.status_updated", EventLog.entity_id == job["id"])))
        assert [row.details["status"] for row in events] == ["paused", "active", "closed"]
        assert all(row.actor_user_id == admin["id"] for row in events)
