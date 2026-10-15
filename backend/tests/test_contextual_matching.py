# ruff: noqa: F811
from datetime import date
from types import SimpleNamespace

import pytest
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.domain.services.matching_text import professional_sections
from app.domain.services.requirement_analysis import (
    relevant_experience,
    requirement_rows,
    requirement_score,
)
from app.domain.services.skill_context import skill_mentions
from app.infrastructure.nlp.text_processor import text_processor


def profile(**changes):
    return SimpleNamespace(skills=[], profession="", experience="", experiences=[], evidence=[], educations=[], certifications=[], preferences={}, **changes)


def job(**changes):
    return SimpleNamespace(skills=["python", "fastapi"], skill_requirements=[], title="Desarrollador backend", description="Desarrollar servicios y APIs", requirements="Python y FastAPI", quality_details={"experience_years": 2}, **changes)


@pytest.mark.parametrize("text,state", [
    ("Desarrollé servicios con Python", "applied"), ("Estoy aprendiendo Python", "learning"),
    ("No tengo experiencia en Python", "negated"), ("Python: sin experiencia", "negated"),
    ("I have never used Python", "negated"), ("I am learning Python", "learning"),
    ("Habilidades: Python", "declared"), ("No solo uso Python, también SQL", "applied"),
])
def test_context_distinguishes_use_learning_negation_and_explicit_declarations(text, state):
    assert skill_mentions(text, ["python"])[0]["state"] == state


def test_clause_scope_aliases_and_no_implicit_leadership_skills():
    rows = skill_mentions("Sin experiencia en Python, pero implementé consultas SQL; estoy aprendiendo k8s.", ["python", "sql", "kubernetes"])
    assert {row["skill"]: row["state"] for row in rows} == {"python": "negated", "sql": "applied", "kubernetes": "learning"}
    assert skill_mentions("Lideré diez personas durante tres años", ["scrum", "gestion de proyectos"]) == []


def test_cv_extracts_only_supported_positive_skills_and_retains_learning_context():
    result = text_processor.analyze_cv("Desarrollador backend\nImplementé APIs con Python y SQL.\nEstoy aprendiendo Kubernetes.\nNo tengo experiencia en Java.")
    assert {"python", "sql"} <= set(result.skills)
    assert "kubernetes" not in result.skills and "java" not in result.skills
    assert {row["state"] for row in result.skill_context} >= {"applied", "learning", "negated"}
    contradictory = text_processor.analyze_cv("Habilidades: Python\nNo tengo experiencia en Python")
    assert "python" not in contradictory.skills
    # Requirements extraction is separate: no change to the vacancy parser.
    assert "python" in text_processor.analyze_job("Se requiere experiencia en Python").skills


def test_course_and_project_sections_do_not_become_hidden_professional_skills():
    result = text_processor.analyze_cv("Cursos\nPython\nProyectos\nImplementé una API con FastAPI\nHabilidades\nSQL")
    assert "python" not in result.skills and "fastapi" not in result.skills and "sql" in result.skills
    assert any(row["skill"] == "fastapi" and row["state"] == "project" for row in result.skill_context)
    p = profile()
    p.preferences = {"cv_skill_context": result.skill_context}
    rows = requirement_rows(p, job())
    assert [row["status"] for row in rows] == ["unknown", "partial"]
    assert rows[1]["score"] == 70 and rows[1]["related_months"] == 0


def test_requirement_statuses_are_traceable_and_do_not_change_profile_skills():
    p = profile()
    p.skills = ["sql"]
    p.experiences = [{"role": "Desarrollador Python", "start_date": "2020-01", "end_date": "2021-06", "description": "Implementé servicios con Python. Estoy aprendiendo FastAPI."}]
    p.evidence = [{"title": "Proyecto SQL", "kind": "project", "skills": ["sql"]}]
    j = job()
    j.skills = ["python", "fastapi", "sql", "java"]
    rows = requirement_rows(p, j)
    assert [row["status"] for row in rows] == ["fulfilled", "partial", "fulfilled", "unknown"]
    assert rows[0]["related_months"] == 18 and rows[0]["supporting_experiences"] == 1
    assert rows[1]["supporting_experiences"] == 0 and rows[1]["score"] == 35
    assert rows[2]["evidence"][0]["verified"] is False
    assert p.skills == ["sql"]
    assert requirement_score(rows) == 58.75


def test_relevant_experience_unions_overlapping_roles_and_excludes_unrelated_jobs():
    p = profile()
    p.experiences = [
        {"role": "Desarrollador backend", "description": "Implementé Python", "start_date": "2020-01", "end_date": "2021-06"},
        {"role": "Desarrollador de software", "description": "APIs", "start_date": "2020-06", "end_date": "2021-06"},
        {"role": "Vendedor", "description": "Venta de alimentos", "start_date": "2010-01", "end_date": "2019-12"},
    ]
    result = relevant_experience(p, job(), today=date(2026, 10, 13))
    assert result["related_months"] == 18 and result["required_months"] == 24
    assert result["related_roles"] == 2 and result["status"] == "partial" and result["score"] == 75


def test_incomplete_year_only_and_current_periods_are_not_invented():
    p = profile()
    p.experiences = [{"role": "Desarrollador", "start_date": "2020-01"}]
    missing = relevant_experience(p, job(), today=date(2026, 10, 13))
    assert missing["related_months"] == 0 and missing["status"] == "unknown" and missing["roles_without_dates"] == 1
    p.experiences = [{"role": "Desarrollador", "start_year": "2020", "end_year": "2021"}]
    assert relevant_experience(p, job())["estimated"] is True
    p.experiences = [{"role": "Desarrollador", "start_date": "2026-01", "is_current": True}]
    assert relevant_experience(p, job(), today=date(2026, 10, 13))["related_months"] == 10


def test_sections_keep_roles_functions_and_knowledge_separate_and_strip_identifiers():
    p = profile()
    p.profession = "Desarrolladora backend"
    p.skills = ["python"]
    p.user = SimpleNamespace(name="Persona Privada", email="private@example.com")
    p.experiences = [{"role": "Backend Python", "company": "Empresa Privada", "description": "Persona Privada implementó una API en Empresa Privada. private@example.com"}]
    pairs = professional_sections(p, job())
    assert {row[0] for row in pairs} == {"roles", "responsibilities", "technical"}
    assert "Persona Privada" not in str(pairs) and "private@example.com" not in str(pairs) and "Empresa Privada" not in str(pairs)
    assert next(row for row in pairs if row[0] == "technical")[2] == "python"


def test_import_preserves_confirmed_records_and_distinct_rehires():
    from app.application.use_cases.profiles import _merge_imported
    old = [{"role": "Backend", "company": "Equipo", "start_year": "2020", "end_year": "2021", "description": "Confirmado"}]
    imported = [{"role": "Backend", "company": "Equipo", "start_year": "2020", "end_year": "2021", "description": "Detectado"}, {"role": "Backend", "company": "Equipo", "start_year": "2024", "end_year": "2025"}]
    rows = _merge_imported(old, imported, ("role", "company"))
    assert len(rows) == 2 and rows[0]["description"] == "Confirmado" and len(old) == 1


def test_semantic_matching_encodes_three_distinct_sections_with_existing_local_interface():
    from app.application.use_cases.matching import candidate_match
    calls = []
    class RecordingAnalysis:
        def embed(self, text):
            return [1]
        def matching_similarity(self, left, right, embedding):
            calls.append((left, right))
            return 80
    p, j = profile(), job()
    p.skills, p.profession, p.experience = ["python"], "Desarrollador", "Construí APIs"
    j.sector = ""
    result = candidate_match(p, j, nlp=RecordingAnalysis())
    assert len(calls) == 3 and {right for _, right in calls} == {j.title, j.description, j.requirements}
    assert calls[1][0] == "Construí APIs" and calls[2][0] == "python"
    assert 0 <= result[0] <= 100


def test_recommendation_api_exposes_context_recomputes_experience_and_preserves_privacy(client):
    _, company = company_account(client, "context-company")
    created = create_job(client, company)
    _, candidate = register(client, "context-candidate", skills=["python"])
    p = client.get("/api/v1/profiles/me", headers=candidate).json()
    p.update(profession="Desarrollador backend", experiences=[{"role": "Backend Python", "company": "Empresa privada", "description": "Implementé Python. Estoy aprendiendo FastAPI.", "start_date": "2020-01", "end_date": "2021-06"}])
    saved = client.put("/api/v1/profiles/me", headers=candidate, json=p)
    assert saved.status_code == 200, saved.text
    endpoint = f"/api/v1/matching/jobs/{created['id']}"
    first = client.get(endpoint, headers=candidate).json()
    assert first["version"] == "contextual-match-v11" and len(first["section_scores"]) == 3
    assert all("excerpt" not in row for row in first["requirements"])
    assert abs(sum(row["points"] for row in first["components"]) - first["overall_score"]) < .02
    assert client.get(endpoint, headers=company).status_code == 403
    assert "Empresa privada" not in str(first)
    from app.infrastructure.database.models import Job
    with client.session_factory() as db:
        db.get(Job, created["id"]).quality_details = {"experience_years": 2}
        db.commit()
    refreshed = client.get("/api/v1/recommendations/me/jobs", headers=candidate, params={"include_all": True}).json()[0]["match_details"]
    assert refreshed["experience_requirement"]["required_months"] == 24
    assert refreshed["experience_requirement"]["related_months"] == 18
    assert refreshed["experience_requirement"]["status"] == "partial"
    assert refreshed["input_version"] != first["input_version"]


def test_cv_upload_keeps_existing_certificate_documents_and_exposes_context_only_to_owner(client, monkeypatch, tmp_path):
    from app.core.config import settings
    from app.infrastructure.nlp import resumes
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr(resumes, "extract_pdf_text", lambda _: "Desarrollador Python\nImplementé Python. Estoy aprendiendo Kubernetes. No tengo experiencia en Java.")
    _, candidate = register(client, "context-upload", skills=[])
    p = client.get("/api/v1/profiles/me", headers=candidate).json()
    p["certifications"] = [{"name": "Curso previo", "issuer": "Proveedor", "year": "2025", "url": "https://example.com/credential", "verified": False}]
    client.put("/api/v1/profiles/me", headers=candidate, json=p).raise_for_status()
    response = client.post("/api/v1/profiles/me/cv", headers=candidate, files={"file": ("cv.pdf", b"%PDF-1.4", "application/pdf")})
    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["certifications"][0]["url"] == "https://example.com/credential"
    assert "kubernetes" not in saved["skills"] and "java" not in saved["skills"]
    assert saved["cv_skill_context"] and any(row["state"] == "learning" for row in saved["cv_skill_context"])
