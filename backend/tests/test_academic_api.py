# ruff: noqa: F811
from test_api_flows import client, company_account, register  # noqa: F401
from test_offer_quality import complete_offer

from app.domain.services.professions import infer_study_fields


def test_policy_is_saved_validated_and_refreshes_academic_explanations(client):
    _, company = company_account(client, "academic-owner")
    payload = complete_offer()
    payload.update(
        required_education_level="university",
        required_study_fields=["Ingeniería de Sistemas"],
    )
    response = client.post("/api/v1/jobs", headers=company, json=payload)
    assert response.status_code == 201, response.text
    job = response.json()
    _, candidate = register(
        client,
        "academic-person",
        skills=["sql", "excel"],
        profession="Analista de datos",
    )
    profile = client.get("/api/v1/profiles/me", headers=candidate).json()
    profile["educations"] = [
        {"degree": "Ingeniería Informática", "level": "university", "is_current": False}
    ]
    assert (
        client.put("/api/v1/profiles/me", headers=candidate, json=profile).status_code
        == 200
    )
    endpoint = f"/api/v1/matching/jobs/{job['id']}"
    initial = client.get(endpoint, headers=candidate).json()
    assert initial["education_requirement"]["status"] == "partial"
    assert initial["education_requirement"]["score"] == 79
    details = {**job["quality_details"], "education_field_policy": "exact"}
    response = client.patch(
        f"/api/v1/jobs/{job['id']}", headers=company, json={"quality_details": details}
    )
    assert response.status_code == 200, response.text
    assert response.json()["quality_details"]["education_field_policy"] == "exact"
    exact = client.get(endpoint, headers=candidate).json()
    assert exact["input_version"] != initial["input_version"]
    assert exact["education_requirement"]["status"] == "not_met"
    assert exact["education_requirement"]["score"] == 0
    assert (
        client.patch(
            f"/api/v1/jobs/{job['id']}",
            headers=company,
            json={"quality_details": {**details, "education_field_policy": "invented"}},
        ).status_code
        == 422
    )
    profile["educations"][0]["degree"] = "Programa académico no catalogado"
    assert (
        client.put("/api/v1/profiles/me", headers=candidate, json=profile).status_code
        == 200
    )
    pending = client.get(endpoint, headers=candidate).json()
    assert pending["education_requirement"]["status"] == "review"
    assert pending["education_requirement"]["score"] is None
    assert not any(row["key"] == "education" for row in pending["components"])
    assert (
        client.post(
            "/api/v1/applications", headers=candidate, json={"job_id": job["id"]}
        ).status_code
        == 201
    )
    response = client.get(
        f"/api/v1/recommendations/jobs/{job['id']}/candidates/{profile['user_id']}/explanation",
        headers=company,
    )
    assert response.status_code == 200, response.text
    assert (
        response.json()["match_details"]["education_requirement"]["status"] == "review"
    )


def test_extracted_study_fields_do_not_expand_accounting_to_all_finance():
    assert infer_study_fields("Profesional en Contaduría Pública") == [
        "Contaduría Pública"
    ]
    assert infer_study_fields("Contabilidad y Finanzas") == ["Contabilidad y Finanzas"]
    assert infer_study_fields("Contaduría Pública o Economía") == [
        "Contaduría Pública",
        "Economía",
    ]


def test_company_can_search_catalog_variants_without_restricting_free_text(client):
    _, company = company_account(client, "academic-catalog-owner")
    response = client.get("/api/v1/hiring/education/catalog", headers=company, params={"query": "contabilidad"})
    assert response.status_code == 200
    assert response.json()["version"] == "academic-fields-v3"
    assert any(row["label"] == "Contaduría Pública" for row in response.json()["items"])
    assert client.get("/api/v1/hiring/education/catalog", params={"query": "Contaduría"}).status_code == 401
