# ruff: noqa: F811
from io import BytesIO

import pytest
from pypdf import PdfReader
from test_api_flows import client, company_account, register  # noqa: F401
from test_offer_quality import complete_offer


def save(client, candidate, **changes):
    profile = client.get("/api/v1/profiles/me", headers=candidate).json()
    result = client.put(
        "/api/v1/profiles/me", headers=candidate, json={**profile, **changes}
    )
    assert result.status_code == 200, result.text
    return result.json()


def test_profile_credentials_are_saved_preserved_for_old_clients_and_private(client):
    person, candidate = register(client, "credential-person")
    _, company = company_account(client, "credential-company")
    profile = save(
        client,
        candidate,
        driving_licenses=[
            {"category": "B1", "status": "valid", "expires_on": "2099-12-31"}
        ],
        professional_cards=[
            {
                "profession": "Ingeniería civil",
                "issuer": "Consejo",
                "number": "PRIVATE-CARD",
                "status": "valid",
            }
        ],
    )
    assert profile["driving_licenses"] == [{"category": "B1"}]
    assert "expires_on" not in profile["professional_cards"][0] and "status" not in profile["professional_cards"][0]
    legacy = {
        key: value
        for key, value in profile.items()
        if key not in {"driving_licenses", "professional_cards"}
    }
    assert (
        client.put("/api/v1/profiles/me", headers=candidate, json=legacy).status_code
        == 200
    )
    assert (
        client.get("/api/v1/profiles/me", headers=candidate).json()[
            "professional_cards"
        ][0]["number"]
        == "PRIVATE-CARD"
    )
    assert (
        client.get(
            f"/api/v1/profiles/candidates/{person['id']}", headers=company
        ).status_code
        == 403
    )
    assert save(client, candidate, professional_cards=[])["professional_cards"] == []


def test_job_documents_are_public_compared_and_invalidate_cached_explanations(client):
    _, company = company_account(client, "documents-company")
    _, outsider = company_account(client, "documents-outsider")
    person, candidate = register(client, "documents-candidate", skills=["sql", "excel"])
    # Establish the automatic summary before comparing document-only edits.
    save(client, candidate)
    payload = complete_offer()
    payload["quality_details"]["credential_requirements"] = {
        "driving_categories": ["B1", "C1"],
        "professional_cards": ["Ingeniería civil"],
    }
    response = client.post("/api/v1/jobs", headers=company, json=payload)
    assert response.status_code == 201, response.text
    job = response.json()
    assert client.get(f"/api/v1/jobs/{job['id']}").json()["quality_details"][
        "credential_requirements"
    ]["professional_cards"] == ["Ingeniería civil"]
    endpoint = f"/api/v1/matching/jobs/{job['id']}"
    initial = client.get(endpoint, headers=candidate).json()
    assert initial["credential_requirements"]["status"] == "not_met"
    save(
        client,
        candidate,
        driving_licenses=[
            {"category": "C1", "status": "valid", "expires_on": "2099-01-01"}
        ],
        professional_cards=[
            {
                "profession": "Ingeniero civil",
                "number": "PRIVATE-CARD",
                "status": "valid",
            }
        ],
    )
    declared = client.get(endpoint, headers=candidate).json()
    assert declared["credential_requirements"]["status"] == "recorded"
    assert initial["input_version"] != declared["input_version"]
    assert (
        initial["overall_score"] == declared["overall_score"]
    )  # Documentary checks never fabricate skill points.
    assert "PRIVATE-CARD" not in str(declared)
    assert (
        client.post(
            "/api/v1/applications", headers=candidate, json={"job_id": job["id"]}
        ).status_code
        == 201
    )
    ranking = client.get(
        f"/api/v1/recommendations/jobs/{job['id']}/candidates", headers=company
    )
    assert ranking.status_code == 200
    assert "PRIVATE-CARD" not in ranking.text
    assert ranking.json()[0]["credential_status"] == "recorded"
    profile_endpoint = f"/api/v1/profiles/candidates/{person['id']}?job_id={job['id']}"
    assert "PRIVATE-CARD" in client.get(profile_endpoint, headers=company).text
    assert client.get(profile_endpoint, headers=outsider).status_code == 403


@pytest.mark.parametrize("style", ["classic", "modern", "minimal"])
def test_resume_export_includes_credentials_only_when_selected(client, style):
    _, candidate = register(client, "credential-export-" + style)
    save(
        client,
        candidate,
        driving_licenses=[
            {"category": "B1", "status": "valid", "expires_on": "2099-01-01"}
        ],
        professional_cards=[
            {"profession": "Ingeniería civil", "number": "CARD-123", "status": "valid"}
        ],
    )
    response = client.post(
        "/api/v1/profiles/me/export",
        headers=candidate,
        json={
            "sections": ["driving_licenses", "professional_cards"],
            "include_photo": False,
            "profile": {"resume_style": style},
        },
    )
    assert response.status_code == 200, response.text
    text = " ".join(
        page.extract_text() for page in PdfReader(BytesIO(response.content)).pages
    )
    assert "LICENCIAS DE CONDUCCIÓN" in text and "B1" in text and "CARD-123" in text
    response = client.post(
        "/api/v1/profiles/me/export",
        headers=candidate,
        json={"sections": ["summary"], "include_photo": False},
    )
    assert "CARD-123" not in " ".join(
        page.extract_text() for page in PdfReader(BytesIO(response.content)).pages
    )
