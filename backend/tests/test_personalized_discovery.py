# ruff: noqa: F811
from types import SimpleNamespace

from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.api.deps import get_text_analysis
from app.domain.services.experience_dates import recent_experiences
from app.domain.services.work_preferences import employer_preference_conflicts


def test_travel_does_not_override_refusal_to_relocate_but_commuting_does():
    profile = SimpleNamespace(location="Medellín", department="Antioquia", preferences={"mobility": {"willing_to_relocate": False, "willing_to_travel": True}})
    job = SimpleNamespace(modality="onsite", location="Bogotá", department="Bogotá D.C.", salary=4_000_000)
    assert employer_preference_conflicts(profile, job)
    profile.preferences["mobility"]["commuting_cities"] = ["Bogotá, Bogotá D.C."]
    assert not employer_preference_conflicts(profile, job)
    profile.preferences.update(salary_required=True)
    profile.desired_salary = 5_000_000
    assert employer_preference_conflicts(profile, job)
    profile.preferences.update(salary_required=False, modality_required=True)
    profile.preferred_modality = "remote"
    assert employer_preference_conflicts(profile, job)
    job.modality = "remote"
    assert not employer_preference_conflicts(profile, job)


def test_recommendations_exclude_unrelated_profiles_even_at_zero_minimum(client):
    _, owner = company_account(client, "personalized-company")
    job = create_job(client, owner)
    relevant, _ = register(client, "relevant-python", profession="Desarrollador Python", skills=["Python", "SQL", "FastAPI"])
    unrelated, _ = register(client, "unrelated-accounting", profession="Contador", skills=["Excel", "contabilidad"])
    endpoint = f"/api/v1/recommendations/jobs/{job['id']}/candidates-page?audience=invite&minimum_match=0"
    response = client.get(endpoint, headers=owner)
    assert response.status_code == 200, response.text
    identifiers = {item["user_id"] for item in response.json()["items"]}
    assert relevant["id"] in identifiers and unrelated["id"] not in identifiers


def test_radar_uses_fresh_dates_instead_of_old_statistical_participation(client):
    account, headers = register(client, "fresh-radar", profession="Desarrollador Python", skills=["Python"], location="Medellín")
    from app.infrastructure.database.models import User
    with client.session_factory() as db:
        user = db.get(User, account["id"])
        user.profile.preferences = {**(user.profile.preferences or {}), "market_participation": {"level": "junior", "enabled": False}}
        db.commit()
    initial = client.get("/api/v1/profiles/me/market?personalized=true", headers=headers)
    assert initial.status_code == 200, initial.text
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    profile["experiences"] = [{"role": "Desarrollador", "start_date": "2017-07", "is_current": True}]
    client.put("/api/v1/profiles/me", headers=headers, json=profile).raise_for_status()
    report = client.get("/api/v1/profiles/me/market?personalized=true", headers=headers).json()
    assert report["suggested_filters"]["level"] == "senior"
    assert report["filters"]["level"] == "senior"
    assert report["participation"]["level"] == "junior"


def test_mobility_city_catalog_accepts_accents_and_rejects_invented_city(client):
    _, headers = register(client, "city-catalog")
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    profile["mobility"] = {"commuting_cities": ["medellin, antioquia", "Bogotá"]}
    response = client.put("/api/v1/profiles/me", headers=headers, json=profile)
    assert response.status_code == 200, response.text
    assert response.json()["mobility"]["commuting_cities"] == ["Medellín, Antioquia", "Bogotá"]
    profile["mobility"]["commuting_cities"] = ["Ciudad inventada"]
    assert client.put("/api/v1/profiles/me", headers=headers, json=profile).status_code == 422


def test_skill_search_is_scoped_and_does_not_run_embeddings(client):
    _, owner = company_account(client, "skill-detection")
    _, candidate = register(client, "skill-detection-candidate")
    calls = []
    client.app.dependency_overrides[get_text_analysis] = lambda: SimpleNamespace(extract_skills=lambda text: calls.append(text) or ["Python", "SQL", "Python"])
    response = client.post("/api/v1/hiring/skills/search", headers=owner, json={"text": "Buscamos Python y SQL"})
    assert response.status_code == 200 and set(response.json()["skills"]) == {"python", "sql"}
    assert len(calls) == 1
    assert client.post("/api/v1/hiring/skills/search", headers=candidate, json={"text": "Python"}).status_code == 403
    assert client.post("/api/v1/hiring/skills/search", headers=owner, json={"text": "a" * 20001}).status_code == 422


def test_experience_display_is_recent_first_without_mutating_source():
    source = [{"role": "Old", "start_year": "2018", "end_year": "2019"}, {"role": "Recent", "start_date": "2022-01", "end_date": "2023-10"}, {"role": "Current", "start_date": "2020-01", "is_current": True}, {"role": "Undated"}]
    assert [row["role"] for row in recent_experiences(source)] == ["Current", "Recent", "Old", "Undated"]
    assert source[0]["role"] == "Old"
