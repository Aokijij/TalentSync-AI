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
            "skill_requirements": [{"skill": "sql", "essential": True, "weight": 4}], "response_days": 7,
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
    assert preview["score"] == 93 and preview["can_publish"] is False
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
