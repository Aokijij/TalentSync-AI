from app.domain.entities.records import Job, Profile, Recommendation
from app.domain.services.skills import skill_set

SKILL_WEIGHT = 0.6
SEMANTIC_WEIGHT = 0.4
MIN_CANDIDATE_RECOMMENDATION = 40.0


def required_skill_coverage(
    candidate_skills: list[str] | None, required_skills: list[str] | None
) -> float:
    candidate_tokens = skill_set(candidate_skills)
    required_tokens = skill_set(required_skills)
    if not required_tokens:
        return 0.0
    return (
        len(candidate_tokens.intersection(required_tokens)) / len(required_tokens) * 100
    )


def is_relevant_candidate_recommendation(
    item: Recommendation, profile: Profile, job: Job
) -> bool:
    """Reject accidental matches caused only by generic tools such as Excel."""
    skill_score = item.skill_match_percentage
    semantic_score = item.semantic_match_percentage
    exceptional_cross_sector_fit = skill_score >= 80.0 and semantic_score >= 75.0
    sector_aligned = (
        not profile.preferred_sector
        or profile.preferred_sector == job.sector
        or exceptional_cross_sector_fit
    )
    return (
        sector_aligned
        and item.match_percentage >= MIN_CANDIDATE_RECOMMENDATION
        and (
            skill_score >= 50.0
            or semantic_score >= 75.0
            or (skill_score >= 30.0 and semantic_score >= 65.0)
        )
    )


def combined_match(semantic: float, skill_score: float) -> float:
    """Transparent score: required skills lead, CV/job context validates fit."""
    return round(skill_score * SKILL_WEIGHT + semantic * SEMANTIC_WEIGHT, 2)


def recommendation_reasons(
    profile: Profile, job: Job, semantic: float, skill_score: float
) -> list[str]:
    profile_skills = skill_set(profile.skills)
    job_skills = skill_set(job.skills)
    overlap = sorted(profile_skills.intersection(job_skills))
    missing = sorted(job_skills - profile_skills)
    reasons: list[str] = []
    if profile.profession:
        profession = profile.profession.lower().strip()
        title = job.title.lower()
        if profession and (
            profession in title or any(token in title for token in profession.split())
        ):
            reasons.append("Tu experiencia/profesión se alinea con el cargo")
    if overlap:
        reasons.append(f"Skills fuertes: {', '.join(overlap[:7])}")
    if job_skills and missing:
        reasons.append(f"Para subir tu match: trabaja {', '.join(missing[:7])}")
    elif job_skills and (not missing):
        reasons.append("Cubres todas las skills requeridas")
    if semantic >= 75:
        reasons.append("Alta similitud semántica entre tu CV y la vacante")
    elif semantic >= 55:
        reasons.append(
            "Buena alineación semántica (tu CV ya conversa con los requisitos)"
        )
    if not reasons:
        reasons = [
            "Compatibilidad basada en similitud semántica del perfil y la vacante"
        ]
    reasons.append(f"Habilidades requeridas cubiertas: {round(skill_score, 2)}%")
    reasons.append(f"Afinidad del contexto profesional: {round(semantic, 2)}%")
    return [
        f"score:skills:{round(skill_score, 2)}",
        f"score:semantic:{round(semantic, 2)}",
        *dict.fromkeys(reasons),
    ]


def recommend_category(match_percentage: float, skill_score: float) -> str:
    if match_percentage >= 80 and skill_score >= 50:
        return "alta"
    if match_percentage >= 65:
        return "buenas"
    return "brechas"
