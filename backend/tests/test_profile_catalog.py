# ruff: noqa: F811
import pytest
from test_api_flows import client, register  # noqa: F401


@pytest.mark.parametrize("profession,area,expected,excluded", [
    ("Docente de primaria", "education", "education-foundations-v1", "python-foundations-v1"),
    ("Auxiliar contable", "finance", "finance-foundations-v1", "sql-foundations-v1"),
    ("Asesor comercial", "sales", "sales-foundations-v1", "python-foundations-v1"),
    ("Auxiliar de enfermería", "care", "care-foundations-v1", "git-foundations-v1"),
    ("Coordinador de logística", "logistics", "logistics-foundations-v1", "python-foundations-v1"),
    ("Diseñador gráfico", "design", "design-foundations-v1", "sql-foundations-v1"),
    ("Analista de sistemas", "technology", "python-foundations-v1", "sales-foundations-v1"),
])
def test_catalog_defaults_to_relevant_area_and_allows_explicit_exploration(client, profession, area, expected, excluded):
    _, headers = register(client, "catalog-profile", profession=profession, skills=[])
    data = client.get("/api/v1/learning/catalog", headers=headers).json()
    ids = {row["id"] for row in data["assessments"]}
    assert area in data["recommended_areas"] and expected in ids and excluded not in ids
    assert "general-foundations-v1" in ids
    assert all(row["category"] in {area, "general"} for row in data["resources"])
    all_areas = client.get("/api/v1/learning/catalog?area=all", headers=headers).json()
    assert excluded in {row["id"] for row in all_areas["assessments"]}
    assert client.get("/api/v1/learning/catalog?area=unknown", headers=headers).status_code == 422


def test_empty_profile_gets_general_practice_not_software_assumptions(client):
    _, headers = register(client, "empty-catalog", profession="", skills=[])
    data = client.get("/api/v1/learning/catalog", headers=headers).json()
    assert data["recommended_areas"] == ["general"]
    assert {row["id"] for row in data["assessments"]} == {"general-foundations-v1"}


