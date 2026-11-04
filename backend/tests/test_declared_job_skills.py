# ruff: noqa: F811
from test_api_flows import client, company_account  # noqa: F401


def test_selected_requirements_are_the_same_skills_shown_after_create_and_reedit(client):
    _, company = company_account(client, "declared-skills")
    response = client.post("/api/v1/jobs", headers=company, json={
        "title": "Diseño de producto", "description": "Revisar una interfaz que consume una API de Python y SQL.",
        "requirements": "Comunicar decisiones y preparar prototipos accesibles.", "sector": "Tecnologia y software", "status": "draft",
        "skill_requirements": [{"skill": "Figma"}, {"skill": "accesibilidad"}, {"skill": "comunicación"}],
    })
    assert response.status_code == 201, response.text
    job = response.json()
    assert job["skills"] == ["figma", "accesibilidad", "comunicacion"]
    endpoint = f"/api/v1/jobs/{job['id']}"
    changed = client.patch(endpoint, headers=company, json={"skill_requirements": [{"skill": "React"}, {"skill": "TypeScript"}]}).json()
    assert changed["skills"] == ["react", "typescript"]
    changed = client.patch(endpoint, headers=company, json={"description": "Integrar el diseño con una interfaz web que consulta datos desde Python y SQL."}).json()
    assert changed["skills"] == ["react", "typescript"]
    changed = client.patch(endpoint, headers=company, json={"skill_requirements": []}).json()
    assert changed["skills"] == []


def test_legacy_vacancies_without_selected_requirements_keep_text_extraction(client):
    _, company = company_account(client, "inferred-skills")
    response = client.post("/api/v1/jobs", headers=company, json={
        "title": "Desarrollo de API Python", "description": "Desarrollar servicios con Python y consultar bases de datos SQL.",
        "requirements": "Conocimientos de Python, SQL y Git.", "sector": "Tecnologia y software", "status": "draft",
    })
    assert response.status_code == 201, response.text
    assert "python" in response.json()["skills"] and "sql" in response.json()["skills"]
