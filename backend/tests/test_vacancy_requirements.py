from datetime import date
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from test_offer_quality import complete_offer

from app.api.schemas.job import JobCreate
from app.api.schemas.job_quality import QualityDetails, RemoteScope
from app.domain.services.job_requirements import minimum_experience_months
from app.domain.services.offer_review import review_offer
from app.domain.services.professions import education_match, infer_education_level
from app.domain.services.remote_locations import remote_scope_fit
from app.domain.services.requirement_analysis import relevant_experience


def review(payload):
    return review_offer(SimpleNamespace(**payload, pipeline_stages=[{"id": "submitted"}]))


def test_basic_information_has_70_points_and_additional_improvements_30():
    payload = complete_offer()
    report = review(payload)
    assert report["score"] == 100
    assert sum(row["weight"] for row in report["checks"] if row["required"]) == 70
    assert sum(row["weight"] for row in report["checks"] if not row["required"]) == 30
    payload["quality_details"].update(schedule="", missions=[], interview_count=None, process_days=None)
    payload["description"] = "Analizará los reportes semanales de ventas para el equipo."
    report = review(payload)
    assert report["minimum_publish_score"] == 60 and report["can_publish"]
    assert report["score"] == 69


@pytest.mark.parametrize("count", [0, 1, 2, 3])
def test_three_distinct_skills_are_required_with_partial_credit(count):
    payload = complete_offer()
    payload["skill_requirements"] = payload["skill_requirements"][:count]
    report = review(payload)
    check = next(row for row in report["checks"] if row["key"] == "skill_requirements")
    assert check["passed"] is (count == 3)
    assert report["can_publish"] is (count == 3)
    assert check["points"] == round(min(8, count * 8 / 3))


def test_duplicate_skill_aliases_do_not_count_as_three_skills():
    payload = complete_offer()
    payload["skill_requirements"] = [{"skill": name} for name in ["JS", "javascript", "sql"]]
    assert not review(payload)["can_publish"]
    with pytest.raises(ValidationError):
        JobCreate.model_validate(payload)


def test_monthly_requirement_matches_related_experience_without_rounding_to_years():
    job = SimpleNamespace(title="Desarrollador Python", requirements="", skills=["python"], quality_details={"experience_months": 6})
    profile = SimpleNamespace(experiences=[{"role": "Desarrollador Python", "start_date": "2025-01", "end_date": "2025-02"}])
    result = relevant_experience(profile, job, date(2026, 10, 16))
    assert result["required_months"] == 6 and result["related_months"] == 2
    assert result["status"] == "partial" and result["score"] == 33.33
    profile.experiences[0]["end_date"] = "2025-06"
    assert relevant_experience(profile, job)["status"] == "fulfilled"
    assert minimum_experience_months({"experience_years": 2}) == 24
    assert minimum_experience_months({"experience_months": 6, "experience_years": 2}) == 6
    job.quality_details = {}
    job.requirements = "Solicitamos al menos 6 meses de experiencia relacionada."
    assert relevant_experience(profile, job)["required_months"] == 6


def test_education_in_progress_only_meets_level_when_explicitly_accepted():
    profile = SimpleNamespace(educations=[{"degree": "Ingeniería de sistemas", "level": "university", "is_current": True}])
    job = SimpleNamespace(required_education_level="university", required_study_fields=["Ingeniería de sistemas"], quality_details={})
    assert education_match(profile, job) == 70
    job.quality_details = {"education_accepts_in_progress": True}
    assert education_match(profile, job) == 100
    job.required_study_fields = ["Contaduría"]
    assert education_match(profile, job) == 0
    assert infer_education_level("Bachiller académico") == "secondary"
    payload = complete_offer()
    payload["required_education_level"] = "secondary"
    assert JobCreate.model_validate(payload).required_education_level == "secondary"


def test_secondary_education_requires_completion_and_ignores_career_restrictions():
    profile = SimpleNamespace(educations=[{"degree": "Bachiller académico", "level": "secondary", "is_current": True}])
    job = SimpleNamespace(required_education_level="secondary", required_study_fields=["Ingeniería de sistemas"], quality_details={"education_accepts_in_progress": True})
    assert education_match(profile, job) == 0
    profile.educations[0]["is_current"] = False
    assert education_match(profile, job) == 100


@pytest.mark.parametrize("location,allowed", [("Medellín, Antioquia", True), ("España", True), ("México", True), ("Japón", False)])
def test_remote_scope_accepts_union_of_countries_and_continents(location, allowed):
    profile = SimpleNamespace(location=location, preferences={})
    job = SimpleNamespace(quality_details={"remote_scope": {"mode": "regions", "countries": ["CO", "MX"], "continents": ["EU"]}})
    fit = remote_scope_fit(profile, job)
    assert fit["invitation_allowed"] is allowed
    assert fit["status"] == ("remote" if allowed else "conflict")


def test_unknown_country_is_not_invented_and_empty_regional_scope_blocks_publication():
    profile = SimpleNamespace(location="", preferences={})
    scope = {"mode": "regions", "countries": ["CO"], "continents": []}
    job = SimpleNamespace(quality_details={"remote_scope": scope})
    assert remote_scope_fit(profile, job)["status"] == "unknown"
    payload = complete_offer()
    payload["quality_details"]["remote_scope"] = {**scope, "countries": []}
    assert "location" in [row["key"] for row in review(payload)["blockers"]]
    assert RemoteScope(countries=["co", "CO"], mode="regions").countries == ["CO"]
    with pytest.raises(ValidationError):
        RemoteScope(countries=["ZZ"], mode="regions")
    with pytest.raises(ValidationError):
        RemoteScope(countries=["CO"], mode="global")


def test_schedule_hours_are_derived_and_old_manual_values_cannot_override_them():
    schedule = {"mode": "fixed", "days": ["mon", "tue", "wed", "thu", "fri"], "start": "05:30", "end": "15:30", "break_minutes": 60}
    assert QualityDetails(work_schedule=schedule, weekly_hours=40).weekly_hours == 45
    schedule.update(days=["mon", "mon"], start="22:00", end="06:00", break_minutes=30)
    assert QualityDetails(work_schedule=schedule).weekly_hours == 7.5
    schedule.update(mode="flexible")
    assert QualityDetails(work_schedule=schedule, weekly_hours=40).weekly_hours is None
    assert QualityDetails(weekly_hours=40).weekly_hours == 40
    schedule.update(mode="fixed", days=["mon", "tue", "wed", "thu", "fri"], start="01:00", end="23:00", break_minutes=0)
    with pytest.raises(ValidationError):
        QualityDetails(work_schedule=schedule)
