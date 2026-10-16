# ruff: noqa: F811
from types import SimpleNamespace

import pytest
from test_api_flows import client, company_account, register  # noqa: F401
from test_offer_quality import complete_offer

from app.domain.services.offer_rating import RATING_SCALE, offer_rating
from app.domain.services.offer_review import review_offer
from app.domain.services.offer_writing import writing_draft


@pytest.mark.parametrize("score,code", [(0, "D"), (49, "D"), (50, "C"), (74, "C"), (75, "B"), (89, "B"), (90, "A"), (100, "A")])
def test_quality_bands_cover_each_boundary(score, code):
    assert offer_rating(score)["code"] == code
    assert sum(row["minimum"] <= score <= row["maximum"] for row in RATING_SCALE) == 1


def test_an_excellent_score_does_not_bypass_missing_publication_requirements():
    payload = complete_offer()
    payload["quality_details"]["contract_type"] = ""
    report = review_offer(SimpleNamespace(**payload, pipeline_stages=[{"id": "initial"}]))
    assert report["score"] == 92 and report["rating"]["label"] == "Excelente"
    assert report["can_publish"] is False and report["blockers"][0]["key"] == "contract_type"


def test_editorial_proposals_preserve_evidence_context_and_do_not_invent_work_conditions():
    payload = complete_offer()
    payload["description"] += " Oferta ficticia sin contratación real. Buscamos un perfil dinámico."
    payload["requirements"] += " Se revisará el portafolio durante una conversación técnica."
    payload["languages"] = [{"name": "inglés", "level": "B2"}]
    payload["skill_requirements"].append({"skill": "power bi", "weight": 1, "essential": False})
    result = writing_draft(SimpleNamespace(**payload))
    proposals = {row["field"]: row for row in result["proposals"]}
    description, requirements = proposals["description"]["text"], proposals["requirements"]["text"]
    assert "equipo comercial" in description and "Oferta ficticia sin contratación real" in description
    assert "dinámico" not in description and "Analizar" in description and "60 días" in description
    assert "portafolio" in requirements and "B2" in requirements
    assert "proyectos de formación" in requirements and requirements.count("power bi") == 1
    assert all(row["changes"] for row in proposals.values())
    assert "50 llamadas" not in description and "beneficios" not in description.lower()
    assert "Analizará" in proposals["description"]["original"]
    assert "• Revisar diferencias entre fuentes." in description
    assert "• Preparar un informe semanal con resultados documentados." in description


def test_writing_flags_conflicting_experience_without_choosing_an_invented_requirement():
    payload = complete_offer()
    payload["requirements"] = "Necesitas 5 años de experiencia y conocimientos de SQL demostrables con proyectos."
    result = writing_draft(SimpleNamespace(**payload))
    assert any("años diferentes" in row["text"] for row in result["questions"])
    assert "5 años" in next(row["text"] for row in result["proposals"] if row["field"] == "requirements")


def test_regenerating_applied_proposals_preserves_text_without_duplicating_sections():
    job = SimpleNamespace(**complete_offer())
    first = writing_draft(job)
    for proposal in first["proposals"]:
        setattr(job, proposal["field"], proposal["text"])
    second = writing_draft(job)
    assert {row["field"]: row["text"] for row in first["proposals"]} == {row["field"]: row["text"] for row in second["proposals"]}


def test_writing_separates_inline_actions_preserves_subjects_and_does_not_repeat_conditions():
    job = SimpleNamespace(**complete_offer())
    job.description = "analizara los reportes semanales • documentará diferencias; el equipo revisará las entregas."
    job.required_education_level = "technical"
    job.required_study_fields = ["Sistemas", "Informática"]
    job.quality_details["education_accepts_in_progress"] = True
    result = writing_draft(job)
    texts = {row["field"]: row["text"] for row in result["proposals"]}
    assert "• Analizar los reportes semanales." in texts["description"]
    assert "• Documentar diferencias." in texts["description"]
    assert "El equipo revisará las entregas." in texts["description"]
    assert "Condiciones registradas" not in texts["description"]
    assert "Lunes a viernes" not in texts["description"]
    assert "Técnico · en formación o terminado" in texts["requirements"]
    assert "• Sistemas" in texts["requirements"] and "• Informática" in texts["requirements"]
    for proposal in result["proposals"]:
        setattr(job, proposal["field"], proposal["text"])
    assert texts == {row["field"]: row["text"] for row in writing_draft(job)["proposals"]}


def test_preview_api_returns_bands_and_their_explanation_without_changing_roles(client):
    _, owner = company_account(client, "rating-owner")
    response = client.post("/api/v1/hiring/quality/preview", headers=owner, json=complete_offer())
    assert response.status_code == 200, response.text
    assert response.json()["rating"]["code"] == "A" and len(response.json()["rating_scale"]) == 4
    _, candidate = register(client, "rating-candidate")
    assert client.post("/api/v1/hiring/quality/preview", headers=candidate, json=complete_offer()).status_code == 403
