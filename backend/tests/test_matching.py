from types import SimpleNamespace

import pytest

from app.domain.services.matching import (
    combined_match,
    is_relevant_candidate_recommendation,
    professional_context_alignment,
    recommend_category,
    recommendation_reasons,
    required_skill_coverage,
    language_coverage,
)


def test_required_skills_are_normalized_and_duplicates_do_not_inflate_score():
    assert required_skill_coverage(
        ["Python", "python", "SQL"], ["python", "sql", "Docker", "docker"]
    ) == pytest.approx(200 / 3)
    assert required_skill_coverage(["Python"], []) == 0
    assert required_skill_coverage([], ["Python"]) == 0


@pytest.mark.parametrize(
    "score,skills,category",
    [(80, 50, "alta"), (80, 49, "buenas"), (65, 0, "buenas"), (64.99, 100, "brechas")],
)
def test_category_boundaries(score, skills, category):
    assert recommend_category(score, skills) == category


def test_cross_sector_recommendations_need_exceptional_fit():
    profile = SimpleNamespace(preferred_sector="Salud")
    job = SimpleNamespace(sector="Tecnologia")
    match = SimpleNamespace(
        skill_match_percentage=80, semantic_match_percentage=75, match_percentage=78
    )
    assert is_relevant_candidate_recommendation(match, profile, job)
    match.semantic_match_percentage = 74.99
    assert not is_relevant_candidate_recommendation(match, profile, job)
    profile.preferred_sector = job.sector
    assert is_relevant_candidate_recommendation(match, profile, job)
    match.match_percentage = 39.99
    assert not is_relevant_candidate_recommendation(match, profile, job)


def test_reason_metadata_order_and_matching_weights_are_stable():
    profile = SimpleNamespace(skills=["Python"], profession="Desarrollador")
    job = SimpleNamespace(skills=["Python", "SQL"], title="Desarrollador Python")
    reasons = recommendation_reasons(profile, job, semantic=75, skill_score=50)
    assert reasons[:2] == ["score:skills:50", "score:context:75"]
    assert "Tu experiencia y profesión se alinean con el cargo" in reasons
    assert "Habilidades que ya cumples: python" in reasons
    assert "Habilidades por fortalecer: sql" in reasons
    assert combined_match(75, 50) == 60


def test_professional_context_rewards_related_roles_and_experience():
    aligned_profile = SimpleNamespace(
        profession="Desarrolladora backend",
        experience="Diseño y desarrollo de APIs con Python para servicios financieros",
        education="Ingeniería de sistemas",
        experiences=[{"role": "Desarrolladora Python", "description": "APIs y bases de datos"}],
        educations=[],
        certifications=[],
    )
    unrelated_profile = SimpleNamespace(
        profession="Diseñadora gráfica",
        experience="Ilustración editorial y campañas publicitarias",
        education="Diseño visual",
        experiences=[],
        educations=[],
        certifications=[],
    )
    job = SimpleNamespace(
        title="Desarrollador Python",
        description="Construcción de APIs para servicios financieros",
        requirements="Experiencia en backend y bases de datos",
        sector="Tecnología",
    )

    aligned = professional_context_alignment(aligned_profile, job, semantic=60)
    unrelated = professional_context_alignment(unrelated_profile, job, semantic=60)

    assert aligned > unrelated
    assert 0 <= unrelated <= 100
    assert 0 <= aligned <= 100


def test_language_levels_affect_matching_only_when_required():
    profile = SimpleNamespace(languages=[{"name": "inglés", "level": "B1"}])
    job = SimpleNamespace(languages=[{"name": "inglés", "level": "B2"}])
    assert language_coverage(profile, job) == 75
    assert combined_match(50, 100, 75) == 82.5
    profile.languages[0]["level"] = "NATIVE"
    assert language_coverage(profile, job) == 100
    profile.languages = []
    assert language_coverage(profile, job) == 0
    job.languages = []
    assert language_coverage(profile, job) is None
    assert combined_match(50, 100) == 80
