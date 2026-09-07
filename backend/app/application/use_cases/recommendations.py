import re
from datetime import datetime

from app.application.errors import UseCaseError
from app.application.ports.services import TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.jobs import ensure_job_access
from app.application.use_cases.matching import (
    rank_candidates_for_job,
    refresh_user_recommendations,
)
from app.domain.entities.records import Recommendation, User


def profile_experience(profile) -> tuple[float | None, str | None]:
    total_years = 0
    roles: list[str] = []
    for item in profile.experiences or []:
        start_match = re.search("\\d{4}", str(item.get("start_year", "")))
        end_value = str(item.get("end_year", ""))
        end_match = re.search("\\d{4}", end_value)
        if item.get("role"):
            roles.append(str(item["role"]))
        if not start_match:
            continue
        start = int(start_match.group())
        end = (
            int(end_match.group())
            if end_match
            else datetime.utcnow().year
            if end_value.lower() in {"presente", "actualidad", "actual", ""}
            else start
        )
        total_years += max(0, end - start)
    summary = ", ".join(roles[:2]) or profile.experience
    return (float(total_years) if total_years else None, summary)


def my_recommended_jobs(
    include_all: bool, current_user: User, db: UnitOfWork, *, nlp: TextAnalysis
) -> list[Recommendation]:
    return refresh_user_recommendations(
        db, current_user, include_all=include_all, nlp=nlp
    )


def ranked_candidates(
    job_id: int, current_user: User, db: UnitOfWork, *, nlp: TextAnalysis
) -> list[dict]:
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    ensure_job_access(db, job, current_user)
    applied_ids = {user_id for (user_id,) in db.applications.candidate_ids(job.id)}
    ranked = []
    for user, percentage in rank_candidates_for_job(db, job, nlp=nlp):
        has_applied = user.id in applied_ids
        if not has_applied and percentage <= 60:
            continue
        years, summary = profile_experience(user.profile)
        ranked.append(
            dict(
                user_id=user.id,
                name=user.name,
                profession=user.profile.profession,
                match_percentage=percentage,
                skills=user.profile.skills or [],
                experience_years=years,
                experience_summary=summary,
                has_applied=has_applied,
            )
        )
    return sorted(
        ranked,
        key=lambda candidate: (
            not candidate["has_applied"],
            -candidate["match_percentage"],
        ),
    )
