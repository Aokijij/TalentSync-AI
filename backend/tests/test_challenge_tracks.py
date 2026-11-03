# ruff: noqa: F811
from copy import deepcopy

import pytest
from test_api_flows import client, register  # noqa: F401
from test_ecosystem import administrator
from test_learning_resources import content

from app.core.config import Settings, settings
from app.domain.services.challenge_tracks import related_assessments
from app.domain.services.learning_activities import evaluate
from app.domain.services.learning_catalog import ASSESSMENTS
from app.infrastructure.database.models import AssessmentAttempt


def test_bank_has_real_level_blueprints_private_solutions_and_unique_questions():
    current = [row for row in ASSESSMENTS.values() if row.get("selection")]
    assert len(current) == 111
    assert {row["category"] for row in current} == {"general", "technology", "service", "sales", "administration", "finance", "logistics", "education", "design", "care", "industry", "hospitality", "agriculture", "construction"}
    for bank in current:
        assert bank["question_count"] == {"beginner": 10, "intermediate": 15, "advanced": 20}[bank["level"]]
        assert sum(row["count"] for row in bank["selection"]) == bank["question_count"]
        ids = [row["id"] for row in bank["questions"]]
        assert len(ids) == len(set(ids))
        for question in bank["questions"]:
            assert evaluate(question, question["answer"])
            assert question["topic"] and question["feedback"]
    assert set(related_assessments({"skills": ["HTML", "CSS"]}, ASSESSMENTS)) == {"web-beginner-v2", "web-intermediate-v2", "html-beginner-v1", "html-intermediate-v1", "css-beginner-v1", "css-intermediate-v1"}
    assert not related_assessments({"skills": ["cirugia"]}, ASSESSMENTS)


def test_courses_share_assessment_history_without_completing_courses(client):
    admin = administrator(client)
    _, explorer = register(client, "independent-challenge-discovery")
    global_catalog = client.get("/api/v1/learning/catalog?area=all", headers=explorer).json()["assessments"]
    assert {row["category"] for row in global_catalog} == {row["category"] for row in ASSESSMENTS.values() if not row.get("retired")}
    assert all("related_course_ids" not in row and "questions" not in row for row in global_catalog)
    courses = []
    for title in ("Excel para presupuestos", "Excel para inventarios"):
        response = client.post("/api/v1/admin/learning/resources", headers=admin, json=content(title=title, skills=["excel"]))
        assert response.status_code == 201
        courses.append(next(row for row in response.json() if row["title"] == title))
    _, candidate = register(client, "shared-challenge")
    _, other = register(client, "shared-challenge-other")
    for course in courses:
        assert client.put(f"/api/v1/learning/plans/{course['id']}", headers=candidate, json={}).status_code == 200
    path = f"/api/v1/learning/plans/{courses[0]['id']}/challenges"
    assert client.get(path, headers=other).status_code == 404
    response = client.get(path, headers=candidate).json()
    assert len(response["assessments"]) == 3
    bank_before = deepcopy(ASSESSMENTS["excel-intermediate-v2"])
    attempt = client.post("/api/v1/learning/assessments/excel-intermediate-v2/start", headers=candidate).json()
    assert len(attempt["questions"]) == 15
    assert all("answer" not in question and "feedback" not in question for question in attempt["questions"])
    assert client.post("/api/v1/learning/assessments/excel-intermediate-v2/start", headers=candidate).json() == attempt
    with client.session_factory() as db:
        answers = {row["id"]: row["answer"] for row in db.get(AssessmentAttempt, attempt["id"]).snapshot}
    result = client.post(f"/api/v1/learning/attempts/{attempt['id']}/submit", headers=candidate, json={"answers": answers}).json()
    assert result["score"] == 100 and result["level"] == "intermediate"
    assert sum(row["total"] for row in result["topic_results"]) == 15
    assert ASSESSMENTS["excel-intermediate-v2"] == bank_before
    for course in courses:
        related = client.get(f"/api/v1/learning/plans/{course['id']}/challenges", headers=candidate).json()["assessments"]
        assert next(row for row in related if row["id"] == "excel-intermediate-v2")["last_attempt"]["passed"]
    assert all(row["status"] == "in_progress" for row in client.get("/api/v1/learning/plans", headers=candidate).json())


def production(**overrides):
    return Settings(_env_file=None, **({"environment": "production", "secret_key": "x" * 48, "public_app_url": "https://talent.example.org", "session_auth_enabled": True, "session_cookie_secure": True, "allowed_hosts": ["api.example.org"], "cors_origins": ["https://talent.example.org"], "database_url": "postgresql+psycopg://app:placeholder@db.invalid/talent?sslmode=require"} | overrides))


@pytest.mark.parametrize("overrides", [{"local_mail_enabled": True}, {"local_mfa_review_enabled": True}, {"local_admin_review_enabled": True}, {"session_auth_enabled": False}, {"session_cookie_secure": False}, {"company_mfa_required": False}, {"public_app_url": "http://127.0.0.1:5173"}, {"allowed_hosts": ["*"]}, {"cors_origins": ["http://localhost:5173"]}, {"database_url": "sqlite://"}])
def test_production_refuses_development_shortcuts(overrides):
    with pytest.raises(ValueError):
        production(**overrides)


def test_production_accepts_explicit_separate_frontend_and_api_origins():
    assert production().environment == "production"


def test_production_hides_mailbox_and_rejects_demo_statistics(client, monkeypatch):
    _, candidate = register(client, "production-visibility")
    monkeypatch.setattr(settings, "environment", "production")
    assert client.get("/api/v1/dev/mailbox").status_code == 404
    assert not client.get("/api/v1/auth/options").json()["local_mail"]
    assert client.get("/api/v1/profiles/me/market?dataset=demo", headers=candidate).status_code == 422


def test_new_sector_cases_are_distinct_and_assign_by_declared_skill_not_title():
    from app.application.use_cases.learning_resources import enrich
    from app.domain.services.professional_challenges import (
        TRACKS as PROFESSIONAL_TRACKS,
    )
    from app.domain.services.sector_challenges import TRACKS as SECTOR_TRACKS
    TRACKS = [*SECTOR_TRACKS, *PROFESSIONAL_TRACKS]

    for slug, category, skill, _, _ in TRACKS:
        for level in ("beginner", "intermediate"):
            bank = ASSESSMENTS[f"{slug}-{level}-v1"]
            assert len({item["prompt"] for item in bank["questions"]}) == len(bank["questions"])
            assert {item.get("type", "choice") for item in bank["questions"]} == {"choice", "order", "number", "matching"}
            assert all(item.get("context") for item in bank["questions"] if item["id"].startswith("case-"))
        resource = enrich({"id": "course-coverage", "category": category, "title": "Formación del proveedor", "skills": [skill], "url": "https://example.org/course", "kind": "course", "hours": 1})
        assert f"{slug}-beginner-v1" in resource["assessment_ids"]
        assert all(row["course_skills"] == [skill] for row in resource["assigned_challenges"])
        assert all(not ({"questions", "answer", "feedback", "selection"} & set(row)) for row in resource["assigned_challenges"])
    assert not related_assessments({"title": "Curso de React y Python", "skills": ["historia del arte"]}, ASSESSMENTS)
    assert not related_assessments({"skills": ["turismo sostenible", "agricultura"]}, ASSESSMENTS)
