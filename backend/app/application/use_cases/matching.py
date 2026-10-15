from datetime import datetime

from app.application.ports.services import TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.personalization import order as personalize
from app.domain.entities.records import Job, Recommendation, User
from app.domain.services.languages import LEVELS, language_levels
from app.domain.services.match_explanations import (
    explain,
    input_version,
    preference_alignment,
)
from app.domain.services.matching import (
    combined_match,
    is_relevant_candidate_recommendation,
    language_coverage,
    professional_context_alignment,
    recommend_category,
    recommendation_reasons,
)
from app.domain.services.matching_text import professional_sections
from app.domain.services.professions import (
    education_match,
    required_certification_match,
)
from app.domain.services.reputation import company_health
from app.domain.services.requirement_analysis import (
    relevant_experience,
    requirement_rows,
    requirement_score,
)
from app.domain.services.skills import skill_set
from app.domain.services.writing_context import (
    original_context_profile,
)

_UNSET = object()


def commit_scores(db):
    if hasattr(db, "commit_retaining_state"):
        db.commit_retaining_state()
    else:
        db.commit()


def prepare_scores(nlp, pairs):
    if hasattr(nlp, "prepare_matching"):
        def texts():
            for profile, job in pairs:
                original = original_context_profile(profile)
                for source in [profile, *([original] if original is not None else [])]:
                    for _, _, left, right, _ in professional_sections(source, job):
                        if left:
                            yield left
                            yield right
        nlp.prepare_matching(texts())


def candidate_match(profile, job, *, nlp):
    return _candidate_match(profile, job, nlp=nlp)[0]


def _context_analysis(profile, job, nlp):
    sections = []
    pairs = professional_sections(profile, job)
    total = sum(item[4] for item in pairs) or 1
    for key, label, left, right, weight in pairs:
        if not left:
            score = 0
        elif hasattr(nlp, "matching_similarity"):
            score = nlp.matching_similarity(left, right, None if hasattr(nlp, "prepare_matching") else nlp.embed(right))
        else:
            score = nlp.similarity_percentage(nlp.embed(left), nlp.embed(right))
        sections.append({"key": key, "label": label, "score": round(score, 2), "weight": round(weight / total, 4), "has_candidate_data": bool(left)})
    raw_semantic = sum(row["score"] * row["weight"] for row in sections)
    context_score = professional_context_alignment(profile, job, raw_semantic)
    return context_score, sections


def _candidate_match(profile, job, *, nlp):
    context_score, sections = _context_analysis(profile, job, nlp)
    original = original_context_profile(profile)
    retained_context = False
    if original is not None:
        source_score, source_sections = _context_analysis(original, job, nlp)
        retained_context = source_score > context_score
        if retained_context:
            context_score, sections = source_score, source_sections
    rows = requirement_rows(profile, job)
    if original is not None:
        source_rows = {row["key"]: row for row in requirement_rows(original, job)}
        for index, row in enumerate(rows):
            source_row = source_rows[row["key"]]
            if source_row["score"] > row["score"] and row["status"] != "not_met" and "contradictoria" not in row["reason"]:
                rows[index] = {**source_row, "reason": source_row["reason"] + " Respaldada por el texto original de la propuesta aplicada."}
                retained_context = True
    skill_score = requirement_score(rows)
    experience = relevant_experience(profile, job)
    if original is not None:
        source_experience = relevant_experience(original, job)
        if source_experience["related_months"] > experience["related_months"]:
            experience = source_experience
            retained_context = True
    if experience["required_months"]:
        context_score = round(context_score * .8 + (experience["score"] or 0) * .2, 2)
    language_score = language_coverage(profile, job)
    education_score = education_match(profile, job)
    certification_score = required_certification_match(profile, job)
    percentage = combined_match(context_score, skill_score, language_score, education_score, certification_score)
    confidence = 100.0
    if getattr(job, "source_kind", "internal") == "external":
        confidence = external_data_confidence(job)
        percentage = combined_match(context_score, skill_score, language_score, education_score, certification_score)
        # A short provider summary must never look as certain as a complete
        # TalentSync vacancy. Low data quality only lowers the score.
        percentage *= 0.75 + confidence / 400
        percentage = round(min(100.0, percentage), 2)
    return (percentage, context_score, skill_score, language_score, confidence, education_score, certification_score), {"section_scores": sections, "experience_details": experience, "requirement_details": rows, "retained_writing_context": retained_context}


def external_data_confidence(job) -> float:
    skills = list(dict.fromkeys(getattr(job, "skills", None) or []))
    description = str(getattr(job, "description", "") or "")
    skill_signal = min(1.0, len(skills) / 8)
    text_signal = min(1.0, len(description) / 1_200)
    return round(40 + skill_signal * 35 + text_signal * 25, 2)


def upsert_recommendation(
    db: UnitOfWork,
    user: User,
    job: Job,
    *,
    nlp: TextAnalysis,
    commit_result: bool = True,
    cached=_UNSET,
) -> Recommendation:
    if user.profile is None:
        raise ValueError("El candidato no tiene perfil profesional")
    scores, analysis = _candidate_match(
        user.profile, job, nlp=nlp
    )
    percentage, context_score, skill_score, language_score, confidence, education_score, certification_score = scores
    recommendation = db.recommendations.find_for_user_job(user.id, job.id) if cached is _UNSET else cached
    if recommendation is None:
        recommendation = db.recommendations.new(
            user_id=user.id, job_id=job.id, match_percentage=percentage
        )
        db.add(recommendation)
    recommendation.match_percentage = percentage
    recommendation.created_at = datetime.utcnow()
    recommendation.match_details = explain(user.profile, job, context=context_score, skills=skill_score, language=language_score,
        education=education_score, certifications=certification_score, confidence=confidence, percentage=percentage,
        text_method=getattr(nlp, "match_method", "lexical-hashing-v1"), **analysis)
    recommendation.reasons = recommendation_reasons(
        user.profile, job, semantic=context_score, skill_score=skill_score, education_score=education_score, certification_score=certification_score,
        requirement_details=analysis["requirement_details"]
    )
    if language_score is not None:
        available = language_levels(user.profile.languages)
        language_reasons = [f"score:languages:{language_score}"]
        for name, level in language_levels(job.languages).items():
            item = {"name": name, "level": level}
            actual = available.get(name, "sin registrar")
            required_label = "Nativo" if item["level"] == "NATIVE" else item["level"]
            actual_label = "Nativo" if actual == "NATIVE" else actual
            if LEVELS.get(actual, 0) >= LEVELS[level]:
                language_reasons.append(f"Cumples el idioma solicitado: {item['name']} (mínimo {required_label}, tu nivel {actual_label})")
            else:
                language_reasons.append(f"Idioma por fortalecer: {item['name']} (mínimo {required_label}, tu nivel {actual_label}). Registra tu nivel real o mejora hasta el nivel solicitado")
        recommendation.reasons = recommendation.reasons + language_reasons
    recommendation.reasons = [
        f"categoria:{recommend_category(percentage, skill_score)}"
    ] + recommendation.reasons
    if getattr(job, "source_kind", "internal") == "external":
        recommendation.reasons = [
            "source:external",
            f"confidence:data:{confidence}",
            (
                "Compatibilidad estimada con la información disponible en la "
                "publicación externa"
            ),
            *recommendation.reasons,
        ]
    if commit_result:
        db.commit()
        db.refresh(recommendation)
    return recommendation


def refresh_user_recommendations(
    db: UnitOfWork, user: User, include_all: bool, *, nlp: TextAnalysis,
    batch_size: int | None = None, progress: dict | None = None,
) -> list[Recommendation]:
    jobs = db.jobs.active_for_matching() if hasattr(db.jobs, "active_for_matching") else db.jobs.active()
    existing = db.recommendations.for_user_active(user.id)
    by_job = {item.job_id: item for item in existing}
    job_map = {job.id: job for job in jobs}
    method = getattr(nlp, "match_method", "lexical-hashing-v1")
    versions = {job.id: input_version(user.profile, job, method) for job in jobs}
    stale = [job for job in jobs if job.id not in by_job
             or (getattr(by_job[job.id], "match_details", None) or {}).get("input_version") != versions[job.id]]
    # Inputs include the model version and current month (ongoing experience).
    # Recalculate after a real change, rather than expiring every ten minutes or
    # invalidating all scores when only the photo/design has been edited.
    if batch_size is not None:
        known = skill_set(user.profile.skills)
        stale.sort(key=lambda job: (-len(known & skill_set(job.skills)), job.id))
    selected = stale if batch_size is None else stale[:batch_size]
    for start in range(0, len(selected), 24):
        batch = selected[start:start + 24]
        prepare_scores(nlp, ((user.profile, job) for job in batch))
        for job in batch:
            by_job[job.id] = upsert_recommendation(db, user, job, nlp=nlp, commit_result=False, cached=by_job.get(job.id))
    if selected:
        commit_scores(db)
    remaining = len(stale) - len(selected)
    if progress is not None:
        progress.update(pending=remaining, total=len(jobs))
    recommendations = sorted((row for job_id, row in by_job.items() if job_id in versions
        and (row.match_details or {}).get("input_version") == versions[job_id]), key=lambda item: item.match_percentage, reverse=True)
    # Preference flags filter results; they do not change professional scores.
    # Refresh their presentation without scheduling another model evaluation.
    for row in recommendations:
        preferences = preference_alignment(user.profile, job_map[row.job_id])
        row.match_details = {**row.match_details, "preferences": preferences, "candidate_interest_score": preferences["score"]}
    if include_all:
        return personalize(db, user, sorted(recommendations, key=lambda item: (company_health(job_map[item.job_id].company)["visibility_reduced"], -item.match_percentage)))
    recommendations = sorted(
        (
            item
            for item in recommendations
            if is_relevant_candidate_recommendation(
                item, user.profile, job_map[item.job_id]
            )
        ),
        key=lambda item: item.match_percentage,
        reverse=True,
    )
    recommendations = personalize(db, user, recommendations)
    diverse_recommendations: list[Recommendation] = []
    used_skill_tokens: set[str] = set()
    for recommendation in recommendations:
        job = job_map[recommendation.job_id]
        job_tokens = skill_set((job.skills or [])[:8]) if job else set()
        overlap = len(job_tokens.intersection(used_skill_tokens))
        if overlap <= 3:
            diverse_recommendations.append(recommendation)
            used_skill_tokens |= job_tokens
        if len(diverse_recommendations) >= 50:
            break
    return diverse_recommendations


def rank_candidates_for_job(
    db: UnitOfWork, job: Job, *, nlp: TextAnalysis, user_ids: set[int] | None = None,
    batch_size: int | None = None, progress: dict | None = None,
    eligible_only: bool = False, keep_user_ids: set[int] | None = None,
) -> list[tuple[User, float]]:
    users = db.users.candidates_for_ids(user_ids) if user_ids is not None and hasattr(db.users, "candidates_for_ids") else [user for user in db.users.candidates_with_profiles() if user_ids is None or user.id in user_ids]
    if eligible_only:
        from app.domain.services.work_preferences import employer_preference_conflicts
        users = [user for user in users if user.profile and (user.id in (keep_user_ids or set()) or not employer_preference_conflicts(user.profile, job))]
    method = getattr(nlp, "match_method", "lexical-hashing-v1")
    existing = {row.user_id: row for row in db.recommendations.for_job(job.id)} if hasattr(db.recommendations, "for_job") else {
        user.id: db.recommendations.find_for_user_job(user.id, job.id) for user in users}
    versions = {user.id: input_version(user.profile, job, method) for user in users if user.profile}
    stale = [user for user in users if user.profile and (existing.get(user.id) is None
        or (existing[user.id].match_details or {}).get("input_version") != versions[user.id])]
    if batch_size is not None:
        required = skill_set(job.skills)
        stale.sort(key=lambda user: (-len(required & skill_set(user.profile.skills)), user.id))
    selected = stale if batch_size is None else stale[:batch_size]
    for start in range(0, len(selected), 24):
        batch = selected[start:start + 24]
        prepare_scores(nlp, ((user.profile, job) for user in batch))
        for user in batch:
            existing[user.id] = upsert_recommendation(db, user, job, nlp=nlp, commit_result=False, cached=existing.get(user.id))
    if selected:
        commit_scores(db)
    if progress is not None:
        progress.update(pending=len(stale) - len(selected), pool_total=len(users))
    return sorted([(user, existing[user.id].match_percentage) for user in users if user.profile and user.id in existing and (existing[user.id].match_details or {}).get("input_version") == versions[user.id]
        and (not eligible_only or user.id in (keep_user_ids or set()) or is_relevant_candidate_recommendation(existing[user.id], user.profile, job))], key=lambda item: item[1], reverse=True)
