import unicodedata
from copy import deepcopy
from datetime import datetime

from app.application.errors import UseCaseError
from app.application.ports.services import TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.jobs import ensure_job_access
from app.application.use_cases.matching import (
    rank_candidates_for_job,
    refresh_user_recommendations,
    upsert_recommendation,
)
from app.domain.entities.enums import UserRole
from app.domain.entities.records import Notification, Recommendation, User
from app.domain.services.blind_hiring import candidate_alias, identity_hidden
from app.domain.services.experience_dates import experience_months
from app.domain.services.match_explanations import requirements_for
from app.domain.services.skill_levels import declared_skill_levels
from app.domain.services.skills import skill_gap
from app.domain.services.work_preferences import (
    employer_preference_conflicts,
    location_fit,
)


def profile_experience(profile) -> tuple[float | None, str | None]:
    total_years = round(experience_months(profile.experiences) / 12, 2)
    roles = [str(item["role"]) for item in profile.experiences or [] if item.get("role")]
    summary = ", ".join(roles[:2]) or profile.experience
    return (float(total_years) if total_years else None, summary)


def my_recommended_jobs(
    include_all: bool, current_user: User, db: UnitOfWork, *, nlp: TextAnalysis
) -> list[Recommendation]:
    return refresh_user_recommendations(
        db, current_user, include_all=include_all, nlp=nlp
    )


def my_recommended_jobs_batch(current_user, db, *, nlp, batch_size, gate):
    progress = {}
    with gate(current_user.id) as acquired:
        try:
            items = refresh_user_recommendations(db, current_user, include_all=True, nlp=nlp,
                batch_size=batch_size if acquired else 0, progress=progress)
        except UseCaseError as error:
            if error.status_code != 409:
                raise
            # Another scorer committed this pair meanwhile. Its cache is now
            # available; do not repeat inference or fail the whole page.
            items = refresh_user_recommendations(db, current_user, include_all=True, nlp=nlp,
                batch_size=0, progress=progress)
    return {"items": items, **progress}


def ranked_candidates(
    job_id: int,
    current_user: User,
    db: UnitOfWork,
    *,
    nlp: TextAnalysis,
    minimum_match: float = 50,
    audience: str = "all",
    query: str | None = None,
    batch_size: int | None = None, progress: dict | None = None,
) -> list[dict]:
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    ensure_job_access(db, job, current_user)
    applied_ids = {user_id for (user_id,) in db.applications.candidate_ids(job.id)}
    ranked = []
    users = rank_candidates_for_job(db, job, nlp=nlp, user_ids=applied_ids if audience == "applied" else None, batch_size=batch_size, progress=progress, eligible_only=True, keep_user_ids=applied_ids)
    applications = {row.user_id: row for row in db.applications.for_job(job.id)}
    user_ids = {user.id for user, _ in users}
    invitations = db.notifications.pending_invitation_ids(user_ids, f"/vacantes/{job.id}")
    foundations = {}
    shared_ids = {user.id for user, _ in users if (user.privacy_preferences or {}).get("share_evidence", True)}
    for row in db.learning.valid_foundations_for_users(shared_ids, datetime.utcnow()):
        foundations.setdefault(row.user_id, []).append({"skill": row.skill, "score": row.score, "level": "fundamentals", "valid_until": row.valid_until})
    for user, percentage in users:
        professional_percentage = percentage
        fit = location_fit(user.profile, job)
        percentage = round(percentage * fit["factor"], 2)
        has_applied = user.id in applied_ids
        application = applications.get(user.id)
        if audience == "applied" and not has_applied:
            continue
        if audience == "invite" and (has_applied or percentage < minimum_match):
            continue
        if audience == "all" and not has_applied and percentage < minimum_match:
            continue
        years, summary = profile_experience(user.profile)
        hidden = current_user.role != UserRole.ADMIN and identity_hidden(job, application)
        gaps = [row for row in skill_gap(user.profile.skills, requirements_for(job)) if not row["covered"]]
        related = [{"skill": row["skill"], "foundations": row["foundations"]} for row in gaps if row["foundations"]]
        validated = foundations.get(user.id, [])
        candidate = dict(
                user_id=user.id,
                name=candidate_alias(job.id, user.id) if hidden else user.name,
                identity_hidden=hidden,
                related_skills=related,
                validated_foundations=validated,
                profession=user.profile.profession,
                professional_match_percentage=professional_percentage,
                location_fit=fit,
                experience_months=experience_months(user.profile.experiences),
                match_percentage=(max(0.0, min(100.0, percentage + (application.screening_adjustment or 0))) if application else percentage),
                skills=user.profile.skills or [],
                skill_levels=declared_skill_levels(user.profile),
                languages=user.profile.languages or [],
                experience_years=years,
                experience_summary=None if hidden else summary,
                has_applied=has_applied,
                has_pending_invitation=user.id in invitations,
                application_id=application.id if application else None,
                screening_answers=application.screening_answers if application and not hidden else [],
                screening_adjustment=(application.screening_adjustment or 0)
                if application
                else 0,
                base_match_percentage=percentage if application else None,
                adjusted_match_percentage=(
                    max(
                        0.0,
                        min(
                            100.0,
                            percentage + (application.screening_adjustment or 0),
                        ),
                    )
                    if application
                    else None
                ),
            )
        if audience == "invite" and candidate["match_percentage"] < minimum_match:
            continue
        if query:
            searchable = " ".join(
                [
                    candidate["name"],
                    candidate["profession"] or "",
                    " ".join(candidate["skills"]),
                ]
            ).casefold()
            fold = lambda text: "".join(char for char in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(char))
            if not all(term in fold(searchable) for term in fold(query).split()):
                continue
        ranked.append(candidate)
    return sorted(
        ranked,
        key=lambda candidate: (
            not candidate["has_applied"],
            -candidate["match_percentage"],
        ),
    )


def ranked_candidates_batch(job_id, current_user, db, *, nlp, gate, batch_size, **filters):
    progress = {}
    with gate(("company-job", job_id)) as acquired:
        try:
            items = ranked_candidates(job_id, current_user, db, nlp=nlp, batch_size=batch_size if acquired else 0, progress=progress, **filters)
        except UseCaseError as error:
            if error.status_code != 409:
                raise
            items = ranked_candidates(job_id, current_user, db, nlp=nlp, batch_size=0, progress=progress, **filters)
    return items, progress


def candidate_explanation(job_id, user_id, current_user, db, *, nlp):
    from app.application.use_cases.jobs import match_current_candidate
    from app.application.use_cases.profiles import get_candidate_profile
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    ensure_job_access(db, job, current_user)
    visible = get_candidate_profile(user_id, current_user, db, job_id=job_id)
    candidate = db.users.get(user_id)
    recommendation = match_current_candidate(job_id, candidate, db, nlp=nlp)
    details = deepcopy(recommendation.match_details)
    if visible.get("identity_hidden") or not (candidate.privacy_preferences or {}).get("share_evidence", True):
        for row in details.get("requirements", []):
            row["evidence"] = []
    fit = location_fit(candidate.profile, job)
    professional = recommendation.match_percentage
    base = round(professional * fit["factor"], 2)
    application = db.applications.find_for_user_job(user_id, job_id)
    adjustment = (application.screening_adjustment or 0) if application else 0
    return {"user_id": user_id, "job_id": job_id, "match_percentage": max(0, min(100, base + adjustment)),
            "base_match_percentage": base, "professional_match_percentage": professional, "screening_adjustment": adjustment,
            "match_details": details, "location_fit": fit}


def invite_candidate(
    job_id: int,
    user_id: int,
    current_user: User,
    db: UnitOfWork,
    *,
    nlp: TextAnalysis,
) -> Notification:
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    ensure_job_access(db, job, current_user)
    candidate = db.users.get(user_id)
    if (
        candidate is None
        or candidate.role != UserRole.CANDIDATE
        or candidate.profile is None
    ):
        raise UseCaseError(status_code=404, detail="Candidato no encontrado")
    if db.applications.find_for_user_job(user_id, job_id):
        raise UseCaseError(
            status_code=409, detail="El candidato ya se postuló a esta vacante"
        )
    recommendation = upsert_recommendation(db, candidate, job, nlp=nlp)
    conflicts = employer_preference_conflicts(candidate.profile, job)
    if conflicts:
        raise UseCaseError(status_code=422, detail=". ".join(conflicts) + ". Respeta las preferencias del candidato.")
    if recommendation.match_percentage < 50:
        raise UseCaseError(
            status_code=422,
            detail="La invitación requiere al menos 50% de compatibilidad",
        )
    action_url = f"/vacantes/{job.id}"
    existing = db.notifications.find_unread(
        user_id, "candidate_invitation", action_url
    )
    if existing:
        return existing
    notification = db.notifications.new(
        user_id=user_id,
        type="candidate_invitation",
        title=f"{job.company.name} te invita a postularte",
        body=(
            f"Tu perfil tiene {recommendation.match_percentage:.0f}% de compatibilidad "
            f"con {job.title}. Revisa las condiciones y decide si deseas postularte."
        ),
        action_url=action_url,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
