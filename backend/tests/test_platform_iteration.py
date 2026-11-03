# ruff: noqa: F811
from datetime import datetime
from io import BytesIO
from types import SimpleNamespace as Row
from urllib.parse import unquote

import pytest
from pypdf import PdfReader
from test_api_flows import client, company_account, create_job, register  # noqa: F401
from test_career_coach_workspace import candidate, proposal

from app.application.errors import UseCaseError
from app.domain.services.professions import education_match
from app.infrastructure.database.models import Application, Company, Job, Profile
from app.infrastructure.resume_previews import ResumePreviews
from scripts.seed_market_radar import SCENARIOS, seed


def test_seeded_radar_is_varied_idempotent_and_never_mixed_with_real_data(client):
    _, headers = register(client, "radar-demo-viewer", skills=["python", "sql"])
    with client.session_factory() as db:
        seed(db); seed(db)
        assert db.query(Profile).filter(Profile.preferences["radar_demo"].as_boolean().is_(True)).count() == 72
        assert db.query(Company).filter_by(source_name="radar-demo").count() == 24
        assert db.query(Job).filter_by(source_name="radar-demo", status="draft").count() == 72
        for family, level, city, _, _ in SCENARIOS:
            result = client.get("/api/v1/profiles/me/market", params={"dataset": "demo", "family": family, "level": level, "location": city}, headers=headers)
            assert result.status_code == 200, result.text
            data = result.json()
            assert data["dataset"] == "demo" and data["demand"]["sample"] == 24 and not data["demand"]["jobs"]
            assert data["peers"]["sample"] == 24 and len(data["peers"]["skills"]) >= 5
            assert data["salary"]["groups"][0]["sample"] == 24
            assert data["salary"]["groups"][0]["p25"] < data["salary"]["groups"][0]["median"] < data["salary"]["groups"][0]["p75"]
            assert "simulados" in data["salary"]["note"] and "ficticios" in data["peers"]["note"]
    real = client.get("/api/v1/profiles/me/market", params={"family": "software", "level": "junior", "location": "Medellín"}, headers=headers).json()
    assert real["demand"]["sample"] == 0 and real["peers"]["status"] == "insufficient_data" and not real["salary"]["groups"]
    assert real["demo_available"]
    assert {row["skill"] for row in real["demand"]["own_skills"]} == {"python", "sql"}
    assert not client.get("/api/v1/jobs", headers=headers).json()  # Demo salary scenarios remain unpublished.


def test_delete_versions_is_owner_scoped_and_never_undoes_applied_text(client):
    user, headers = candidate(client, "versions-owner")
    _, other = candidate(client, "versions-other")
    first = proposal(client, headers)
    path = f"/api/v1/profiles/me/coach/writing/{first['id']}"
    assert client.delete(path, headers=other).status_code == 404
    assert client.put(path, headers=headers, json={"action": "apply"}).status_code == 200
    before = client.get("/api/v1/profiles/me", headers=headers).json()
    assert client.delete(path, headers=headers).status_code == 200
    assert client.get("/api/v1/profiles/me", headers=headers).json() == before
    assert client.get("/api/v1/profiles/me/coach", headers=headers).json()["writing"] == []
    assert client.delete(path, headers=headers).status_code == 404


def test_explicit_education_level_wins_over_title_and_current_study_is_not_completed(client):
    job = Row(required_education_level="university", required_study_fields=["sistemas"])
    profile = Row(profession="Ingeniería de Sistemas", education="", educations=[{"degree": "Tecnología en sistemas", "level": "university", "end_year": "2024"}])
    assert education_match(profile, job) == 100
    profile.educations[0]["level"] = "technical"
    assert education_match(profile, job) == 80
    profile.educations[0].update(level="university", is_current=True, end_year="")
    assert education_match(profile, job) == 70
    _, headers = register(client, "education-level")
    value = client.get("/api/v1/profiles/me", headers=headers).json()
    value["educations"] = profile.educations
    assert client.put("/api/v1/profiles/me", headers=headers, json=value).status_code == 200
    value["educations"][0]["level"] = "invented"
    assert client.put("/api/v1/profiles/me", headers=headers, json=value).status_code == 422


def test_company_public_score_matches_vacancy_without_exposing_reasons(client):
    _, company = company_account(client, "public-score")
    job = create_job(client, company)
    user, headers = register(client, "public-score-viewer")
    with client.session_factory() as db:
        db.add(Application(user_id=user["id"], job_id=job["id"], status="rejected", resolution_reason="response_deadline", created_at=datetime.utcnow()))
        db.commit()
    public = client.get(f"/api/v1/companies/{job['company_id']}", headers=headers)
    assert public.status_code == 200, public.text
    detail = client.get(f"/api/v1/jobs/{job['id']}", headers=headers).json()
    assert public.json()["platform_score"] == detail["employer_trust"]["score"]
    assert public.json()["platform_score"] < 100
    assert "confirmed_incidents" not in public.json() and "missed_deadlines" not in public.json()


def test_named_native_preview_is_private_identical_and_has_filename_and_frame_policy(client):
    _, headers = register(client, "named-pdf-owner")
    _, other = register(client, "named-pdf-other")
    response = client.post("/api/v1/profiles/me/export/preview", headers=headers, json={"profile": {"name": "José / Prueba"}, "include_photo": False})
    assert response.status_code == 200, response.text
    resource = response.json(); assert resource["filename"] == "José Prueba - TalentSync - Hoja de vida.pdf"
    assert resource["url"].endswith(".pdf")
    assert client.get(resource["url"]).status_code == 401
    assert client.get(resource["url"], headers=other).status_code == 404
    preview = client.get(resource["url"], headers=headers)
    assert preview.status_code == 200 and preview.content == client.get(resource["url"], headers=headers).content
    assert resource["filename"] in unquote(preview.headers["content-disposition"])
    assert "TalentSync" in PdfReader(BytesIO(preview.content)).metadata.title
    assert "x-frame-options" not in preview.headers and "frame-ancestors 'self'" in preview.headers["content-security-policy"]
    assert "*" not in preview.headers["content-security-policy"] and "no-store" in preview.headers["cache-control"]
    assert client.get("/health").headers["x-frame-options"] == "DENY"


def test_previews_expire_and_are_bounded_per_owner():
    previews = ResumePreviews()
    old = previews.put(1, b"one", "one.pdf")
    for index in range(5):
        previews.put(1, b"data", f"{index}.pdf")
    assert len(previews.entries) == 3
    with pytest.raises(UseCaseError):
        previews.get(1, old, "one.pdf")
    token = previews.put(2, b"private", "private.pdf")
    with pytest.raises(UseCaseError):
        previews.get(1, token, "private.pdf")
    row = previews.entries[token]; previews.entries[token] = (*row[:3], 0)
    with pytest.raises(UseCaseError):
        previews.get(2, token, "private.pdf")
