from app.application.ports.services import TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.records import Job, Recommendation, User
from app.domain.services.matching import (
    combined_match,
    is_relevant_candidate_recommendation,
    recommend_category,
    recommendation_reasons,
    required_skill_coverage,
    professional_context_alignment,
    language_coverage,
)
from app.domain.services.skills import skill_set


def candidate_match(profile, job, *, nlp):
    raw_semantic = nlp.similarity_percentage(profile.embedding, job.embedding)
    context_score = professional_context_alignment(profile, job, raw_semantic)
    skill_score = required_skill_coverage(profile.skills, job.skills)
    language_score = language_coverage(profile, job)
    return combined_match(context_score, skill_score, language_score), context_score, skill_score, language_score


def upsert_recommendation(
    db: UnitOfWork, user: User, job: Job, *, nlp: TextAnalysis
) -> Recommendation:
    if user.profile is None:
        raise ValueError("El candidato no tiene perfil profesional")
    percentage, context_score, skill_score, language_score = candidate_match(user.profile, job, nlp=nlp)
    recommendation = db.recommendations.find_for_user_job(user.id, job.id)
    if recommendation is None:
        recommendation = db.recommendations.new(
            user_id=user.id, job_id=job.id, match_percentage=percentage
        )
        db.add(recommendation)
    recommendation.match_percentage = percentage
    recommendation.reasons = recommendation_reasons(
        user.profile, job, semantic=context_score, skill_score=skill_score
    )
    if language_score is not None:
        available = {item["name"]: item["level"] for item in user.profile.languages or []}
        language_reasons = [f"score:languages:{language_score}"]
        levels = {level: index for index, level in enumerate(["A1", "A2", "B1", "B2", "C1", "C2", "NATIVE"], start=1)}
        for item in job.languages:
            actual = available.get(item["name"], "sin registrar")
            required_label = "Nativo" if item["level"] == "NATIVE" else item["level"]
            actual_label = "Nativo" if actual == "NATIVE" else actual
            if levels.get(actual, 0) >= levels[item["level"]]:
                language_reasons.append(f"Cumples el idioma solicitado: {item['name']} (mínimo {required_label}, tu nivel {actual_label})")
            else:
                language_reasons.append(f"Idioma por fortalecer: {item['name']} (mínimo {required_label}, tu nivel {actual_label}). Registra tu nivel real o mejora hasta el nivel solicitado")
        recommendation.reasons = recommendation.reasons + language_reasons
    recommendation.reasons = [
        f"categoria:{recommend_category(percentage, skill_score)}"
    ] + recommendation.reasons
    db.commit()
    db.refresh(recommendation)
    return recommendation


def refresh_user_recommendations(
    db: UnitOfWork, user: User, include_all: bool, *, nlp: TextAnalysis
) -> list[Recommendation]:
    jobs = db.jobs.active()
    recommendations = sorted(
        [upsert_recommendation(db, user, job, nlp=nlp) for job in jobs],
        key=lambda item: item.match_percentage,
        reverse=True,
    )
    if include_all:
        return recommendations
    recommendations = sorted(
        (
            item
            for item in recommendations
            if is_relevant_candidate_recommendation(
                item, user.profile, db.jobs.get(item.job_id)
            )
        ),
        key=lambda item: item.match_percentage,
        reverse=True,
    )
    diverse_recommendations: list[Recommendation] = []
    used_skill_tokens: set[str] = set()
    for recommendation in recommendations:
        job = db.jobs.get(recommendation.job_id)
        job_tokens = skill_set((job.skills or [])[:8]) if job else set()
        overlap = len(job_tokens.intersection(used_skill_tokens))
        if overlap <= 3:
            diverse_recommendations.append(recommendation)
            used_skill_tokens |= job_tokens
        if len(diverse_recommendations) >= 50:
            break
    return diverse_recommendations


def rank_candidates_for_job(
    db: UnitOfWork, job: Job, *, nlp: TextAnalysis
) -> list[tuple[User, float]]:
    users = db.users.candidates_with_profiles()
    ranked: list[tuple[User, float]] = []
    for user in users:
        if user.profile:
            percentage, _, _, _ = candidate_match(user.profile, job, nlp=nlp)
            ranked.append((user, percentage))
    return sorted(ranked, key=lambda item: item[1], reverse=True)
