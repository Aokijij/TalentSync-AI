# ruff: noqa: F811
import pytest
from test_api_flows import client, register  # noqa: F401


@pytest.mark.parametrize("profession,area,expected,excluded", [
    ("Docente de primaria", "education", "education-beginner-v2", "python-beginner-v2"),
    ("Auxiliar contable", "finance", "finance-beginner-v2", "sql-beginner-v2"),
    ("Asesor comercial", "sales", "sales-beginner-v2", "python-beginner-v2"),
    ("Auxiliar de enfermería", "care", "care-beginner-v2", "python-beginner-v2"),
    ("Coordinador de logística", "logistics", "inventory-beginner-v2", "python-beginner-v2"),
    ("Diseñador gráfico", "design", "design-beginner-v2", "sql-beginner-v2"),
    ("Analista de sistemas", "technology", "python-beginner-v2", "sales-beginner-v2"),
])
def test_catalog_defaults_to_relevant_area_and_allows_explicit_exploration(client, profession, area, expected, excluded):
    _, headers = register(client, "catalog-profile", profession=profession, skills=[])
    data = client.get("/api/v1/learning/catalog", headers=headers).json()
    ids = {row["id"] for row in data["assessments"]}
    assert area in data["recommended_areas"] and expected in ids and excluded not in ids
    assert "communication-beginner-v2" in ids
    assert all(row["category"] in {area, "general"} for row in data["resources"])
    all_areas = client.get("/api/v1/learning/catalog?area=all", headers=headers).json()
    assert excluded in {row["id"] for row in all_areas["assessments"]}
    assert client.get("/api/v1/learning/catalog?area=unknown", headers=headers).status_code == 422


def test_empty_profile_gets_general_practice_not_software_assumptions(client):
    _, headers = register(client, "empty-catalog", profession="", skills=[])
    data = client.get("/api/v1/learning/catalog", headers=headers).json()
    assert data["recommended_areas"] == ["general"]
    assert "communication-beginner-v2" in {row["id"] for row in data["assessments"]}
    assert all(row["category"] == "general" for row in data["assessments"])
    assert all("simulation-v1" not in row["id"] for row in data["assessments"])


def test_transferable_communication_does_not_route_sales_profile_to_design(client):
    _, headers = register(client, "sales-communication", profession="Asesor comercial", skills=["Comunicación"])
    data = client.get("/api/v1/learning/catalog", headers=headers).json()
    assert data["recommended_areas"] == ["sales"]


