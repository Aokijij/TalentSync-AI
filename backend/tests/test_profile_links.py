# ruff: noqa: F811
from io import BytesIO

import pytest
from pypdf import PdfReader
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.infrastructure.database.models import Job

LINKS = [
    {"platform": "github", "url": "https://github.com/portfolio-person", "label": ""},
    {"platform": "linkedin", "url": "https://www.linkedin.com/in/portfolio-person", "label": ""},
    {"platform": "portfolio", "url": "http://example.com/mi-trabajo", "label": "Mi portafolio"},
]


def save_links(client, headers, links):
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    return client.put("/api/v1/profiles/me", headers=headers, json={**profile, "links": links})


def test_links_persist_can_be_edited_and_removed_and_are_optional_for_older_clients(client):
    _, headers = register(client, "profile-links-owner", skills=["python"])
    assert client.get("/api/v1/profiles/me", headers=headers).json()["links"] == []
    response = save_links(client, headers, LINKS)
    assert response.status_code == 200, response.text
    assert response.json()["links"] == LINKS
    # A client that predates this field must not clear it when saving another field.
    older_payload = response.json()
    older_payload.pop("links")
    older_payload["profession"] = "Desarrollador de aplicaciones"
    response = client.put("/api/v1/profiles/me", headers=headers, json=older_payload)
    assert response.status_code == 200 and response.json()["links"] == LINKS
    revised = [{**LINKS[0], "url": "https://github.com/updated-person"}]
    assert save_links(client, headers, revised).json()["links"] == revised
    assert client.get("/api/v1/profiles/me", headers=headers).json()["links"] == revised
    assert save_links(client, headers, []).json()["links"] == []


@pytest.mark.parametrize("links", [
    [{"platform": "other", "url": "javascript:alert(1)"}],
    [{"platform": "other", "url": "data:text/html,example"}],
    [{"platform": "other", "url": "https://user:password@example.com"}],
    [{"platform": "github", "url": "https://github.com.example.com/person"}],
    [{"platform": "linkedin", "url": "https://example.com/person"}],
    [{"platform": "unknown", "url": "https://example.com/person"}],
    [{"platform": "other", "url": "https://example.com/" + "x" * 500}],
    [{"platform": "other", "url": "https://example.com/", "label": "x" * 61}],
    [LINKS[0], LINKS[0]],
    [{"platform": "other", "url": f"https://example.com/{index}"} for index in range(11)],
])
def test_invalid_links_are_rejected_without_changing_the_profile(client, links):
    _, headers = register(client, "invalid-profile-links")
    before = client.get("/api/v1/profiles/me", headers=headers).json()
    response = client.put("/api/v1/profiles/me", headers=headers, json={**before, "links": links})
    assert response.status_code == 422
    assert client.get("/api/v1/profiles/me", headers=headers).json() == before


def test_links_are_visible_to_an_authorized_company_but_hidden_during_blind_hiring(client):
    _, company = company_account(client)
    job = create_job(client, company)
    user, headers = register(client, "links-candidate", profession="Desarrollador Python", skills=["python"])
    assert save_links(client, headers, LINKS).status_code == 200
    endpoint = f"/api/v1/profiles/candidates/{user['id']}"
    assert client.get(endpoint, headers=company).status_code == 403
    assert client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"]}).status_code == 201
    assert client.get(endpoint, headers=company).json()["links"] == LINKS
    with client.session_factory() as db:
        db.get(Job, job["id"]).blind_hiring = True
        db.commit()
    response = client.get(endpoint + f"?job_id={job['id']}", headers=company)
    assert response.status_code == 200
    assert response.json()["identity_hidden"] and response.json()["links"] == []
    assert "portfolio-person" not in response.text


@pytest.mark.parametrize("style", ["classic", "modern", "minimal"])
def test_pdf_includes_clickable_links_and_contact_toggle_can_hide_them(client, style):
    _, headers = register(client, "links-export-" + style)
    assert save_links(client, headers, LINKS).status_code == 200
    before = client.get("/api/v1/profiles/me", headers=headers).json()
    preview_links = [*LINKS[:2], {"platform": "other", "url": "https://example.com/draft?x=1&y=2", "label": "Muestras <personales>"}]
    payload = {"sections": ["contact"], "include_photo": False, "profile": {**before, "links": preview_links, "resume_style": style}}
    response = client.post("/api/v1/profiles/me/export", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    reader = PdfReader(BytesIO(response.content))
    contents = " ".join(page.extract_text() for page in reader.pages)
    assert "ENLACES PROFESIONALES" in contents.upper() and "Muestras <personales>" in contents
    uris = {annotation.get_object().get("/A", {}).get("/URI") for page in reader.pages for annotation in page.get("/Annots", [])}
    assert {item["url"] for item in preview_links} <= uris
    response = client.post("/api/v1/profiles/me/export", headers=headers, json={**payload, "sections": ["summary"]})
    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    assert "portfolio-person" not in " ".join(page.extract_text() for page in reader.pages)
    assert not any(page.get("/Annots") for page in reader.pages)
    assert client.get("/api/v1/profiles/me", headers=headers).json() == before


def test_older_preview_clients_still_include_the_saved_links(client):
    _, headers = register(client, "links-older-preview")
    save_links(client, headers, LINKS)
    response = client.post("/api/v1/profiles/me/export", headers=headers, json={"sections": ["contact"], "include_photo": False, "profile": {"profession": "Desarrollador"}})
    assert response.status_code == 200
    assert "github.com/portfolio-person" in " ".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)
