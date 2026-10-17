# ruff: noqa: F811
from test_api_flows import client, company_account, register  # noqa: F401


def test_legacy_pipeline_uses_default_stages_but_custom_pipeline_stays_scoped(client):
    from app.infrastructure.database.models import Job

    _, company = company_account(client, "legacy-pipeline")
    job = client.post("/api/v1/jobs", headers=company, json={"title": "Analista", "description": "Revisa datos de inventarios", "requirements": "Excel e inventarios", "sector": "Logistica y transporte"}).json()
    _, candidate = register(client, "legacy-pipeline-candidate")
    application = client.post("/api/v1/applications", headers=candidate, json={"job_id": job["id"]}).json()
    with client.session_factory() as db:
        db.get(Job, job["id"]).pipeline_stages = None
        db.commit()
    endpoint = f"/api/v1/applications/{application['id']}/status"
    response = client.put(endpoint, headers=company, json={"pipeline_stage": "interview", "expected_version": application["version"]})
    assert response.status_code == 200, response.text
    assert response.json()["pipeline_stage_title"] == "Entrevista"
    assert response.json()["identity_hidden"] is False
    assert response.json()["version"] > application["version"]
    assert client.put(endpoint, headers=company, json={"pipeline_stage": "reviewing", "expected_version": application["version"]}).status_code == 409
    assert client.get(f"/api/v1/applications/jobs/{job['id']}", headers=company).json()[0]["pipeline_stage"] == "interview"
    custom = [{"id": "initial", "title": "Inicial"}, {"id": "assessment", "title": "Evaluación"}]
    custom_job = client.post("/api/v1/jobs", headers=company, json={"title": "Analista especializado", "description": "Revisa datos de inventarios", "requirements": "Excel e inventarios", "sector": "Logistica y transporte", "pipeline_stages": custom}).json()
    custom_application = client.post("/api/v1/applications", headers=candidate, json={"job_id": custom_job["id"]}).json()
    endpoint = f"/api/v1/applications/{custom_application['id']}/status"
    assert client.put(endpoint, headers=company, json={"pipeline_stage": "interview"}).status_code == 422
    assert client.put(endpoint, headers=company, json={"pipeline_stage": "assessment"}).status_code == 200



def test_identity_is_hidden_until_submission_and_consent_is_vacancy_scoped(client):
    _, company = company_account(client)
    _, stranger = company_account(client, "private-outsider")
    payload = {"title": "Desarrollador Python", "description": "Desarrolla APIs con Python y SQL", "requirements": "Conocimiento de Python y SQL", "sector": "Tecnologia y software", "application_questions": [{"id": "intro", "prompt": "Cuéntanos un proyecto", "type": "open"}]}
    job = client.post("/api/v1/jobs", headers=company, json=payload).json()
    other_job = client.post("/api/v1/jobs", headers=stranger, json={**payload, "blind_hiring": False}).json()
    sibling = client.post("/api/v1/jobs", headers=company, json={**payload, "blind_hiring": False}).json()
    candidate, headers = register(client, "private-person", skills=["Python", "SQL"], profession="Desarrollador Python")
    ranking_url = f"/api/v1/recommendations/jobs/{job['id']}/candidates"
    profile_url = f"/api/v1/profiles/candidates/{candidate['id']}"
    photo_url = f"/api/v1/profiles/{candidate['id']}/photo"
    ranking = client.get(ranking_url, headers=company)
    assert ranking.status_code == 200 and ranking.json()[0]["identity_hidden"] is True
    assert candidate["name"] not in ranking.text
    assert client.get(ranking_url + "-page", headers=company, params={"query": candidate["name"], "minimum_match": 0}).json()["items"] == []
    assert client.post(f"/api/v1/recommendations/jobs/{job['id']}/candidates/{candidate['id']}/invite", headers=company).status_code == 200
    assert client.get(ranking_url, headers=company).json()[0]["identity_hidden"] is True
    assert client.get(profile_url, headers=company).status_code == 403
    assert client.get(profile_url + f"?job_id={job['id']}", headers=company).status_code == 403
    assert client.get(photo_url, headers=company).status_code == 403
    submission = client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"], "screening_answers": [{"question_id": "intro", "answer": "Me llamo PRIVATE-NAME y estudié en PRIVATE-UNIVERSITY"}]})
    assert submission.status_code == 201
    ranking = client.get(ranking_url, headers=company).json()
    assert ranking[0]["identity_hidden"] is False and ranking[0]["name"] == candidate["name"]
    applications = client.get(f"/api/v1/applications/jobs/{job['id']}", headers=company)
    assert candidate["name"] in applications.text and "PRIVATE-NAME" in applications.text
    assert candidate["name"] in client.get("/api/v1/notifications", headers=company).text
    assert client.get(profile_url, headers=company).status_code == 200
    assert client.get(photo_url, headers=company).status_code == 404  # Authorized, but no photo uploaded.
    # Applying to one vacancy cannot reveal identity to other companies or unrelated recommendations.
    for owner, target in [(stranger, other_job), (company, sibling)]:
        ranking = client.get(f"/api/v1/recommendations/jobs/{target['id']}/candidates", headers=owner)
        assert ranking.json()[0]["identity_hidden"] is True and candidate["name"] not in ranking.text
        assert client.get(profile_url + f"?job_id={target['id']}", headers=owner).status_code == 403
    assert client.get(profile_url, headers=stranger).status_code == 403


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
    assert after["completeness"] > before["completeness"]
    assert after["can_publish"] is False
    assert any(row["key"] == "contract_type" for row in after["blockers"])
    _, candidate = register(client, "sales-quality-match", profession="Asesor comercial", skills=["ventas"])
    match = client.post(f"/api/v1/jobs/{job['id']}/match", headers=candidate)
    assert match.status_code == 200
    assert match.json()["skill_match_percentage"] == 100
    assert "Cumples todas las habilidades requeridas" in match.json()["reasons"]


def test_submitted_profile_is_visible_only_to_the_authorized_company(client):
    from app.infrastructure.database.models import User

    _, company = company_account(client, "anonymous-owner")
    _, other_company = company_account(client, "anonymous-outsider")
    job = client.post("/api/v1/jobs", headers=company, json={"title": "Analista de inventarios", "description": "Revisa inventarios y controla movimientos", "requirements": "Excel y control de inventarios", "sector": "Logistica y transporte"}).json()
    candidate, headers = register(client, "PRIVATE-PERSON", profession="Analista de inventarios", skills=["excel", "inventarios"])
    application = client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"]}).json()
    with client.session_factory() as db:
        profile = db.get(User, candidate["id"]).profile
        profile.phone = "PRIVATE-PHONE"
        profile.cv_text = "PRIVATE-CV"
        profile.cv_filename = "PRIVATE-FILENAME"
        profile.photo_filename = "PRIVATE-PHOTO"
        profile.experience = "PRIVATE-SUMMARY"
        profile.experiences = [{"role": "Analista", "company": "PRIVATE-EMPLOYER", "description": "PRIVATE-DESCRIPTION", "start_year": "2022", "end_year": "2026"}]
        profile.educations = [{"degree": "Tecnología logística", "institution": "PRIVATE-SCHOOL", "start_year": "2018", "end_year": "2021"}]
        db.commit()
    endpoint = f"/api/v1/profiles/candidates/{candidate['id']}?job_id={job['id']}"
    response = client.get(endpoint, headers=company)
    assert response.status_code == 200, response.text
    assert response.json()["identity_hidden"] is False
    assert response.json()["skills"] == ["excel", "inventarios"]
    assert response.json()["experiences"][0]["role"] == "Analista"
    assert "PRIVATE-PHONE" in response.text and "PRIVATE-EMPLOYER" in response.text
    assert client.get(endpoint, headers=other_company).status_code == 403
    assert client.get(endpoint.replace(f"job_id={job['id']}", "job_id=99999"), headers=company).status_code == 403
    assert client.get(f"/api/v1/profiles/candidates/{candidate['id']}", headers=company).status_code == 200
    # Legacy settings cannot re-hide an already submitted profile.
    visible_job = client.post("/api/v1/jobs", headers=company, json={"title": "Analista visible", "description": "Revisa inventarios y controla movimientos", "requirements": "Excel y control de inventarios", "sector": "Logistica y transporte", "blind_hiring": False}).json()
    client.post("/api/v1/applications", headers=headers, json={"job_id": visible_job["id"]})
    assert client.get(endpoint, headers=company).json()["identity_hidden"] is False
    assert client.put(f"/api/v1/applications/{application['id']}/status", headers=company, json={"status": "technical_interview"}).status_code == 200
    assert client.get(endpoint, headers=company).json()["name"] == candidate["name"]
