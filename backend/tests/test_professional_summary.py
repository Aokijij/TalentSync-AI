# ruff: noqa: F811
from io import BytesIO
from types import SimpleNamespace as Row

import pytest
from pypdf import PdfReader
from test_api_flows import client, company_account, register  # noqa: F401

from app.api.deps import get_career_writer
from app.application.use_cases import profiles
from app.domain.services.professional_summary import summary_facts, validate_summary
from app.infrastructure.database.models import User
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

TEXT = "Desarrollo interfaces web con React y JavaScript. Reviso requisitos y ejecuto pruebas funcionales para el equipo de desarrollo."


def test_custom_summary_survives_other_edits_legacy_clients_and_pdf_export(client):
    _, headers = register(client, "custom-summary", profession="Desarrollador frontend", skills=["React", "JavaScript"])
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    assert profile["summary_mode"] == "automatic"
    profile.update(experience=TEXT, summary_mode="custom")
    saved = client.put("/api/v1/profiles/me", headers=headers, json=profile)
    assert saved.status_code == 200, saved.text
    assert saved.json()["experience"] == TEXT and saved.json()["summary_mode"] == "custom"
    profile = saved.json()
    profile.pop("summary_mode")  # Older clients do not reset a personal summary.
    profile.update(profession="Desarrollador de aplicaciones", phone="3001234567")
    saved = client.put("/api/v1/profiles/me", headers=headers, json=profile)
    assert saved.json()["experience"] == TEXT and saved.json()["summary_mode"] == "custom"
    pdf = client.post("/api/v1/profiles/me/export", headers=headers, json={"sections": ["summary"], "include_photo": False})
    assert pdf.status_code == 200, pdf.text
    contents = " ".join(page.extract_text() for page in PdfReader(BytesIO(pdf.content)).pages)
    assert "Desarrollo interfaces web con React y JavaScript" in contents
    profile.update(experience="", summary_mode="custom")
    assert client.put("/api/v1/profiles/me", headers=headers, json=profile).json()["experience"] == ""
    profile.update(summary_mode="invalid")
    assert client.put("/api/v1/profiles/me", headers=headers, json=profile).status_code == 422


def test_cv_import_does_not_replace_a_custom_summary(client):
    user, headers = register(client, "summary-cv", skills=["React"])
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    profile.update(experience=TEXT, summary_mode="custom")
    client.put("/api/v1/profiles/me", headers=headers, json=profile).raise_for_status()
    nlp = Row(analyze_cv=lambda _: Row(clean_text="texto", profession="Desarrollador", skills=["JavaScript"], experience="Resumen extraído diferente", education=None, location=None, phone=None,
        experiences=[{"role": "Desarrollador", "company": "Organización", "description": "Desarrollé interfaces", "start_year": "2020", "end_year": "2023"}], educations=[], certifications=[], embedding=[1], skill_context=[]))
    with client.session_factory() as session:
        stored = session.get(User, user["id"])
        updated = profiles.upload_cv(None, stored, SqlAlchemyUnitOfWork(session), nlp=nlp, resumes=Row(extract=lambda *_: ("sample.pdf", "React y JavaScript")))
        assert updated.experience == TEXT and updated.summary_mode == "custom" and updated.experiences


def test_local_generation_is_a_private_preview_and_accepts_unsaved_facts(client):
    _, headers = register(client, "summary-generation", profession="Analista de datos", skills=["SQL"])
    before = client.get("/api/v1/profiles/me", headers=headers).json()
    observed = []
    class Writer:
        def generate_summary(self, facts, *, tone):
            observed.append((facts, tone))
            return {"summary": TEXT}
    client.app.dependency_overrides[get_career_writer] = lambda: Writer()
    payload = {"tone": "concise", "profile": {"profession": "Desarrollador frontend", "skills": ["React", "JavaScript"], "experiences": [{"role": "Desarrollador", "description": TEXT}], "experience": ""}}
    response = client.post("/api/v1/profiles/me/summary/generate", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["text"] == TEXT and response.json()["method"] == "local-ai"
    assert observed[0][0]["profesion"] == "Desarrollador frontend" and observed[0][1] == "concise"
    assert client.get("/api/v1/profiles/me", headers=headers).json() == before
    _, company = company_account(client, "summary-company")
    assert client.post("/api/v1/profiles/me/summary/generate", headers=company, json=payload).status_code == 403
    assert client.post("/api/v1/profiles/me/summary/generate", json=payload).status_code == 401
    payload["user_id"] = 999
    assert client.post("/api/v1/profiles/me/summary/generate", headers=headers, json=payload).status_code == 422


def test_generation_uses_saved_profile_and_preserves_it_when_generator_is_unavailable(client):
    _, headers = register(client, "summary-unavailable", profession="Desarrollador frontend", skills=["React", "JavaScript"])
    before = client.get("/api/v1/profiles/me", headers=headers).json()
    client.app.dependency_overrides[get_career_writer] = lambda: None
    response = client.post("/api/v1/profiles/me/summary/generate", headers=headers, json={})
    assert response.status_code == 503
    assert client.get("/api/v1/profiles/me", headers=headers).json() == before
    observed = []
    class Writer:
        def generate_summary(self, facts, *, tone):
            observed.append(facts)
            return {"summary": "Soy desarrollador frontend con conocimientos de React y JavaScript. Mi perfil se orienta al desarrollo frontend con estas tecnologías."}
    client.app.dependency_overrides[get_career_writer] = lambda: Writer()
    response = client.post("/api/v1/profiles/me/summary/generate", headers=headers, json={})
    assert response.status_code == 200, response.text
    assert observed[0]["profesion"] == before["profession"]


@pytest.mark.parametrize("unsupported", [
    "Soy experto en React y desarrollo interfaces web con JavaScript para el equipo de desarrollo.",
    "Soy desarrollador frontend especializado en React y JavaScript para el equipo de desarrollo.",
    "Soy desarrollador frontend con React y JavaScript, pero no tengo experiencia en interfaces web.",
    "Desarrollo interfaces web con React y JavaScript y he trabajado en 30 proyectos profesionales.",
    "Desarrollo interfaces web con React y JavaScript y despliego aplicaciones con Kubernetes y AWS.",
])
def test_unsupported_skills_achievements_and_numbers_are_rejected(unsupported):
    from app.infrastructure.nlp.text_processor import text_processor
    facts = summary_facts(Row(profession="Desarrollador frontend", skills=["React", "JavaScript"], experience=TEXT))
    with pytest.raises(ValueError):
        validate_summary({"summary": unsupported}, facts, extract_skills=text_processor.extract_skills)


def test_facts_are_bounded_include_recent_roles_and_keep_current_study_status():
    profile = Row(profession="Desarrollador", skills=["React"] * 100, experience="X" * 4000, experiences=[{"role": f"Cargo {year}", "description": "Y" * 3000, "start_year": str(year), "end_year": str(year + 1)} for year in range(2015, 2024)], educations=[{"degree": "Ingeniería", "end_year": "En curso"}])
    facts = summary_facts(profile)
    assert len(facts["habilidades"]) == 12 and len(facts["experiencias"]) == 4
    assert facts["experiencias"][0]["cargo"] == "Cargo 2023"
    assert len(facts["experiencias"][0]["funciones"]) == 450 and len(facts["resumen_actual"]) == 900
    assert facts["formacion"][0]["en_curso"] is True


def test_local_model_verb_typo_is_corrected_without_changing_personal_text():
    from app.infrastructure.nlp.text_processor import text_processor
    facts = summary_facts(Row(profession="Desarrollador frontend", skills=["React"], experience="Ejecuté pruebas funcionales y documenté incidencias en interfaces con React."))
    text = validate_summary({"summary": "Soy desarrollador frontend con habilidades en React. Ejecuó pruebas funcionales y documenté incidencias en interfaces web."}, facts, extract_skills=text_processor.extract_skills)
    assert "Ejecuté pruebas funcionales" in text and "Ejecuó" not in text
