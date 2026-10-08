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


def test_quality_uses_local_reference_and_scenarios_preserve_category(client):
    _, company = company_account(client)
    job = client.post("/api/v1/jobs", headers=company, json={"title": "Junior Python", "description": "Desarrolla aplicaciones para el equipo", "requirements": "Experiencia de 7 años; solo hombres", "sector": "Tecnologia y software"}).json()
    report = client.get(f"/api/v1/hiring/quality/{job['id']}", headers=company)
    assert report.status_code == 200
    assert {row["code"] for row in report.json()["issues"]} >= {"level_conflict", "salary_missing", "personal_restrictions"}
    assert report.json()["salary_reference"]["median"] is None
    scenario = {"id": "scenario-delivery", "category": "work_scenario", "prompt": "Tu entrega se retrasa. ¿Qué haces?", "type": "choice", "options": ["Aviso pronto y propongo alternativas", "Espero hasta la fecha final"], "option_scores": {}}
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=company, json={"application_questions": [scenario]}).status_code == 200
    assert client.get(f"/api/v1/jobs/{job['id']}").json()["application_questions"][0]["category"] == "work_scenario"
