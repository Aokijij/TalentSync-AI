# ruff: noqa: F811
from test_api_flows import client, company_account, register  # noqa: F401


def test_blind_hiring_hides_identity_and_text_until_interview(client):
    _, company = company_account(client)
    job = client.post("/api/v1/jobs", headers=company, json={"title": "Desarrollador Python", "description": "Desarrolla APIs con Python y SQL", "requirements": "Conocimiento de Python y SQL", "sector": "Tecnologia y software", "application_questions": [{"id": "intro", "prompt": "Cuéntanos un proyecto", "type": "open"}]}).json()
    assert job["blind_hiring"] is True
    candidate, headers = register(client, "private-person", skills=["Python", "SQL"], profession="Desarrollador Python")
    application = client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"], "screening_answers": [{"question_id": "intro", "answer": "Me llamo PRIVATE-NAME y estudié en PRIVATE-UNIVERSITY"}]}).json()
    ranking = client.get(f"/api/v1/recommendations/jobs/{job['id']}/candidates", headers=company)
    assert ranking.status_code == 200
    assert candidate["name"] not in ranking.text
    assert "PRIVATE-NAME" not in ranking.text
    assert ranking.json()[0]["identity_hidden"] is True
    response = client.get(f"/api/v1/applications/jobs/{job['id']}", headers=company)
    assert "PRIVATE-NAME" not in response.text
    assert candidate["name"] not in response.text
    assert client.get(f"/api/v1/profiles/candidates/{candidate['id']}", headers=company).status_code == 403
    assert client.get(f"/api/v1/profiles/{candidate['id']}/photo", headers=company).status_code == 403
    notifications = client.get("/api/v1/notifications", headers=company)
    assert candidate["name"] not in notifications.text
    assert client.put(f"/api/v1/applications/{application['id']}/status", headers=company, json={"status": "technical_interview"}).status_code == 200
    ranking = client.get(f"/api/v1/recommendations/jobs/{job['id']}/candidates", headers=company).json()
    assert ranking[0]["identity_hidden"] is False
    assert ranking[0]["name"] == candidate["name"]
    assert client.get(f"/api/v1/profiles/candidates/{candidate['id']}", headers=company).status_code == 200


def test_quality_uses_local_reference_and_retires_new_scenarios(client):
    _, company = company_account(client)
    job = client.post("/api/v1/jobs", headers=company, json={"title": "Junior Python", "description": "Desarrolla aplicaciones para el equipo", "requirements": "Experiencia de 7 años; solo hombres", "sector": "Tecnologia y software"}).json()
    report = client.get(f"/api/v1/hiring/quality/{job['id']}", headers=company)
    assert report.status_code == 200
    assert {row["code"] for row in report.json()["issues"]} >= {"level_conflict", "salary_missing", "personal_restrictions"}
    assert report.json()["salary_reference"]["median"] is None
    scenario = {"id": "scenario-delivery", "category": "work_scenario", "prompt": "Tu entrega se retrasa. ¿Qué haces?", "type": "choice", "options": ["Aviso pronto y propongo alternativas", "Espero hasta la fecha final"], "option_scores": {}}
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=company, json={"application_questions": [scenario]}).status_code == 422
    from app.infrastructure.database.models import Job
    with client.session_factory() as db:
        legacy = db.get(Job, job["id"])
        legacy.application_questions = [scenario]
        db.commit()
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=company, json={"application_questions": [scenario]}).status_code == 200
    assert client.get(f"/api/v1/jobs/{job['id']}").json()["application_questions"][0]["category"] == "work_scenario"
    changed = {**scenario, "prompt": "Otra situación de trabajo"}
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=company, json={"application_questions": [changed]}).status_code == 422
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=company, json={"application_questions": []}).status_code == 200


def test_quality_checklist_changes_after_saving_actionable_corrections(client):
    _, headers = company_account(client)
    response = client.post("/api/v1/jobs", headers=headers, json={"title": "Asesor comercial", "description": "Atiende solicitudes", "requirements": "Conocimiento comercial", "sector": "Ventas y comercio"})
    assert response.status_code == 201
    job = response.json()
    endpoint = f"/api/v1/hiring/quality/{job['id']}"
    before = client.get(endpoint, headers=headers).json()
    assert any(not row["passed"] for row in before["checks"])
    patch = {"description": "Atiende solicitudes de clientes, documenta necesidades y coordina propuestas comerciales con el equipo. Realiza seguimiento de acuerdos y registra resultados verificables.", "requirements": "Experiencia en comunicación comercial, seguimiento de oportunidades y venta consultiva para entender las necesidades de cada cliente.", "salary": 2500000, "modality": "onsite", "location": "Bogotá", "response_days": 7, "skill_requirements": [{"skill": "ventas", "essential": True, "weight": 3}]}
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=headers, json=patch).status_code == 200
    after = client.get(endpoint, headers=headers).json()
    assert after["completeness"] > before["completeness"] and after["completeness"] == 100
    assert all(row["passed"] for row in after["checks"])
    _, candidate = register(client, "sales-quality-match", profession="Asesor comercial", skills=["ventas"])
    match = client.post(f"/api/v1/jobs/{job['id']}/match", headers=candidate)
    assert match.status_code == 200
    assert match.json()["skill_match_percentage"] == 100
    assert "Cumples todas las habilidades requeridas" in match.json()["reasons"]
