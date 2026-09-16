from app.domain.entities.records import Job, Profile, Recommendation
import re
import unicodedata

from app.domain.services.skills import skill_set

SKILL_WEIGHT = 0.6
SEMANTIC_WEIGHT = 0.4
MIN_CANDIDATE_RECOMMENDATION = 40.0
CONTEXT_STOPWORDS = {
    "para", "como", "con", "del", "las", "los", "una", "uno", "por",
    "que", "sus", "esta", "este", "desde", "entre", "sobre", "cargo",
    "persona", "equipo", "empresa", "experiencia", "años", "ano", "and",
    "the", "de", "en", "el", "la", "y", "o", "un", "se", "al",
}


def _context_tokens(value: str | None) -> set[str]:
    normalized = unicodedata.normalize("NFKD", str(value or "").lower())
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return {
        token
        for token in re.findall(r"[a-z0-9+#.]{3,}", normalized)
        if token not in CONTEXT_STOPWORDS
    }


def _coverage(source: str | None, target: str | None) -> float:
    source_tokens = _context_tokens(source)
    target_tokens = _context_tokens(target)
    if not source_tokens or not target_tokens:
        return 0.0
    return min(100.0, len(source_tokens & target_tokens) / len(target_tokens) * 100)


def professional_context_alignment(profile: Profile, job: Job, semantic: float) -> float:
    """Blend broad text similarity with explicit career evidence."""
    job_text = " ".join(
        filter(None, [job.title, job.description, job.requirements, job.sector])
    )
    roles = " ".join(
        str(item.get("role", "")) for item in (getattr(profile, "experiences", None) or [])
    )
    responsibilities = " ".join(
        str(item.get("description", ""))
        for item in (getattr(profile, "experiences", None) or [])
    )
    education = " ".join(
        str(item.get("degree", ""))
        for item in (getattr(profile, "educations", None) or [])
    )
    certifications = " ".join(
        str(item.get("name", ""))
        for item in (getattr(profile, "certifications", None) or [])
    )
    profession_score = _coverage(getattr(profile, "profession", None), job.title)
    role_score = max(profession_score, _coverage(roles, f"{job.title} {job.requirements}"))
    responsibility_score = _coverage(
        f"{getattr(profile, 'experience', '')} {responsibilities}", job_text
    )
    education_score = _coverage(
        f"{getattr(profile, 'education', '')} {education} {certifications}",
        job.requirements,
    )
    has_structured_context = any(
        str(value or "").strip()
        for value in [
            getattr(profile, "profession", None),
            getattr(profile, "experience", None),
            getattr(profile, "education", None),
            roles,
            responsibilities,
            education,
            certifications,
        ]
    )
    if not has_structured_context:
        return round(semantic, 2)
    score = (
        semantic * 0.45
        + role_score * 0.30
        + responsibility_score * 0.20
        + education_score * 0.05
    )
    preferred_sector = getattr(profile, "preferred_sector", None)
    if preferred_sector and job.sector and preferred_sector == job.sector:
        score = min(100.0, score + 8.0)
    return round(score, 2)


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


def language_coverage(profile, job) -> float | None:
    required = getattr(job, "languages", None) or []
    if not required:
        return None
    levels = {level: index for index, level in enumerate(["A1", "A2", "B1", "B2", "C1", "C2", "NATIVE"], start=1)}
    available = {item["name"]: levels.get(item["level"], 0) for item in getattr(profile, "languages", None) or []}
    return round(sum(min(1.0, available.get(item["name"], 0) / levels[item["level"]]) for item in required) / len(required) * 100, 2)


def combined_match(semantic: float, skill_score: float, language_score: float | None = None) -> float:
    """Transparent score: required skills lead, CV/job context validates fit."""
    if language_score is not None:
        return round(skill_score * SKILL_WEIGHT + semantic * 0.3 + language_score * 0.1, 2)
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
            reasons.append("Tu experiencia y profesión se alinean con el cargo")
    if overlap:
        reasons.append(f"Habilidades que ya cumples: {', '.join(overlap[:7])}")
    if job_skills and missing:
        reasons.append(f"Habilidades por fortalecer: {', '.join(missing[:7])}")
    elif job_skills and (not missing):
        reasons.append("Cumples todas las habilidades requeridas")
    if semantic >= 75:
        reasons.append("Tu experiencia está muy relacionada con las funciones del cargo")
    elif semantic >= 55:
        reasons.append(
            "Tu experiencia se relaciona con varias funciones del cargo"
        )
    experiences = getattr(profile, "experiences", None) or []
    if not experiences:
        reasons.append(
            "Para mejorar: agrega cargos, responsabilidades y logros concretos a tu experiencia"
        )
    elif semantic < 65:
        job_context = _context_tokens(f"{job.title} {job.description} {job.requirements}")
        profile_context = _context_tokens(
            " ".join(
                [
                    str(getattr(profile, "profession", "") or ""),
                    str(getattr(profile, "experience", "") or ""),
                    *[
                        f"{item.get('role', '')} {item.get('description', '')}"
                        for item in experiences
                    ],
                ]
            )
        )
        missing_context = sorted(job_context - profile_context - job_skills)[:5]
        if missing_context:
            reasons.append(
                "Contexto profesional por explicar mejor: "
                + ", ".join(missing_context)
                + ". Incluye ejemplos reales si tienes esa experiencia"
            )
    if not reasons:
        reasons = [
            "Compatibilidad basada en tu experiencia y los requisitos de la vacante"
        ]
    reasons.append(f"Habilidades requeridas cubiertas: {round(skill_score, 2)}%")
    reasons.append(f"Afinidad del contexto profesional: {round(semantic, 2)}%")
    return [
        f"score:skills:{round(skill_score, 2)}",
        f"score:context:{round(semantic, 2)}",
        *dict.fromkeys(reasons),
    ]


def recommend_category(match_percentage: float, skill_score: float) -> str:
    if match_percentage >= 80 and skill_score >= 50:
        return "alta"
    if match_percentage >= 65:
        return "buenas"
    return "brechas"
