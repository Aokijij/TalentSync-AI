# ruff: noqa: F811
from io import BytesIO

import pytest
from pypdf import PdfReader
from test_account_security import browser, csrf, login  # noqa: F401
from test_api_flows import client, register  # noqa: F401

from app.core.config import settings
from app.domain.services.learning_activities import activities_for, activity_key
from app.domain.services.learning_catalog import ASSESSMENTS
from app.infrastructure.database.models import User
from app.infrastructure.nlp.text_processor import text_processor


def test_optional_company_mfa_does_not_disable_existing_authenticators_or_admin_gate(browser, monkeypatch):
    monkeypatch.setattr(settings, "company_mfa_required", False)
    register(browser, "optional-company", "company", company_name="Empresa de prueba", nit="LOCAL-OPTIONAL")
    result = login(browser, "optional-company@example.com")
    assert result.json()["mfa_setup_required"] is False
    assert browser.get("/api/v1/companies/me").status_code == 200
    with browser.session_factory() as db:
        user = db.query(User).filter_by(email="optional-company@example.com").one()
        user.mfa_enabled = True
        db.commit()
    assert browser.get("/api/v1/companies/me").status_code == 403
    assert login(browser, "optional-company@example.com").json() == {"mfa_required": True}
    browser.cookies.clear()
    with browser.session_factory() as db:
        user = db.query(User).filter_by(email="optional-company@example.com").one()
        user.role = "admin"
        user.mfa_enabled = False
        db.commit()
    response = browser.post("/api/v1/auth/session/admin/login", json={"email": "optional-company@example.com", "password": "Test-password-2026!"})
    assert response.json()["mfa_setup_required"] is True
    assert browser.get("/api/v1/admin/stats").status_code == 403


def test_active_plan_limit_leave_ownership_version_and_rejoin(client):
    _, headers = register(client, "limited-plan")
    _, other = register(client, "other-plan")
    for area in ["sales", "finance", "logistics"]:
        assert client.put(f"/api/v1/learning/plans/practice-{area}-v1", headers=headers, json={}).status_code == 200
    endpoint = "/api/v1/learning/plans/practice-care-v1"
    assert client.put(endpoint, headers=headers, json={}).status_code == 409
    plan = client.get("/api/v1/learning/plans", headers=headers).json()[0]
    endpoint = f"/api/v1/learning/plans/{plan['resource']['id']}"
    assert client.delete(endpoint, headers=other, params={"version": plan["version"]}).status_code == 404
    assert client.delete(endpoint, headers=headers, params={"version": 0}).status_code == 409
    assert client.delete(endpoint, headers=headers, params={"version": plan["version"]}).status_code == 200
    assert client.put("/api/v1/learning/plans/practice-care-v1", headers=headers, json={}).status_code == 200
    assert len(client.get("/api/v1/learning/plans", headers=headers).json()) == 3


@pytest.mark.parametrize("area", ["general", "technology", "service", "sales", "administration", "finance", "logistics", "education", "design", "care"])
def test_interactive_laboratory_drafts_checks_and_publishes_scoped_evidence(client, area):
    _, headers = register(client, f"interactive-{area}", skills=[])
    resource = client.get(f"/api/v1/learning/catalog?area={area}", headers=headers).json()["resources"][0]
    assert all("answer" not in item and "feedback" not in item for item in resource["journey"]["activities"])
    endpoint = f"/api/v1/learning/plans/{resource['id']}"
    plan = client.put(endpoint, headers=headers, json={}).json()[0]
    answers = {item["id"]: item["answer"] for item in activities_for(activity_key(resource))}
    wrong = {**answers, "calculation": -999}
    draft = client.patch(endpoint + "/journey", headers=headers, json={"version": plan["version"], "activity_answers": wrong}).json()[0]
    assert not all(item["correct"] for item in draft["progress"]["activity_feedback"])
    payload = {"version": draft["version"], "activity_answers": wrong, "finish": True}
    assert client.patch(endpoint + "/journey", headers=headers, json=payload).status_code == 422
    payload["activity_answers"] = answers
    response = client.patch(endpoint + "/journey", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    assert response.json()[0]["progress"]["published"]
    evidence = client.get("/api/v1/matching/evidence", headers=headers).json()
    assert len(evidence) == 1 and not evidence[0]["verified"]
    assert client.get("/api/v1/profiles/me", headers=headers).json()["skills"] == []
    assert client.delete(endpoint, headers=headers, params={"version": response.json()[0]["version"]}).status_code == 200
    assert len(client.get("/api/v1/matching/evidence", headers=headers).json()) == 1


def test_mixed_assessment_invalid_data_feedback_and_targeted_resources(client):
    _, headers = register(client, "mixed-assessment")
    assessment = "finance-simulation-v1"
    bank = ASSESSMENTS[assessment]
    attempt = client.post(f"/api/v1/learning/assessments/{assessment}/start", headers=headers).json()
    answers = {item["id"]: item["answer"] for item in bank["questions"]}
    endpoint = f"/api/v1/learning/attempts/{attempt['id']}/submit"
    for invalid in [True, "NaN", "Infinity", [1, 1, 1], {"fake": 1}]:
        assert client.post(endpoint, headers=headers, json={"answers": {**answers, "calculation": invalid}}).status_code == 422
    answers["calculation"] = 0
    answers["sequence"] = [0, 1, 2, 3]
    result = client.post(endpoint, headers=headers, json={"answers": answers}).json()
    assert result["score"] == 60 and not result["passed"]
    assert len(result["feedback"]) == 5 and all(item["prompt"] and item["message"] for item in result["feedback"])
    assert any("conciliacion bancaria" in item["skills"] for item in result["improvement_resources"])


@pytest.mark.parametrize("resource_id", ["project-rest", "project-git", "project-security", "project-sql", "project-python", "project-microservices"])
def test_technology_projects_have_their_own_reviewable_laboratory(client, resource_id):
    _, headers = register(client, f"lab-{resource_id}")
    endpoint = f"/api/v1/learning/plans/{resource_id}"
    plan = client.put(endpoint, headers=headers, json={}).json()[0]
    answers = {item["id"]: item["answer"] for item in activities_for(resource_id)}
    result = client.patch(endpoint + "/journey", headers=headers, json={"version": plan["version"], "activity_answers": answers, "finish": True})
    assert result.status_code == 200, result.text
    assert result.json()[0]["progress"]["published"]


def test_passed_assessment_still_recommends_practice_for_one_mistake(client):
    _, headers = register(client, "passed-needs-practice")
    bank = ASSESSMENTS["finance-simulation-v1"]
    attempt = client.post("/api/v1/learning/assessments/finance-simulation-v1/start", headers=headers).json()
    answers = {item["id"]: item["answer"] for item in bank["questions"]}
    answers["calculation"] = 0
    result = client.post(f"/api/v1/learning/attempts/{attempt['id']}/submit", headers=headers, json={"answers": answers}).json()
    assert result["passed"] and result["score"] == 80
    assert result["improvement_resources"]
    saved = client.get("/api/v1/learning/passport", headers=headers).json()["assessments"][0]
    assert saved["feedback"] == result["feedback"] and saved["improvement_resources"]


def test_pdf_download_is_private_paginated_and_preserves_accents(client):
    user, headers = register(client, "pdf-download", profession="Diseñador gráfico", skills=["comunicación"])
    with client.session_factory() as db:
        profile = db.get(User, user["id"]).profile
        profile.experience = "Experiencia en comunicación y diseño. " * 160
        db.commit()
    response = client.get("/api/v1/profiles/me/export", headers=headers)
    assert response.status_code == 200 and response.headers["content-type"] == "application/pdf"
    pdf = PdfReader(BytesIO(response.content))
    assert len(pdf.pages) > 1
    assert "Diseñador gráfico" in "".join(page.extract_text() for page in pdf.pages)
    assert "no-store" in response.headers["cache-control"]
    assert client.get("/api/v1/profiles/me/export").status_code == 401


def test_resume_coordinate_source_recovers_duties_without_profile_or_technology_bleed():
    text = """EXPERIENCIA LABORAL
2019 - 2020 Empresa Uno
ANALISTA DE CALIDAD
2022 - 2023 Empresa Dos
ANALISTA DE INVENTARIO
PERFIL PROFESIONAL Estudiante con conocimientos en varias áreas.
TECNOLOGIAS PROYECTOS Empresa Tres
2019 - 2020
COORDINATE EXPERIENCE LAYOUT
EXPERIENCIA LABORAL
2019 - 2020
Empresa Uno
ANALISTA DE CALIDAD
Ejecución de pruebas funcionales y seguimiento de incidencias.
2022 - 2023
Empresa Dos
ANALISTA DE INVENTARIO
Gestión de existencias y análisis de movimientos.
PROYECTOS
Un proyecto independiente.
FORMACIÓN ACADÉMICA
Universidad de Prueba
Ingeniería de Sistemas
2020 - Presente
"""
    experience, education, _ = text_processor.extract_resume_items(text)
    rows = {item["company"]: item for item in experience}
    assert "pruebas funcionales" in rows["Empresa Uno"]["description"]
    assert "Gestión de existencias" in rows["Empresa Dos"]["description"]
    assert all("Estudiante" not in item["description"] for item in experience)
    assert all("TECNOLOGIAS" not in item["degree"] for item in education)
