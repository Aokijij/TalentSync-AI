# ruff: noqa: F811
from datetime import date
from types import SimpleNamespace

import pytest
from test_api_flows import client, company_account, create_job, register  # noqa: F401
from test_offer_quality import complete_offer

from app.domain.services.experience_dates import experience_months, validate_experiences
from app.domain.services.work_preferences import location_fit


def test_month_precision_current_jobs_overlap_and_unknown_end():
    today = date(2026, 10, 13)
    periods = [{"start_date": "2024-01", "end_date": "2024-06"}, {"start_date": "2024-03", "end_date": "2024-12"}]
    assert experience_months(periods, today) == 12  # Overlap is not counted twice.
    assert experience_months([{"start_date": "2026-08", "is_current": True}], today) == 3
    assert experience_months([{"start_date": "2024-01", "end_date": ""}], today) == 0
    assert experience_months([{"start_year": "2020", "end_year": "2026"}], today) == 72
    assert experience_months([{"start_date": "2024-04", "end_date": "2024-04"}], today) == 1


@pytest.mark.parametrize("item", [
    {"start_date": "2024-13"}, {"start_date": "2024-06", "end_date": "2024-05"},
    {"start_date": "2099-01"}, {"is_current": True, "end_date": "2024-01"}, {"is_current": "false"},
])
def test_invalid_dates_are_rejected(item):
    with pytest.raises(ValueError):
        validate_experiences([item])


@pytest.mark.parametrize("modality,city,mobility,expected", [
    ("remote", "Cali", {"willing_to_relocate": False, "willing_to_travel": False}, "remote"),
    ("onsite", "Bogota D.C.", {}, "local"),
    ("hybrid", "Cali", {"willing_to_relocate": True}, "relocation"),
    ("hybrid", "Cali", {"willing_to_travel": True, "willing_to_relocate": False}, "confirm"),
    ("onsite", "Cali", {"willing_to_travel": False, "willing_to_relocate": False}, "conflict"),
    ("onsite", "Cali", {"commuting_cities": ["Bogotá"]}, "local"),
    ("hybrid", "", {}, "unknown"), ("onsite", "Cali", {}, "unknown"),
])
def test_location_respects_explicit_mobility_without_assuming_daily_travel(modality, city, mobility, expected):
    profile = SimpleNamespace(location=city, preferences={"mobility": mobility})
    job = SimpleNamespace(modality=modality, location="Bogotá")
    result = location_fit(profile, job)
    assert result["status"] == expected
    assert result["factor"] == (.8 if expected == "conflict" else 1)
    assert result["invitation_allowed"] is (expected != "conflict")


def test_profile_dates_and_mobility_survive_preference_flags_and_ranked_pages(client):
    _, owner = company_account(client, "mobility-owner")
    job = create_job(client, owner)
    client.patch(f"/api/v1/jobs/{job['id']}", headers=owner, json={"modality": "onsite", "location": "Bogotá"}).raise_for_status()
    candidate, headers = register(client, "mobility-candidate", profession="Desarrollador Python", skills=["Python", "SQL", "FastAPI"])
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    mobility = {"willing_to_relocate": False, "willing_to_travel": False, "commuting_cities": []}
    profile.update(location="Cali", department="Valle del Cauca", mobility=mobility,
                   experiences=[{"role": "Desarrollador", "start_date": "2024-01", "end_date": "2024-12", "is_current": False}])
    saved = client.put("/api/v1/profiles/me", headers=headers, json=profile)
    assert saved.status_code == 200, saved.text
    assert saved.json()["mobility"] == mobility
    client.put("/api/v1/matching/preferences", headers=headers, json={"location_required": True}).raise_for_status()
    assert client.get("/api/v1/profiles/me", headers=headers).json()["mobility"] == mobility
    legacy = {key: value for key, value in profile.items() if key != "mobility"}
    client.put("/api/v1/profiles/me", headers=headers, json=legacy).raise_for_status()
    assert client.get("/api/v1/profiles/me", headers=headers).json()["mobility"] == mobility
    page = client.get(f"/api/v1/recommendations/jobs/{job['id']}/candidates-page?minimum_match=0&limit=5", headers=owner)
    assert page.status_code == 200, page.text
    assert candidate["id"] not in {item["user_id"] for item in page.json()["items"]}
    invitation = client.post(f"/api/v1/recommendations/jobs/{job['id']}/candidates/{candidate['id']}/invite", headers=owner)
    assert invitation.status_code == 422 and "traslado" in invitation.json()["detail"]
    client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"]}).raise_for_status()
    applied = client.get(f"/api/v1/recommendations/jobs/{job['id']}/candidates-page?audience=applied", headers=owner)
    row = next(item for item in applied.json()["items"] if item["user_id"] == candidate["id"])
    assert row["location_fit"]["status"] == "conflict" and row["experience_months"] == 12
    profile["experiences"][0]["end_date"] = "2023-12"
    assert client.put("/api/v1/profiles/me", headers=headers, json=profile).status_code == 422


def test_offer_review_handles_languages_and_current_conditions_without_publishing(client):
    _, owner = company_account(client, "quality-languages-review")
    payload = complete_offer()
    payload["languages"] = [{"name": "inglés", "level": "B2"}]
    response = client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload)
    assert response.status_code == 200, response.text
    checks = {row["key"]: row for row in response.json()["checks"]}
    assert checks["contract_type"]["passed"] and checks["schedule"]["passed"]
    payload["quality_details"]["schedule"] = "aaaaaaaaaaaaaaaaaa"
    response = client.post("/api/v1/hiring/quality/preview", headers=owner, json=payload)
    assert not next(row for row in response.json()["checks"] if row["key"] == "schedule")["passed"]
    assert not response.json()["can_publish"]
