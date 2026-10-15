from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.domain.services.skills import skill_gap, skill_key


def test_profile_conditions_are_authoritative_and_requirement_flags_refresh_without_invalidating_scores(client):  # noqa: F811
    _, company = company_account(client, "profile-conditions")
    job = create_job(client, company)
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=company, json={"salary": 3_000_000, "modality": "onsite", "location": "Bogotá"}).status_code == 200
    _, headers = register(client, "profile-conditions-person", skills=["python"])
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    profile.update(desired_salary=4_000_000, preferred_modality="hybrid", location="Medellín")
    assert client.put("/api/v1/profiles/me", headers=headers, json=profile).status_code == 200
    endpoint = f"/api/v1/matching/jobs/{job['id']}"
    initial = client.get(endpoint, headers=headers).json()
    response = client.put("/api/v1/matching/preferences", headers=headers, json={"salary_required": True})
    assert response.status_code == 200
    assert response.json()["minimum_salary"] == 4_000_000
    assert response.json()["modalities"] == ["hybrid"]
    required = client.get(endpoint, headers=headers).json()
    assert required["preferences"]["unmet_conditions"] == ["Salario mínimo"]
    assert required["overall_score"] == initial["overall_score"]
    assert required["input_version"] == initial["input_version"]
    profile.update(desired_salary=2_500_000, preferred_modality="onsite", location="Bogotá")
    assert client.put("/api/v1/profiles/me", headers=headers, json=profile).status_code == 200
    fresh = client.get("/api/v1/recommendations/me/jobs", headers=headers, params={"include_all": True}).json()[0]["match_details"]
    assert fresh["preferences"]["unmet_conditions"] == []
    assert all(row["matches"] for row in fresh["preferences"]["checks"])
    assert fresh["input_version"] != required["input_version"]
    assert client.get("/api/v1/matching/preferences", headers=headers).json()["salary_required"] is True


def test_related_skills_are_not_equivalent():
    assert skill_key("SpringBoot") == "spring boot"
    rows = skill_gap(["Java", "Docker"], [{"skill": "spring boot", "essential": True, "weight": 3}])
    assert rows[0]["status"] == "related"
    assert rows[0]["foundations"] == ["java"]
    assert not rows[0]["covered"]


def test_weighted_match_explanations_preferences_evidence_and_cache(client):  # noqa: F811
    _, company = company_account(client)
    job = create_job(client, company)
    candidate, headers = register(client, "match-user", skills=["Python"])
    requirements = [{"skill": "python", "essential": False, "weight": 1}, {"skill": "java", "essential": True, "weight": 3}]
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=company, json={"skill_requirements": requirements}).status_code == 200
    endpoint = f"/api/v1/matching/jobs/{job['id']}"
    details = client.get(endpoint, headers=headers).json()
    assert details["components"][0]["score"] == 25
    assert details["unmet_essential_skills"] == ["java"]
    assert abs(sum(row["points"] for row in details["components"]) - details["overall_score"]) < .02
    assert details["score_type"] == "compatibility_index"
    assert client.put("/api/v1/matching/preferences", headers=headers, json={"minimum_salary": 8_000_000, "salary_required": True, "modalities": ["onsite"], "modality_required": True}).status_code == 200
    evidence = {"title": "API personal", "kind": "repository", "url": "https://example.com/project", "description": "API implementada con Python y pruebas", "skills": ["Python"]}
    response = client.post("/api/v1/matching/evidence", headers=headers, json=evidence)
    assert response.status_code == 200
    row = response.json()[0]
    assert not row["verified"]
    details = client.get(endpoint, headers=headers).json()
    assert details["preferences"]["unmet_conditions"] == ["Modalidad"]
    assert details["preferences"]["unknown_conditions"] == ["Salario mínimo"]
    assert details["requirements"][0]["evidence"][0]["verified"] is False
    _, other = register(client, "other-evidence")
    assert client.delete(f"/api/v1/matching/evidence/{row['id']}", headers=other).status_code == 404
    assert client.delete(f"/api/v1/matching/evidence/{row['id']}", headers=headers).status_code == 204
    records = client.get("/api/v1/recommendations/me/jobs", headers=headers, params={"include_all": True})
    assert records.status_code == 200
    # A changed requirement invalidates cached recommendations even within ten minutes.
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=company, json={"skill_requirements": [{"skill": "python", "essential": True, "weight": 1}]}).status_code == 200
    fresh = client.get("/api/v1/recommendations/me/jobs", headers=headers, params={"include_all": True}).json()[0]["match_details"]
    assert fresh["components"][0]["score"] == 100
    assert fresh["input_version"] != details["input_version"]
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=company, json={"skill_requirements": [requirements[0], requirements[0]]}).status_code == 422
