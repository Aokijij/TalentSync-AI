from datetime import datetime
from uuid import uuid4

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.application.use_cases.jobs import match_current_candidate
from app.domain.services.credential_links import certificate_url
from app.domain.services.skills import normalize_skills
from app.domain.services.work_preferences import effective_preferences


def add_certificate(profile, item):
    if item.get("kind") != "certificate":
        return
    certificate = {"id": item["id"], "name": item["title"], "issuer": item.get("issuer", ""),
                   "year": item.get("year", ""), "url": certificate_url(item.get("url")),
                   "description": item["description"], "source": "external_certificate", "evidence_id": item["id"]}
    profile.certifications = [row for row in profile.certifications or [] if row.get("evidence_id") != item["id"]] + [certificate]


def preferences(db, user, payload=None):
    if payload is not None:
        db.profiles.lock_owner(user.id)
        db.refresh(user.profile)
        # Keep older API clients working by writing their values to the profile.
        # Current clients send only the three requirement flags.
        if "minimum_salary" in payload:
            user.profile.desired_salary = payload["minimum_salary"]
        if "modalities" in payload:
            user.profile.preferred_modality = next(iter(payload["modalities"]), None)
        if "locations" in payload:
            user.profile.location = next(iter(payload["locations"]), None)
        user.profile.preferences = {
            **(user.profile.preferences or {}),
            **{key: bool((user.profile.preferences or {}).get(key, False)) for key in (
                "salary_required", "modality_required", "location_required"
            )},
            **{key: value for key, value in payload.items() if key.endswith("_required")},
        }
        user.profile.updated_at = datetime.utcnow()
        record_event(db, "profile.preferences_changed", "profile", user.profile.id, actor_user_id=user.id)
        db.commit()
    return effective_preferences(user.profile)


def evidence(db, user, payload=None, *, analysis=None):
    items = user.profile.evidence or []
    if payload is not None:
        if len(items) >= 50:
            raise UseCaseError(status_code=422, detail="Puedes registrar hasta 50 evidencias")
        item = {**payload, "id": uuid4().hex, "created_at": datetime.utcnow().isoformat(), "verified": False}
        if analysis is not None:
            item["analysis"] = analysis
        if payload.get("add_to_profile"):
            add_certificate(user.profile, item)
            skills = normalize_skills([*(user.profile.skills or []), *payload["skills"]])
            if len(skills) > 100:
                raise UseCaseError(status_code=422, detail="Tu perfil admite hasta cien habilidades")
            user.profile.skills = skills
        user.profile.evidence = [*items, item]
        user.profile.updated_at = datetime.utcnow()
        record_event(db, "profile.evidence_added", "profile", user.profile.id, actor_user_id=user.id, details={"source": payload["kind"]})
        db.commit()
    return user.profile.evidence or []


def edit_evidence_text(db, user, evidence_id, payload):
    db.profiles.lock_owner(user.id)
    db.refresh(user.profile)
    rows = user.profile.evidence or []
    item = next((row for row in rows if row["id"] == evidence_id), None)
    if item is None:
        raise UseCaseError(status_code=404, detail="Evidencia no encontrada")
    # Edit only the candidate's text, preserving the imported reference and analysis.
    text = {"title": payload["title"], "description": payload["description"]}
    user.profile.evidence = [{**row, **text} if row["id"] == evidence_id else row for row in rows]
    if item.get("kind") == "certificate":
        user.profile.certifications = [
            {**row, "name": text["title"], "description": text["description"]}
            if row.get("evidence_id") == evidence_id else row
            for row in user.profile.certifications or []
        ]
    user.profile.updated_at = datetime.utcnow()
    record_event(db, "profile.evidence_edited", "profile", user.profile.id, actor_user_id=user.id)
    db.commit()
    return user.profile.evidence


def remove_evidence(db, user, evidence_id):
    rows = user.profile.evidence or []
    if not any(row["id"] == evidence_id for row in rows):
        raise UseCaseError(status_code=404, detail="Evidencia no encontrada")
    user.profile.evidence = [row for row in rows if row["id"] != evidence_id]
    user.profile.updated_at = datetime.utcnow()
    record_event(db, "profile.evidence_removed", "profile", user.profile.id, actor_user_id=user.id)
    db.commit()


def add_evidence_skills(db, user, evidence_id):
    rows = user.profile.evidence or []
    evidence = next((row for row in rows if row["id"] == evidence_id), None)
    if evidence is None:
        raise UseCaseError(status_code=404, detail="Evidencia no encontrada")
    db.learning.lock_owner(user.id)
    add_certificate(user.profile, evidence)
    skills = normalize_skills([*(user.profile.skills or []), *evidence.get("skills", [])])
    if len(skills) > 100:
        raise UseCaseError(status_code=422, detail="Tu perfil admite hasta cien habilidades")
    user.profile.skills = skills
    user.profile.evidence = [{**row, "add_to_profile": True} if row["id"] == evidence_id else row for row in rows]
    user.profile.updated_at = datetime.utcnow()
    record_event(db, "profile.evidence_skills_added", "profile", user.profile.id, actor_user_id=user.id, details={"source": "declared"})
    db.commit()
    return user.profile.evidence


def match_details(db, user, job_id, nlp):
    return match_current_candidate(job_id, user, db, nlp=nlp).match_details
