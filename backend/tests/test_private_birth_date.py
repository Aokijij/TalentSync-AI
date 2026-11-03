# ruff: noqa: F811
from io import BytesIO

import pytest
from pypdf import PdfReader
from test_api_flows import client, company_account, register  # noqa: F401
from test_credentials_api import save
from test_offer_quality import complete_offer

from app.domain.services.career_coach import snapshot
from app.infrastructure.database.models import User


def test_birth_date_is_private_preserved_when_omitted_and_does_not_affect_matching(client):
    person, candidate = register(client, "private-birthday", skills=["sql", "excel"])
    _, company = company_account(client, "birthday-employer")
    save(client, candidate)
    response = client.post("/api/v1/jobs", headers=company, json=complete_offer())
    assert response.status_code == 201, response.text
    job = response.json()
    matching = f"/api/v1/matching/jobs/{job['id']}"
    before = client.get(matching, headers=candidate).json()
    profile = save(client, candidate, birth_date="1994-06-17")
    assert profile["birth_date"] == "1994-06-17"
    with client.session_factory() as session:
        coach_input = snapshot(session.get(User, person["id"]).profile)
        assert "birth_date" not in coach_input and "1994-06-17" not in str(coach_input)
    assert client.get("/api/v1/profiles/me", headers=candidate).json()["birth_date"] == "1994-06-17"
    after = client.get(matching, headers=candidate).json()
    assert before["input_version"] == after["input_version"]
    assert before["overall_score"] == after["overall_score"]
    assert "1994-06-17" not in str(after)
    legacy = {key: value for key, value in profile.items() if key != "birth_date"}
    assert client.put("/api/v1/profiles/me", headers=candidate, json=legacy).status_code == 200
    assert client.get("/api/v1/profiles/me", headers=candidate).json()["birth_date"] == "1994-06-17"
    assert client.post("/api/v1/applications", headers=candidate, json={"job_id": job["id"]}).status_code == 201
    shared = client.get(f"/api/v1/profiles/candidates/{person['id']}?job_id={job['id']}", headers=company)
    assert shared.status_code == 200, shared.text
    assert "birth_date" not in shared.json() and "1994-06-17" not in shared.text
    document = {"type": "CC", "number": "ID-EXAMPLE-7788"}
    save(client, candidate, identification=document, personal_visibility={"birth_date": True, "identification": True})
    endpoint = f"/api/v1/profiles/candidates/{person['id']}?job_id={job['id']}"
    shared = client.get(endpoint, headers=company).json()
    assert shared["birth_date"] == "1994-06-17" and shared["identification"] == document
    assert "personal_visibility" not in shared
    own = client.get("/api/v1/profiles/me", headers=candidate).json()
    legacy = {key: value for key, value in own.items() if key not in {"birth_date", "identification", "personal_visibility"}}
    preserved = client.put("/api/v1/profiles/me", headers=candidate, json=legacy).json()
    assert preserved["identification"] == document and preserved["personal_visibility"]["birth_date"] is True
    with client.session_factory() as session:
        assert "ID-EXAMPLE-7788" not in str(snapshot(session.get(User, person["id"]).profile))
    save(client, candidate, personal_visibility={"birth_date": False, "identification": True})
    shared = client.get(endpoint, headers=company).json()
    assert "birth_date" not in shared and shared["identification"] == document
    save(client, candidate, personal_visibility={})
    assert "identification" not in client.get(endpoint, headers=company).json()
    assert client.get(matching, headers=candidate).json()["input_version"] == before["input_version"]
    assert save(client, candidate, birth_date=None)["birth_date"] is None


@pytest.mark.parametrize("value", ["2099-01-01", "1899-12-31", "2000-02-30", "not-a-date"])
def test_birth_date_rejects_invalid_and_future_values(client, value):
    _, candidate = register(client, "invalid-birthday-" + value)
    response = client.put("/api/v1/profiles/me", headers=candidate, json={"birth_date": value})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "birth_date"]


@pytest.mark.parametrize("style", ["classic", "modern", "minimal"])
def test_private_birth_date_is_never_exported_in_cv(client, style):
    _, candidate = register(client, "birthday-pdf-" + style)
    save(client, candidate, birth_date="1994-06-17")
    response = client.post("/api/v1/profiles/me/export", headers=candidate, json={"include_photo": False, "profile": {"resume_style": style, "birth_date": "1994-06-17"}})
    assert response.status_code == 200, response.text
    text = " ".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)
    assert "1994" not in text and "nacimiento" not in text.lower()
    document = {"type": "passport", "number": "SHARE-EXAMPLE-7788"}
    save(client, candidate, identification=document, personal_visibility={"birth_date": True, "identification": True})
    response = client.post("/api/v1/profiles/me/export", headers=candidate, json={"include_photo": False, "profile": {"resume_style": style}})
    assert response.status_code == 200, response.text
    text = " ".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)
    assert "17/06/1994" in text and "SHARE-EXAMPLE-7788" in text
    header = []
    def collect_header(value, cm, tm, font, size):
        # Header contacts are translated by their containing ReportLab table.
        if "17/06/1994" in value or "SHARE-EXAMPLE-7788" in value:
            header.append(cm[5] + tm[5])
    PdfReader(BytesIO(response.content)).pages[0].extract_text(visitor_text=collect_header)
    assert len(header) == 2 and min(header) > 680
    assert "DATOS PERSONALES" not in text
    # A private draft can hide one field without saving a change to the profile.
    response = client.post("/api/v1/profiles/me/export", headers=candidate, json={"include_photo": False, "profile": {"resume_style": style, "personal_visibility": {"birth_date": False, "identification": True}}})
    text = " ".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)
    assert "1994" not in text and "SHARE-EXAMPLE-7788" in text
    assert client.get("/api/v1/profiles/me", headers=candidate).json()["personal_visibility"]["birth_date"] is True
