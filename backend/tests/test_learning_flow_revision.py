# ruff: noqa: F811
from datetime import datetime

from test_api_flows import client, company_account, register  # noqa: F401

from app.domain.services.learning_activities import activities_for
from app.infrastructure.database.models import LearningPlan, User
from app.infrastructure.learn_catalog import LearnCatalog


def test_practice_submission_hides_solutions_locks_scores_and_preserves_history(client):
    _, candidate = register(client, "flow-attempt", skills=[])
    _, other = register(client, "flow-other")
    base = "/api/v1/learning/plans/project-python"
    plan = client.put(base, headers=candidate, json={}).json()[0]
    answers = {row["id"]: row["answer"] for row in activities_for("project-python")}
    wrong = {**answers, "calculation": -999, "connections": [0, 0, 0]}
    draft = client.patch(base + "/journey", headers=candidate, json={"version": plan["version"], "activity_answers": wrong}).json()[0]
    assert draft["progress"]["activity_feedback"] == [] and draft["progress"]["score"] is None
    result = client.patch(base + "/journey", headers=candidate, json={"version": draft["version"], "activity_answers": wrong, "finish": True})
    assert result.status_code == 200, result.text
    plan = result.json()[0]
    assert plan["progress"]["score"] == 33.3 and plan["status"] == "completed"
    feedback = plan["progress"]["activity_feedback"]
    assert "10 − 2 − 1 = 7" not in str(feedback)
    assert feedback[0]["correct"] and "Definir entradas" in feedback[0]["message"]
    assert not plan["progress"]["published"]
    assert client.patch(base + "/journey", headers=candidate, json={"version": plan["version"], "activity_answers": answers, "finish": True}).status_code == 409
    assert client.post(base + "/skills", headers=other).status_code == 404
    assert client.get("/api/v1/profiles/me", headers=candidate).json()["skills"] == []
    assert client.post(base + "/skills", headers=candidate).status_code == 200
    assert "python" in client.get("/api/v1/profiles/me", headers=candidate).json()["skills"]
    retried = client.patch(base + "/journey", headers=candidate, json={"version": plan["version"], "retry": True}).json()[0]
    assert retried["progress"]["activity_answers"] == {} and retried["progress"]["attempt_number"] == 2
    assert client.patch(base + "/journey", headers=other, json={"version": retried["version"], "activity_answers": answers, "finish": True}).status_code == 404
    success = client.patch(base + "/journey", headers=candidate, json={"version": retried["version"], "activity_answers": answers, "finish": True}).json()[0]
    assert success["progress"]["score"] == 100 and success["progress"]["published"]
    assert client.delete(base, headers=candidate, params={"version": success["version"]}).status_code == 200
    history = client.get("/api/v1/learning/passport", headers=candidate).json()["learning_results"]
    assert [row["score"] for row in history] == [100, 33.3]
    assert client.get("/api/v1/learning/passport", headers=other).json()["learning_results"] == []


def test_partial_draft_does_not_evaluate_unfinished_matching(client):
    _, candidate = register(client, "flow-partial")
    base = "/api/v1/learning/plans/project-python"
    plan = client.put(base, headers=candidate, json={}).json()[0]
    response = client.patch(base + "/journey", headers=candidate, json={"version": plan["version"], "activity_answers": {"connections": [0, -1, -1]}})
    assert response.status_code == 200 and response.json()[0]["progress"]["activity_feedback"] == []
    assert client.patch(base + "/journey", headers=candidate, json={"version": response.json()[0]["version"], "activity_answers": {"connections": [0, -1, -1]}, "finish": True}).status_code == 422


def test_legacy_completed_practice_can_retry_without_losing_the_previous_result(client):
    user, candidate = register(client, "flow-legacy")
    base = "/api/v1/learning/plans/project-python"
    plan = client.put(base, headers=candidate, json={}).json()[0]
    answers = {row["id"]: row["answer"] for row in activities_for("project-python")}
    plan = client.patch(base + "/journey", headers=candidate, json={"version": plan["version"], "activity_answers": answers, "finish": True}).json()[0]
    with client.session_factory() as db:
        row = db.query(LearningPlan).filter_by(user_id=user["id"], resource_id="project-python").one()
        row.progress = {key: value for key, value in row.progress.items() if key not in {"submitted", "score", "attempt_number"}}
        db.get(User, user["id"]).profile.preferences = {}
        db.commit()
    retried = client.patch(base + "/journey", headers=candidate, json={"version": plan["version"], "retry": True})
    assert retried.status_code == 200, retried.text
    assert retried.json()[0]["progress"]["attempt_number"] == 2
    history = client.get("/api/v1/learning/passport", headers=candidate).json()["learning_results"]
    assert len(history) == 1 and history[0]["score"] == 100


def test_certificate_survives_plan_refresh_and_evidence_skills_are_opt_in(client):
    _, candidate = register(client, "flow-certificate", skills=[])
    _, other = register(client, "flow-certificate-other")
    base = "/api/v1/learning/plans/microsoft-data-analytics"
    client.put(base, headers=candidate, json={"status": "completed"})
    supplied = {"name": "Documento de formación", "credential_url": "https://example.com/credentials/supplied", "year": datetime.utcnow().year, "has_certificate": True}
    result = client.post(base + "/certificate", headers=candidate, json=supplied)
    assert result.status_code == 200 and result.json()["certificate"]["verified"] is False
    plans = client.get("/api/v1/learning/plans", headers=candidate).json()
    assert plans[0]["certificate"]["name"] == supplied["name"]
    passport = client.get("/api/v1/learning/passport", headers=candidate).json()
    assert passport["certificates"] and passport["learning_results"]
    evidence = client.get("/api/v1/matching/evidence", headers=candidate).json()[0]
    assert "autenticidad" not in evidence["description"]
    assert client.post(f"/api/v1/matching/evidence/{evidence['id']}/skills", headers=other).status_code == 404
    assert client.post(f"/api/v1/matching/evidence/{evidence['id']}/skills", headers=candidate).status_code == 200
    assert client.get("/api/v1/profiles/me", headers=candidate).json()["skills"]
    _, company = company_account(client, "flow-company")
    assert client.post(base + "/skills", headers=company).status_code == 403


def test_learn_metadata_retains_actual_language_level_and_provider_details():
    resource = LearnCatalog._resource({"id": "learn.real-module", "url": "https://learn.microsoft.com/training/modules/real-module/",
        "title": "<b>Introducción</b>", "summary": "<p>Aprende datos &amp; gráficos.</p>", "durationInMinutes": 121,
        "locale": "es-es", "levels": [{"id": "intermediate"}], "products": [{"id": "power-bi", "name": "Power BI"}],
        "prerequisites": "<ul><li>Conocimientos básicos de datos</li></ul>", "units": [{"title": "Preparar los datos"}]})
    details = resource["content"]["details"]
    assert details["languages"] == ["es"] and details["level"] == "intermediate"
    assert details["syllabus"] == ["Preparar los datos"] and "<" not in details["prerequisites"]
    assert details["certificate_cost"] == "none" and resource["content"]["instructions"] == "Aprende datos & gráficos."
