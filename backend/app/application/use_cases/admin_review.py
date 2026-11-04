"""Bounded operational records and persistent publication decisions."""
from datetime import datetime, timedelta

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.domain.entities.enums import UserRole
from app.domain.services.external_job_content import admission_reasons
from app.domain.services.job_freshness import FRESH_HOURS, externally_available
from app.domain.services.offer_review import review_offer


def require_admin(user):
    if user.role != UserRole.ADMIN:
        raise UseCaseError(403, "Esta función requiere acceso administrativo")


def job_detail(db, user, job_id):
    require_admin(user)
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(404, "Vacante no encontrada")
    fields = ("id", "title", "description", "requirements", "salary", "location", "department", "modality", "employment_type", "sector", "status", "benefits", "skills", "skill_requirements", "languages", "required_education_level", "required_study_fields", "created_at", "expires_at", "source_kind", "source_name", "external_url", "external_published_at", "external_checked_at", "external_check_state", "external_check_reason", "external_available", "external_admission_reasons", "source_portal", "quality_details", "response_days", "moderation_status", "moderation_note", "moderation_revision")
    data = {key: getattr(job, key, None) for key in fields}
    data.update(company_id=job.company_id, company_name=job.company.name if job.company else "", applications_count=len(job.applications))
    if job.source_kind == "external":
        now = datetime.utcnow()
        recent = bool(job.external_verified_at and job.external_verified_at >= now - timedelta(hours=FRESH_HOURS))
        checks = [
            {"label": "Oferta activa en la fuente", "passed": job.status == "active"},
            {"label": "Vigencia confirmada recientemente", "passed": recent and job.external_check_state == "verified"},
            {"label": "Fecha de publicación y habilidades suficientes", "passed": not admission_reasons(job.external_published_at, job.skills, now=now)},
            {"label": "Funciones, requisitos, experiencia y formación claros", "passed": bool(((job.external_content or {}).get("admission") or {}).get("clarity_passed"))},
            {"label": "Dentro del plazo de la oferta", "passed": not job.expires_at or job.expires_at > now},
        ]
        data["review"] = {"checks": checks, "can_publish": all(row["passed"] for row in checks), "score": None}
    else:
        review = review_offer(job)
        checks = [{"label": row["label"], "passed": row["passed"]} for row in review["checks"]]
        checks.extend({"label": row["message"], "passed": False} for row in review["issues"] if row["severity"] == "critical")
        company_ready = bool(job.company and (not job.company.verification_required or job.company.verification_status == "verified"))
        checks.append({"label": "Empresa habilitada para publicar", "passed": company_ready})
        data["review"] = {"checks": checks, "can_publish": review["can_publish"] and company_ready, "score": review["score"]}
    data["history"] = [{"id": row.id, "event": row.event_type, "created_at": row.created_at, "details": row.details} for row in db.events.for_entity("job", job.id, limit=20)]
    return data


def review_publication(db, user, job_id, payload):
    require_admin(user)
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(404, "Vacante no encontrada")
    if job.source_kind != "external":
        raise UseCaseError(422, "Gestiona el estado de esta vacante desde sus controles de publicación")
    if payload["revision"] != job.moderation_revision:
        raise UseCaseError(409, "La revisión cambió. Actualiza la ficha antes de guardar")
    if payload["status"] == "approved" and (job.status != "active" or not externally_available(job, ignore_moderation=True)):
        raise UseCaseError(422, "La oferta aún no cumple la vigencia y claridad requeridas. Consulta los puntos pendientes de la ficha")
    previous = job.moderation_status
    if not db.jobs.update_moderation(job.id, payload["revision"], payload["status"], payload["note"]):
        raise UseCaseError(409, "Otra revisión se guardó primero. Actualiza la ficha")
    record_event(db, "job.publication_reviewed", "job", job.id, actor_user_id=user.id,
                 details={"status": payload["status"], "previous_status": previous, "version": payload["revision"] + 1})
    db.commit()
    db.refresh(job)
    return job_detail(db, user, job_id)


def user_detail(db, user, user_id):
    require_admin(user)
    record = db.users.get(user_id)
    if record is None:
        raise UseCaseError(404, "Cuenta no encontrada")
    profile = record.profile
    return {"id": record.id, "name": record.name, "email": record.email, "role": record.role.value,
            "created_at": record.created_at, "email_verified": record.email_verified, "mfa_enabled": record.mfa_enabled,
            "registration_pending": record.registration_pending,
            "profile": {"profession": profile.profession, "location": profile.location, "department": profile.department,
                        "skills": profile.skills or [], "summary": profile.experience,
                        "experiences_count": len(profile.experiences or []), "educations_count": len(profile.educations or []),
                        "certifications_count": len(profile.certifications or []), "languages": profile.languages or [],
                        "has_cv": bool(profile.cv_filename)} if profile else None,
            "applications": [{"id": item.id, "job_id": item.job_id, "job_title": item.job.title if item.job else "", "status": item.status.value, "created_at": item.created_at} for item in sorted(record.applications, key=lambda item: item.id, reverse=True)[:20]]}


def company_detail(db, user, company_id):
    require_admin(user)
    record = db.companies.get(company_id)
    if record is None:
        raise UseCaseError(404, "Empresa no encontrada")
    fields = ("id", "name", "description", "sector", "size", "location", "website", "mission", "values", "benefits", "is_external", "source_name", "verification_status", "verification_required")
    data = {key: getattr(record, key, None) for key in fields}
    data["nit"] = None if record.is_external else record.nit
    data["owner_email"] = record.owner.email if record.owner else None
    data["jobs"] = [{"id": item.id, "title": item.title, "status": item.status, "applications_count": len(item.applications)} for item in sorted(record.jobs, key=lambda item: item.id, reverse=True)[:30]]
    data["jobs_count"] = len(record.jobs)
    return data
