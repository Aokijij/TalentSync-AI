# ruff: noqa: F811
from types import SimpleNamespace

import pytest
from test_api_flows import client, register  # noqa: F401

from app.domain.services.career_guidance import career_guidance
from app.domain.services.skill_context import profile_skill_context, skill_mentions
from app.infrastructure.nlp.text_processor import text_processor


def profile(**changes):
    return SimpleNamespace(**{"profession": "Analista", "skills": ["sql"], "experiences": [], "educations": [], "experience": "", "preferences": {}, **changes})


@pytest.mark.parametrize("text,expected", [
    ("EDUCACIÓN\nUniversidad Ejemplo\nCONTACTO\nHABILIDADES\nPython\nSQL", {"python": "declared", "sql": "declared"}),
    ("Cursos\nPython\nEducación\nSQL", {"python": "training", "sql": "training"}),
    ("Finalicé un curso de Python", {"python": "training"}),
    ("Experiencia en machine learning con Python", {"python": "applied"}),
    ("Estoy aprendiendo Python. Implementé consultas SQL.", {"python": "learning", "sql": "applied"}),
    ("No tengo experiencia en Python, utilizo SQL", {"python": "negated", "sql": "applied"}),
    ("Estoy estudiando Python y domino SQL", {"python": "learning", "sql": "declared"}),
    ("Python: fundamentos de programación", {"python": "training"}),
])
def test_learning_requires_attached_explicit_cue_not_a_section_or_field_name(text, expected):
    rows = skill_mentions(text, list(expected))
    assert {row["skill"]: row["state"] for row in rows} == expected
    for row in rows:
        assert text[row["start"]:row["end"]].lower() == row["skill"]
        assert row["reason"]
        if row["state"] == "learning":
            assert row["cue"]


def test_multicolumn_style_headings_and_decomposed_accents_keep_skill_offsets():
    text = "EDUCACIO\u0301N\nUniversidad Ejemplo\nTECNOLOGÍAS PROYECTOS\nJavaScript\nHTML5\nCSS3"
    rows = skill_mentions(text, ["javascript", "html", "css"])
    assert len(rows) == 3 and all(row["state"] == "unknown" for row in rows)
    assert [text[row["start"]:row["end"]] for row in rows] == ["JavaScript", "HTML5", "CSS3"]


def test_old_heading_based_learning_is_corrected_on_read_without_reupload_or_skill_changes():
    p = profile(preferences={"cv_skill_context": [{"skill": "python", "state": "learning", "source_section": "learning", "excerpt": "Python"}, {"skill": "sql", "state": "learning", "excerpt": "Estoy aprendiendo SQL"}]})
    rows = profile_skill_context(p)
    assert [row["state"] for row in rows] == ["unknown", "learning"]
    assert p.preferences["cv_skill_context"][0]["state"] == "learning" and p.skills == ["sql"]


def test_training_is_not_auto_declared_and_technical_heading_ends_education_scope():
    result = text_processor.analyze_cv("EDUCACIÓN\nCurso de Python\nTECNOLOGÍAS\nSQL\nMachine learning")
    assert "python" not in result.skills and "sql" in result.skills and "machine learning" in result.skills


def test_coach_guides_real_writing_without_generating_achievements_or_a_hiring_score():
    p = profile(experiences=[{"role": "Asesor comercial", "company": "Equipo", "description": "Encargado de ventas"}])
    before = dict(p.experiences[0])
    advice = career_guidance(p)
    item = next(item for item in advice["items"] if item["writing"])
    assert item["original"] == "Encargado de ventas" and item["experience_index"] == 0
    assert "cifras comprobables" in item["detail"] and "draft" not in item
    assert "score" not in advice and p.experiences[0] == before


def test_timeline_handles_overlaps_and_does_not_invent_gaps_from_year_only_dates():
    p = profile(experiences=[{"start_date": "2019-01", "end_date": "2022-12"}, {"start_date": "2020-01", "end_date": "2021-01"}, {"start_date": "2023-01", "end_date": "2024-01"}])
    assert not any(item["id"] == "timeline" for item in career_guidance(p)["items"])
    p.experiences = [{"start_year": "2020", "end_year": "2021"}, {"start_year": "2023", "end_year": "2024"}]
    assert not any(item["id"] == "timeline" for item in career_guidance(p)["items"])
    p.experiences = [{"start_date": "2020-01", "end_date": "2020-12"}, {"start_date": "2022-01", "end_date": "2023-12"}]
    item = next(item for item in career_guidance(p)["items"] if item["id"] == "timeline")
    assert "12 meses" in item["detail"] and "no reduce" in item["detail"] and item["priority"] == 3


def test_guidance_updates_after_profile_save_and_does_not_include_private_source(client):
    _, headers = register(client, "coach-profile", profession="Analista", skills=["sql"])
    p = client.get("/api/v1/profiles/me", headers=headers).json()
    p["experiences"] = [{"role": "Analista", "company": "Equipo", "description": "Hacía reportes", "start_date": "2020-01", "end_date": "2022-01"}]
    saved = client.put("/api/v1/profiles/me", headers=headers, json=p).json()
    assert any(row["id"] == "impact-0" for row in saved["cv_guidance"]["items"])
    saved["experiences"][0]["description"] = "Preparé reportes y entregué un tablero que permitió consultar pedidos."
    response = client.put("/api/v1/profiles/me", headers=headers, json=saved)
    assert response.status_code == 200, response.text
    assert not any(row["id"] == "impact-0" for row in response.json()["cv_guidance"]["items"])
    assert "cv_source_text" not in response.text
