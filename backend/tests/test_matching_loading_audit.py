# ruff: noqa: F811
from types import SimpleNamespace as Row

import pytest
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.application.use_cases import learning, matching
from app.domain.services.languages import language_levels
from app.domain.services.matching import language_coverage
from app.domain.services.professions import education_match, infer_education_level


@pytest.mark.parametrize("name", ["Inglés", "inglés", " INGLES ", "English", "english"])
@pytest.mark.parametrize("level,expected", [("b1", 100), ("B2", 100), ("A2", 66.67), ("Nativo", 100)])
def test_language_identity_and_level_are_canonical_for_legacy_and_api_rows(name, level, expected):
    profile = Row(languages=[{"name": name, "level": level}])
    job = Row(languages=[{"name": "Inglés", "level": "B1"}])
    assert language_coverage(profile, job) == expected


def test_language_duplicates_missing_and_invalid_legacy_values_are_safe():
    profile = Row(languages=[{"name": "english", "level": "B2"}, {"name": "Inglés", "level": "A1"}])
    assert language_levels(profile.languages) == {"inglés": "B2"}
    assert language_coverage(profile, Row(languages=[{"name": "inglés", "level": "B1"}, {"name": "Inglés", "level": "b1"}])) == 100
    assert language_coverage(Row(languages=[]), Row(languages=[{"name": "inglés", "level": "B1"}])) == 0
    assert language_coverage(profile, Row(languages=[{"name": "inglés", "level": "bad"}])) is None


def test_study_fields_are_alternatives_and_technical_engineering_is_not_a_university_degree():
    profile = Row(profession="", education="", educations=[{"degree": "Ingeniería de sistemas", "level": "university"}])
    job = Row(required_study_fields=["Ingeniería informática", "Estadística"], required_education_level="university")
    assert education_match(profile, job) == 100
    assert infer_education_level("Técnico profesional en ingeniería de software") == "technical"
    assert infer_education_level("Tecnólogo en ingeniería de sistemas") == "technologist"


def test_unrelated_degree_cannot_supply_the_required_level_or_be_overridden_by_profession():
    job = Row(required_study_fields=["Ingeniería de sistemas"], required_education_level="university")
    profile = Row(profession="Ingeniero de sistemas", education="", educations=[{"degree": "Derecho", "level": "university"}])
    assert education_match(profile, job) == 0
    profile.educations.append({"degree": "Técnico en sistemas", "level": "technical"})
    assert education_match(profile, job) == 80
    profile.educations[-1].update(level="university", is_current=True)
    assert education_match(profile, job) == 70


def test_two_preference_flags_refresh_filters_without_recalculating_professional_scores(client, monkeypatch):
    _, owner = company_account(client, "flags-company")
    job = create_job(client, owner)
    user, headers = register(client, "flags-owner", skills=["python"], location="Cali")
    path = "/api/v1/recommendations/me/jobs/batch"
    first = client.get(path, headers=headers).json()["items"][0]
    def no_model(*args, **kwargs):
        raise AssertionError("Preference flags must not run inference")
    monkeypatch.setattr(matching, "_candidate_match", no_model)
    for flag in ("modality_required", "location_required"):
        response = client.put("/api/v1/matching/preferences", headers=headers, json={flag: True})
        assert response.status_code == 200, response.text
        result = client.get(path, headers=headers)
        assert result.status_code == 200, result.text
        assert result.json()["pending"] == 0
        assert result.json()["items"][0]["match_percentage"] == first["match_percentage"]
    saved = client.get("/api/v1/matching/preferences", headers=headers).json()
    assert saved["modality_required"] and saved["location_required"]
    assert client.get(f"/api/v1/jobs/{job['id']}", headers=headers).status_code == 200


def test_course_lookup_does_not_evaluate_unrelated_vacancy_compatibilities(client, monkeypatch):
    _, company = company_account(client, "course-speed-company")
    target = create_job(client, company)
    for _ in range(12):
        create_job(client, company)
    _, headers = register(client, "course-speed-owner", skills=["Java"])
    evaluated = []
    original = learning.candidate_match
    def tracked(profile, job, **kwargs):
        evaluated.append(job.id)
        return original(profile, job, **kwargs)
    monkeypatch.setattr(learning, "candidate_match", tracked)
    response = client.get(f"/api/v1/learning/jobs/{target['id']}", headers=headers)
    assert response.status_code == 200, response.text
    assert len(response.json()["resources"]) >= 2
    assert set(evaluated) == {target["id"]}
    assert len(evaluated) <= 11
    for path in ("catalog", "plans", "passport"):
        assert client.get(f"/api/v1/learning/{path}", headers=headers).status_code == 200
