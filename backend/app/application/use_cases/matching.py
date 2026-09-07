from app.application.ports.services import TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.records import Job, Recommendation, User
from app.domain.services.matching import (
    combined_match,
    is_relevant_candidate_recommendation,
    recommend_category,
    recommendation_reasons,
    required_skill_coverage,
)
from app.domain.services.skills import skill_set


def upsert_recommendation(
    db: UnitOfWork, user: User, job: Job, *, nlp: TextAnalysis
) -> Recommendation:
    if user.profile is None:
        raise ValueError("El candidato no tiene perfil profesional")
    semantic = nlp.similarity_percentage(user.profile.embedding, job.embedding)
    skill_score = required_skill_coverage(user.profile.skills, job.skills)
    percentage = combined_match(semantic, skill_score)
    recommendation = db.recommendations.find_for_user_job(user.id, job.id)
    if recommendation is None:
        recommendation = db.recommendations.new(
            user_id=user.id, job_id=job.id, match_percentage=percentage
        )
        db.add(recommendation)
    recommendation.match_percentage = percentage
    recommendation.reasons = recommendation_reasons(
        user.profile, job, semantic=semantic, skill_score=skill_score
    )
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
        if user.profile and user.profile.embedding:
            semantic = nlp.similarity_percentage(user.profile.embedding, job.embedding)
            skill_score = required_skill_coverage(user.profile.skills, job.skills)
            percentage = combined_match(semantic, skill_score)
            ranked.append((user, percentage))
    return sorted(ranked, key=lambda item: item[1], reverse=True)
