from types import SimpleNamespace

import pytest

from app.domain.services.matching import (
    combined_match,
    is_relevant_candidate_recommendation,
    recommend_category,
    recommendation_reasons,
    required_skill_coverage,
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
    assert reasons[:2] == ["score:skills:50", "score:semantic:75"]
    assert "Tu experiencia/profesión se alinea con el cargo" in reasons
    assert "Skills fuertes: python" in reasons
    assert "Para subir tu match: trabaja sql" in reasons
    assert combined_match(75, 50) == 60
