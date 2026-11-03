# ruff: noqa: F811
from test_api_flows import client, register  # noqa: F401
from test_ecosystem import administrator


def test_catalog_uses_work_functions_and_explains_relevance_without_altering_profile(client):
    admin = administrator(client)
    response = client.post("/api/v1/admin/learning/resources", headers=admin, json={"title": "Gestión de proyectos e indicadores", "provider": "Prueba de contexto", "instructions": "Planifica entregas, cronogramas, presupuestos y riesgos de un proyecto.", "url": "https://education.example.com/projects", "skills": ["gestión de proyectos", "planificación", "gestión de riesgos"], "hours": 4, "category": "administration"})
    assert response.status_code == 201
    course_id = next(row["id"] for row in response.json() if row["provider"] == "Prueba de contexto")
    _, candidate = register(client, "project-context-person", profession="Profesional", skills=[])
    profile = client.get("/api/v1/profiles/me", headers=candidate).json()
    profile["experiences"] = [{"company": "Empresa", "role": "Analista de Proyectos", "description": "Planeación y seguimiento de proyectos, control de riesgos y ejecución presupuestal.", "start_date": "2025-07", "end_date": "2025-11"}]
    assert client.put("/api/v1/profiles/me", headers=candidate, json=profile).status_code == 200
    before = client.get("/api/v1/profiles/me", headers=candidate).json()
    catalog = client.get("/api/v1/learning/catalog", headers=candidate).json()
    assert "administration" in catalog["recommended_areas"]
    resource = next(row for row in catalog["resources"] if row["id"] == course_id)
    assert resource["relevance"]["kind"] == "context"
    assert "proyectos" in " ".join(resource["relevance"]["reasons"])
    assert catalog["resources"][0]["relevance"]["score"] > 0
    assert client.get("/api/v1/profiles/me", headers=candidate).json() == before
    assert any(row["id"] == course_id for row in client.get("/api/v1/learning/catalog?area=all", headers=candidate).json()["resources"])
