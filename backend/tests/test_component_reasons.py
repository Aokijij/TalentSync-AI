# ruff: noqa: F811
from test_api_flows import client, company_account, register  # noqa: F401
from test_offer_quality import complete_offer


def test_company_gets_component_reasons_without_identity_or_an_extra_match_version(client):
    _, owner = company_account(client, "component-reasons")
    payload = complete_offer()
    payload.update(required_education_level="university", required_study_fields=["Sistemas"], languages=[{"name": "inglés", "level": "B1"}])
    saved = client.post("/api/v1/jobs", headers=owner, json=payload)
    assert saved.status_code == 201
    job = saved.json()
    candidate, headers = register(client, "component-reasons-person", profession="Analista de datos", skills=["sql"])
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    profile["languages"] = [{"name": "inglés", "level": "B2"}]
    client.put("/api/v1/profiles/me", headers=headers, json=profile).raise_for_status()
    client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"]}).raise_for_status()
    response = client.get(f"/api/v1/recommendations/jobs/{job['id']}/candidates/{candidate['id']}/explanation", headers=owner)
    assert response.status_code == 200, response.text
    components = {row["key"]: row for row in response.json()["match_details"]["components"]}
    assert all(row["explanations"] for row in components.values())
    assert "promedio ponderado" in components["skills"]["explanations"][0]
    assert any("solicitado B1 · registrado B2" in line for line in components["languages"]["explanations"])
    text = str([row["explanations"] for row in components.values()])
    assert candidate["email"] not in text and candidate["name"] not in text
    assert response.json()["match_details"]["version"] == "contextual-match-v11"
