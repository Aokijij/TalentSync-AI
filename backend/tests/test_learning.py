# ruff: noqa: F811
from datetime import datetime, timedelta

import pytest
from test_api_flows import client, company_account, create_job, register  # noqa: F401
from test_ecosystem import administrator
from test_learning_resources import content

from app.domain.services.learning_catalog import ASSESSMENTS
from app.infrastructure.database.models import AssessmentAttempt


@pytest.mark.parametrize("assessment_id", list(ASSESSMENTS))
def test_each_assessment_has_public_questions_and_scoped_credential(client, assessment_id):
    bank = ASSESSMENTS[assessment_id]
    _, headers = register(client, "assessment-candidate", skills=[])
    catalog = client.get("/api/v1/learning/catalog?area=all", headers=headers).json()
    assert any(row["id"] == assessment_id for row in catalog["assessments"]) == (not bank.get("retired", False))
    attempt = client.post(f"/api/v1/learning/assessments/{assessment_id}/start", headers=headers).json()
    assert len(attempt["questions"]) == bank.get("question_count", 5)
    assert all({"id", "prompt", "choices"} <= set(question) and not {"answer", "feedback"} & set(question) for question in attempt["questions"])
    with client.session_factory() as db:
        answers = {question["id"]: question["answer"] for question in db.get(AssessmentAttempt, attempt["id"]).snapshot}
    result = client.post(f"/api/v1/learning/attempts/{attempt['id']}/submit", headers=headers, json={"answers": answers})
    assert result.status_code == 200 and result.json()["passed"] and result.json()["score"] == 100
    passport = client.get("/api/v1/learning/passport", headers=headers).json()["assessments"]
    assert passport[0]["skill"] == bank["skill"] and passport[0]["level"] == bank.get("level", "fundamentals") and passport[0]["valid"]


@pytest.mark.parametrize("invalid", [-1, 3, True, "1", 1.5])
def test_invalid_choice_does_not_consume_an_assessment(client, invalid):
    _, headers = register(client, "invalid-choice")
    bank = ASSESSMENTS["git-foundations-v1"]
    attempt = client.post("/api/v1/learning/assessments/git-foundations-v1/start", headers=headers).json()
    answers = {question["id"]: question["answer"] for question in bank["questions"]}
    answers[bank["questions"][0]["id"]] = invalid
    endpoint = f"/api/v1/learning/attempts/{attempt['id']}/submit"
    assert client.post(endpoint, headers=headers, json={"answers": answers}).status_code == 422
    answers[bank["questions"][0]["id"]] = bank["questions"][0]["answer"]
    assert client.post(endpoint, headers=headers, json={"answers": answers}).json()["passed"]


def test_learning_plan_is_separate_from_validated_fundamentals(client):
    _, company = company_account(client)
    job = create_job(client, company)
    _, candidate = register(client, "learner", skills=["Java"])
    admin = administrator(client)
    course_ids = []
    for skill in ("python", "sql"):
        created = client.post("/api/v1/admin/learning/resources", headers=admin, json=content(title=f"Curso de {skill}", skills=[skill], url=f"https://example.org/{skill}"))
        assert created.status_code == 201
        course_ids.append(next(row["id"] for row in created.json() if row["title"] == f"Curso de {skill}"))
    response = client.get(f"/api/v1/learning/jobs/{job['id']}", headers=candidate)
    assert response.status_code == 200
    resources = response.json()["resources"]
    assert {row["id"] for row in resources} == set(course_ids)
    assert all(row["projected_match"] >= row["current_match"] for row in resources)
    assert client.put(f"/api/v1/learning/plans/{course_ids[0]}", headers=candidate, json={"status": "completed"}).status_code == 200
    assert client.get("/api/v1/learning/passport", headers=candidate).json()["assessments"] == []
    assert "python" not in client.get("/api/v1/profiles/me", headers=candidate).json()["skills"]
    endpoint = "/api/v1/learning/assessments/python-foundations-v1/start"
    attempt = client.post(endpoint, headers=candidate).json()
    assert all("answer" not in row and "feedback" not in row for row in attempt["questions"])
    assert client.post(endpoint, headers=candidate).json()["id"] == attempt["id"]
    answers = {row["id"]: row["answer"] for row in ASSESSMENTS["python-foundations-v1"]["questions"]}
    _, other = register(client, "other-learner")
    submit = f"/api/v1/learning/attempts/{attempt['id']}/submit"
    assert client.post(submit, headers=other, json={"answers": answers}).status_code == 404
    assert client.post(submit, headers=candidate, json={"answers": {"fake": 0}}).status_code == 422
    result = client.post(submit, headers=candidate, json={"answers": answers})
    assert result.status_code == 200
    assert result.json()["passed"] is True
    assert result.json()["score"] == 100
    assert client.post(submit, headers=candidate, json={"answers": answers}).status_code == 409
    assert client.post(endpoint, headers=candidate).status_code == 429
    assert "python" in client.get("/api/v1/profiles/me", headers=candidate).json()["skills"]
    assert client.get("/api/v1/learning/passport", headers=candidate).json()["assessments"][0]["valid"] is True


def test_expired_assessments_and_unsupported_skills_cannot_grant_credit(client):
    _, candidate = register(client, "expired-learner")
    assert client.post("/api/v1/learning/assessments/unknown/start", headers=candidate).status_code == 404
    attempt = client.post("/api/v1/learning/assessments/sql-foundations-v1/start", headers=candidate).json()
    with client.session_factory() as db:
        db.get(AssessmentAttempt, attempt["id"]).expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
    answers = {row["id"]: row["answer"] for row in ASSESSMENTS["sql-foundations-v1"]["questions"]}
    assert client.post(f"/api/v1/learning/attempts/{attempt['id']}/submit", headers=candidate, json={"answers": answers}).status_code == 409
    assert client.get("/api/v1/learning/passport", headers=candidate).json()["assessments"] == []


def test_learning_impact_counts_other_active_jobs_once(client):
    _, company = company_account(client)
    target = create_job(client, company)
    _, candidate = register(client, "impact-learner", skills=["Java"])
    endpoint = f"/api/v1/learning/jobs/{target['id']}"
    only_target = client.get(endpoint, headers=candidate).json()
    assert only_target["sampled_jobs"] == 0
    assert all(row["other_jobs_impacted"] == 0 for row in only_target["resources"])
    other = create_job(client, company)
    additional = client.get(endpoint, headers=candidate).json()
    assert additional["sampled_jobs"] == 1
    assert all(row["other_jobs_impacted"] == 1 for row in additional["resources"])
    assert client.patch(f"/api/v1/jobs/{other['id']}", headers=company, json={"status": "paused"}).status_code == 200
    assert client.get(endpoint, headers=candidate).json()["sampled_jobs"] == 0
