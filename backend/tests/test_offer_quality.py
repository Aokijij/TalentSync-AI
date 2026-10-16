# ruff: noqa: F811
from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace

from test_api_flows import client, company_account, register  # noqa: F401

from app.domain.services.offer_review import local_reference, review_offer
from app.infrastructure.database.models import Job


def complete_offer():
    return {"title": "Analista de datos", "description": "Analizará los reportes de ventas con el equipo comercial, revisará diferencias entre fuentes y preparará un informe semanal con resultados documentados.",
            "requirements": "Fundamentos de SQL y análisis de datos. Se aceptan proyectos de formación como evidencia de los conocimientos y ejemplos de trabajo.",
            "salary": 3500000, "location": "Colombia", "modality": "remote", "employment_type": "full_time", "sector": "Tecnologia y software",
            "skill_requirements": [{"skill": "sql", "essential": True, "weight": 4}, {"skill": "excel", "essential": False, "weight": 2}, {"skill": "analisis de datos", "essential": True, "weight": 3}], "response_days": 7,
            "quality_details": {"version": 1, "salary_max": 4500000, "contract_type": "indefinite", "schedule": "Lunes a viernes, 8:00 a 17:00, con una hora de descanso", "seniority": "junior", "experience_years": 0,
                                "learnable_skills": ["power bi"], "missions": [{"outcome": "Construir un tablero de seguimiento de ventas", "measure": "Revisión documentada y conciliación con las fuentes", "days": 60, "skill": "sql"}], "interview_count": 2, "process_days": 14}}


def test_preview_is_private_and_never_persists_or_publishes(client):
    _, owner = company_account(client, "quality-preview")
    payload = complete_offer()
    payload["status"] = "draft"
    job = client.post("/api/v1/jobs", headers=owner, json=payload).json()
    preview = client.post("/api/v1/hiring/quality/preview", headers=owner, json={**payload, "job_id": job["id"], "title": ""})
    assert preview.status_code == 200, preview.text
    assert preview.json()["can_publish"] is False
    with client.session_factory() as db:
        assert db.get(Job, job["id"]).title == payload["title"]
        assert db.get(Job, job["id"]).status == "draft"
    _, outsider = company_account(client, "quality-other")
    assert client.post("/api/v1/hiring/quality/preview", headers=outsider, json={**payload, "job_id": job["id"]}).status_code == 403
    _, candidate = register(client, "quality-reader")
    assert client.post("/api/v1/hiring/quality/preview", headers=candidate, json=payload).status_code == 403
    assert client.get(f"/api/v1/jobs/{job['id']}").status_code == 404


def test_publication_requires_conditions_even_with_a_high_score(client):
    _, owner = company_account(client, "quality-publish")
    payload = complete_offer()
    payload["quality_details"]["contract_type"] = ""
    preview = client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload).json()
    assert preview["score"] == 92 and preview["can_publish"] is False
    assert client.post("/api/v1/jobs", headers=owner, json=payload).status_code == 422
    saved = client.post("/api/v1/jobs", headers=owner, json={**payload, "status": "draft"})
    assert saved.status_code == 201, saved.text
    job_id = saved.json()["id"]
    assert client.patch(f"/api/v1/jobs/{job_id}", headers=owner, json={"status": "active"}).status_code == 422
    assert client.patch(f"/api/v1/jobs/{job_id}", headers=owner, json={"quality_details": None, "status": "active"}).status_code == 422
    details = complete_offer()["quality_details"]
    published = client.patch(f"/api/v1/jobs/{job_id}", headers=owner, json={"status": "active", "quality_details": details})
    assert published.status_code == 200, published.text
    assert {key: published.json()["quality_summary"][key] for key in ("score", "level", "can_publish")} == {"score": 100, "level": "A", "can_publish": True}
    assert published.json()["quality_summary"]["rating"]["label"] == "Excelente"
    assert client.get(f"/api/v1/jobs/{job_id}").json()["quality_details"]["missions"][0]["days"] == 60


def test_job_list_quality_matches_review_for_guided_and_legacy_offers(client):
    _, owner = company_account(client, "quality-list")
    complete = client.post("/api/v1/jobs", headers=owner, json=complete_offer()).json()
    legacy_payload = complete_offer()
    del legacy_payload["quality_details"]
    legacy = client.post("/api/v1/jobs", headers=owner, json=legacy_payload).json()
    offers = {row["id"]: row for row in client.get("/api/v1/jobs", headers=owner).json()}
    for job in (complete, legacy):
        report = client.get(f"/api/v1/hiring/quality/{job['id']}", headers=owner).json()
        assert offers[job["id"]]["quality_summary"] == {
            key: report[key] for key in ("score", "level", "can_publish", "rating")
        }
    assert offers[complete["id"]]["quality_summary"]["score"] == 100
    assert offers[legacy["id"]]["quality_summary"]["score"] < 100
    assert offers[legacy["id"]]["quality_summary"]["can_publish"] is False


def test_structured_conflicts_and_wording_have_actionable_explanations(client):
    _, owner = company_account(client, "quality-conflicts")
    payload = complete_offer()
    payload["quality_details"].update(experience_years=7, salary_max=2000000, process_days=3)
    payload["description"] += " Buscamos un guerrero con trabajo bajo presión."
    report = client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload).json()
    assert {row["code"] for row in report["issues"]} >= {"level_conflict", "salary_range", "process_conflict"}
    assert any(row["suggestion"] and row["phrase"] == "guerrero" for row in report["issues"])
    assert not report["can_publish"]
    payload = complete_offer()
    payload["quality_details"]["learnable_skills"] = ["sql"]
    assert "learnable_conflict" in {row["code"] for row in client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload).json()["issues"]}
    payload["quality_details"]["salary_max"] = -1
    assert client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload).status_code == 422


def test_feedback_is_explicit_retractable_aggregated_and_scoped_to_revision(client):
    _, owner = company_account(client, "quality-feedback")
    job = client.post("/api/v1/jobs", headers=owner, json=complete_offer()).json()
    endpoint = f"/api/v1/hiring/feedback/{job['id']}"
    report_url = f"/api/v1/hiring/quality/{job['id']}"
    candidates = [register(client, f"opinion-{index}")[1] for index in range(5)]
    for headers in candidates[:4]:
        assert client.put(endpoint, headers=headers, json={"reason": "salary"}).status_code == 200
    report = client.get(report_url, headers=owner).json()["feedback"]
    assert report["sample_size"] == 4 and report["reasons"] == []
    assert client.put(endpoint, headers=candidates[4], json={"reason": "requirements"}).status_code == 200
    summary = client.get(report_url, headers=owner)
    assert summary.json()["feedback"]["available"]
    assert {row["key"]: row["count"] for row in summary.json()["feedback"]["reasons"]}["salary"] == 4
    assert "opinion-" not in summary.text and "user_id" not in summary.text
    assert client.put(endpoint, headers=candidates[0], json={"reason": "unclear"}).status_code == 200
    assert client.get(report_url, headers=owner).json()["feedback"]["sample_size"] == 5
    assert client.delete(endpoint, headers=candidates[0]).status_code == 200
    assert client.get(report_url, headers=owner).json()["feedback"]["reasons"] == []
    _, other = company_account(client, "quality-feedback-other")
    assert client.get(report_url, headers=other).status_code == 403
    assert client.get(report_url, headers=candidates[1]).status_code == 403
    assert client.put(endpoint, headers=owner, json={"reason": "salary"}).status_code == 403
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=owner, json={"salary": 3600000}).status_code == 200
    assert client.get(report_url, headers=owner).json()["feedback"]["sample_size"] == 0
    assert client.get(endpoint, headers=candidates[1]).json()["reason"] is None


def test_offer_revision_notifies_current_candidates_but_noop_does_not(client):
    _, owner = company_account(client, "quality-notice")
    job = client.post("/api/v1/jobs", headers=owner, json=complete_offer()).json()
    _, candidate = register(client, "quality-current", profession="Analista de datos", skills=["sql"])
    assert client.post("/api/v1/applications", headers=candidate, json={"job_id": job["id"]}).status_code == 201
    before_match = client.post(f"/api/v1/jobs/{job['id']}/match", headers=candidate).json()["match_percentage"]
    revision = job["quality_revision"]
    same = client.patch(f"/api/v1/jobs/{job['id']}", headers=owner, json={"salary": job["salary"]})
    assert same.json()["quality_revision"] == revision
    changed = client.patch(f"/api/v1/jobs/{job['id']}", headers=owner, json={"salary": 3600000})
    assert changed.json()["quality_revision"] == revision + 1
    notifications = client.get("/api/v1/notifications", headers=candidate).json()
    assert sum(row["type"] == "job_conditions_updated" for row in notifications) == 1
    after_match = client.post(f"/api/v1/jobs/{job['id']}/match", headers=candidate).json()["match_percentage"]
    assert after_match == before_match


def test_local_reference_requires_independent_comparable_recent_companies():
    payload = complete_offer()
    subject = SimpleNamespace(**payload, id=1, company_id=1, pipeline_stages=[{"id": "initial"}])
    peers = [SimpleNamespace(**deepcopy(payload), id=index + 2, company_id=index + 2, created_at=datetime.utcnow(), source_kind="internal", source_name=None) for index in range(5)]
    assert local_reference(subject, peers)["median"] == 3500000
    peers[0].company_id = peers[1].company_id
    assert local_reference(subject, peers)["median"] is None
    peers[0].company_id = 2
    peers[0].quality_details["seniority"] = "senior"
    assert local_reference(subject, peers)["median"] is None
    peers[0].quality_details["seniority"] = "junior"
    peers[0].source_name = "local-quality-demo"
    assert local_reference(subject, peers)["median"] is None
    assert sum(row["weight"] for row in review_offer(subject)["checks"]) == 100


def test_responsibilities_keep_their_points_without_optional_missions(client):
    _, owner = company_account(client, "quality-optional-mission")
    payload = complete_offer()
    payload["quality_details"]["missions"] = []
    preview = client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload).json()
    assert preview["score"] == 91 and preview["can_publish"] is True
    assert preview["minimum_publish_score"] == 60
    assert preview["blockers"] == []
    assert client.post("/api/v1/jobs", headers=owner, json=payload).status_code == 201


def test_minimal_publishable_offer_keeps_education_questions_and_choice_scores(client):
    _, owner = company_account(client, "quality-minimum")
    payload = complete_offer()
    payload["title"] = "Analista"
    payload["quality_details"].update(schedule="", missions=[], interview_count=None, process_days=None)
    payload["skill_requirements"][0]["essential"] = False
    payload["required_education_level"] = "technical"
    payload["required_study_fields"] = ["Sistemas"]
    questions = [{"id": "availability", "prompt": "¿Puedes asistir los sábados?", "type": "choice", "required": True,
                  "options": ["Sí", "No"], "option_scores": {"Sí": 3, "No": -1}}]
    payload["application_questions"] = questions
    preview = client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload).json()
    assert preview["score"] == 76 and preview["can_publish"] is True
    assert all(not row["required"] for row in preview["next_actions"])
    saved = client.post("/api/v1/jobs", headers=owner, json=payload)
    assert saved.status_code == 201, saved.text
    job = saved.json()
    assert job["required_education_level"] == "technical" and job["required_study_fields"] == ["Sistemas"]
    assert client.get(f"/api/v1/jobs/{job['id']}/application-questions", headers=owner).json()[0]["option_scores"] == questions[0]["option_scores"]
    assert "option_scores" not in client.get(f"/api/v1/jobs/{job['id']}").json()["application_questions"][0]


def test_unknown_work_city_cannot_be_published_even_with_a_high_score(client):
    _, owner = company_account(client, "quality-invalid-city")
    payload = complete_offer()
    payload.update(modality="onsite", location="Ciudad inventada 123")
    preview = client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload).json()
    assert preview["score"] == 92 and preview["can_publish"] is False
    assert [row["key"] for row in preview["blockers"]] == ["location"]
    assert client.post("/api/v1/jobs", headers=owner, json=payload).status_code == 422
    legacy_payload = {key: value for key, value in payload.items() if key != "quality_details"}
    assert client.post("/api/v1/jobs", headers=owner, json=legacy_payload).status_code == 422
    saved = client.post("/api/v1/jobs", headers=owner, json={**payload, "status": "draft"})
    assert saved.status_code == 201
    job_id = saved.json()["id"]
    assert client.patch(f"/api/v1/jobs/{job_id}", headers=owner, json={"status": "active"}).status_code == 422
    published = client.patch(f"/api/v1/jobs/{job_id}", headers=owner, json={"status": "active", "location": "medellin, Antioquia"})
    assert published.status_code == 200, published.text


def test_incomplete_optional_process_cannot_hide_a_contradiction(client):
    _, owner = company_account(client, "quality-process-conflict")
    payload = complete_offer()
    payload["quality_details"].update(missions=[], interview_count=None, process_days=3)
    report = client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload).json()
    assert not report["can_publish"]
    assert any(row["code"] == "process_conflict" for row in report["issues"])


def test_remote_work_needs_no_city_or_country_to_publish(client):
    _, owner = company_account(client, "quality-remote-global")
    payload = complete_offer()
    payload["location"] = ""
    preview = client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload).json()
    assert preview["can_publish"] and preview["minimum_publish_score"] == 60
    assert next(row for row in preview["checks"] if row["key"] == "location")["points"] == 8
    assert client.post("/api/v1/jobs", headers=owner, json=payload).status_code == 201


def test_partial_quality_keeps_independent_credit_for_each_relevant_field(client):
    _, owner = company_account(client, "quality-partial")
    payload = complete_offer()
    payload["quality_details"].update(missions=[], seniority="", experience_years=None, interview_count=None)
    report = client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload).json()
    checks = {row["key"]: row for row in report["checks"]}
    assert checks["description"]["points"] == checks["description"]["weight"] == 15
    assert checks["missions"]["points"] == 0 and checks["missions"]["weight"] == 9
    assert checks["requirements"]["points"] == 4 and checks["requirements"]["state"] == "partial"
    assert checks["process"]["points"] == 4
    assert report["score"] == sum(row["points"] for row in report["checks"])
    assert sum(row["weight"] for row in report["checks"]) == 100
    assert not report["can_publish"] and [row["key"] for row in report["blockers"]] == ["requirements"]
    payload["quality_details"].update(seniority="entry", experience_years=0, missions=[{"outcome": "Preparar un informe con las ventas", "measure": "", "days": 30}])
    updated = client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload).json()
    partial_mission = next(row for row in updated["checks"] if row["key"] == "missions")
    assert partial_mission["points"] == 6 and partial_mission["state"] == "partial"
    assert updated["can_publish"] and not partial_mission["required"]


def test_structured_schedule_is_saved_with_its_public_text_and_rejects_invalid_times(client):
    _, owner = company_account(client, "quality-structured-schedule")
    payload = complete_offer()
    schedule = {"mode": "fixed", "days": ["mon", "tue", "wed", "thu", "fri"], "start": "08:00", "end": "17:00", "break_minutes": 60, "notes": ""}
    payload["quality_details"]["work_schedule"] = schedule
    saved = client.post("/api/v1/jobs", headers=owner, json=payload)
    assert saved.status_code == 201, saved.text
    assert saved.json()["quality_details"]["work_schedule"] == schedule
    payload["quality_details"]["work_schedule"]["start"] = "25:30"
    assert client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload).status_code == 422


def test_guided_vacancies_keep_blind_hiring_and_secondary_education_consistent(client):
    _, owner = company_account(client, "quality-secondary-policy")
    payload = complete_offer()
    payload.update(blind_hiring=False, required_education_level="secondary", required_study_fields=["Sistemas"])
    payload["quality_details"]["education_accepts_in_progress"] = True
    saved = client.post("/api/v1/jobs", headers=owner, json=payload)
    assert saved.status_code == 201, saved.text
    job = saved.json()
    assert job["blind_hiring"] is True
    assert job["required_study_fields"] == []
    assert job["quality_details"]["education_accepts_in_progress"] is False
    changed = client.patch(f"/api/v1/jobs/{job['id']}", headers=owner, json={"quality_details": payload["quality_details"], "required_study_fields": ["Administración"]})
    assert changed.status_code == 200, changed.text
    assert changed.json()["required_study_fields"] == []
    assert changed.json()["quality_details"]["education_accepts_in_progress"] is False


def test_long_screening_questions_and_options_survive_creation_editing_and_submission(client):
    _, owner = company_account(client, "quality-long-screening")
    payload = complete_offer()
    prompt = "Explica cómo resolverías esta situación. " * 20
    option = "Verificar la información con el equipo. " * 20
    assert 500 < len(prompt) <= 1000 and 500 < len(option) <= 1000
    question = {"id": "long", "prompt": prompt, "type": "choice", "required": True, "options": [option, "Consultar otra alternativa"], "option_scores": {option: 3}}
    payload["application_questions"] = [question]
    saved = client.post("/api/v1/jobs", headers=owner, json=payload)
    assert saved.status_code == 201, saved.text
    job_id = saved.json()["id"]
    configured = client.get(f"/api/v1/jobs/{job_id}/application-questions", headers=owner).json()[0]
    assert configured["prompt"] == prompt and configured["options"][0] == option
    assert configured["option_scores"][option] == 3
    question["prompt"] = "¿" + "a" * 998 + "?"
    assert client.patch(f"/api/v1/jobs/{job_id}", headers=owner, json={"application_questions": [question]}).status_code == 200
    question["prompt"] += "a"
    assert client.patch(f"/api/v1/jobs/{job_id}", headers=owner, json={"application_questions": [question]}).status_code == 422
    _, candidate = register(client, "long-screening-candidate")
    applied = client.post("/api/v1/applications", headers=candidate, json={"job_id": job_id, "screening_answers": [{"question_id": "long", "answer": option}]})
    assert applied.status_code == 201, applied.text
    with client.session_factory() as db:
        answer = db.get(Job, job_id).applications[0].screening_answers[0]
        assert answer["answer"] == option.strip() and answer["configured_adjustment"] == 3
