"""Evaluate each study record as a unit, without borrowing another degree's level."""

from app.domain.services.academic_fields import catalog, compare_fields
from app.domain.services.profile_status import is_ongoing


def education_evaluation(profile, job):
    from app.domain.services.professions import LEVEL_RANK, infer_education_level

    details = getattr(job, "quality_details", None) or {}
    policy = details.get("education_field_policy", "related")
    level = getattr(job, "required_education_level", None)
    fields = (
        []
        if level == "secondary"
        else list(getattr(job, "required_study_fields", None) or [])
    )
    accepts_students = level != "secondary" and details.get(
        "education_accepts_in_progress", False
    )
    base = {
        "catalog_version": catalog()["version"],
        "classification_source": catalog()["classification"],
        "policy": policy,
        "required_level": level,
        "accepts_in_progress": accepts_students,
        "requested_fields": fields,
    }
    if not level and not fields:
        return {
            **base,
            "score": None,
            "status": "not_required",
            "comparisons": [],
            "reason": "Esta vacante no exige formación académica.",
        }
    records = getattr(profile, "educations", None) or []
    # A job title or profession alone is not a declared academic record.
    if not records and getattr(profile, "education", None):
        records = [{"degree": str(profile.education)}]
    comparisons = []
    for record in records:
        degree = str(record.get("degree", "") or "").strip()
        actual_level = record.get("level") or infer_education_level(degree)
        ongoing = is_ongoing(record)
        level_status = (
            "not_required"
            if not level
            else "in_progress"
            if ongoing and not accepts_students
            else "unknown"
            if actual_level not in LEVEL_RANK
            else "meets"
            if LEVEL_RANK[actual_level] >= LEVEL_RANK[level]
            else "below"
        )
        level_score = (
            100
            if not level
            else 0
            if level_status in {"in_progress", "unknown"}
            else min(100, LEVEL_RANK[actual_level] / LEVEL_RANK[level] * 100)
        )
        matches = (
            [compare_fields(degree, field, policy) for field in fields]
            if fields
            else [
                {
                    "candidate_degree": degree,
                    "requested_field": None,
                    "status": "not_required",
                    "score": 100,
                    "reason": "Sin restricción de área.",
                }
            ]
        )
        for match in matches:
            score = match["score"]
            if score is not None:
                # A degree in an unrelated area cannot supply a matching academic level.
                score = (
                    round(score * 0.7 + level_score * 0.3, 2)
                    if fields and level and score
                    else score
                    if fields
                    else level_score
                )
            comparisons.append(
                {
                    **match,
                    "score": score,
                    "field_score": match["score"],
                    "level_score": level_score,
                    "level_status": level_status,
                    "actual_level": actual_level,
                    "in_progress": ongoing,
                }
            )
    if not comparisons:
        return {
            **base,
            "score": None,
            "status": "review",
            "comparisons": [],
            "reason": "Falta registrar la formación para poder compararla.",
        }
    best = max(
        comparisons, key=lambda row: row["score"] if row["score"] is not None else -1
    )
    fulfilled = best["score"] == 100 and best["level_status"] not in {
        "unknown",
        "in_progress",
        "below",
    }
    pending = not fulfilled and (
        any(row["score"] is None for row in comparisons)
        or best["level_status"] == "unknown"
    )
    status = (
        "fulfilled"
        if fulfilled
        else "review"
        if pending
        else "partial"
        if best["score"]
        else "not_met"
    )
    # Unknown areas do not become a zero or a positive academic match by default.
    score = None if pending and best["score"] in {None, 0} else best["score"]
    reason = (
        best["reason"]
        if not pending
        else "Hay formación por revisar; no se confirma el cumplimiento académico."
    )
    return {
        **base,
        "score": score,
        "status": status,
        "comparisons": comparisons,
        "selected": best,
        "reason": reason,
    }
