"""Bounded operational records and persistent publication decisions."""
from datetime import datetime, timedelta

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.domain.entities.enums import UserRole
from app.domain.services.editorial_jobs import (
    apply_editorial,
    exclusion_key,
    source_value,
)
from app.domain.services.external_job_content import admission_reasons
from app.domain.services.job_freshness import (
    FRESH_HOURS,
    externally_available,
    verification_method,
)
from app.domain.services.offer_review import review_offer
from app.domain.services.skills import normalize_skills


def require_admin(user):
    if user.role != UserRole.ADMIN:
        raise UseCaseError(403, "Esta función requiere acceso administrativo")


def job_detail(db, user, job_id):
    require_admin(user)
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(404, "Vacante no encontrada")
    fields = ("id", "title", "description", "requirements", "salary", "location", "department", "modality", "employment_type", "sector", "status", "benefits", "skills", "skill_requirements", "languages", "required_education_level", "required_study_fields", "created_at", "expires_at", "source_kind", "source_name", "external_url", "external_published_at", "external_checked_at", "external_check_state", "external_check_reason", "external_available", "external_admission_reasons", "source_portal", "quality_details", "response_days", "moderation_status", "moderation_note", "moderation_revision", "editorial_overrides")
    data = {key: getattr(job, key, None) for key in fields}
    for key in ("external_verification_method", "external_manual_verified_at", "external_manual_verified_until", "external_manual_verified_by", "external_manual_note"):
        data[key] = getattr(job, key, None)
    data.update(company_id=job.company_id, company_name=job.company.name if job.company else "", applications_count=len(job.applications))
    if job.source_kind == "external":
        now = datetime.utcnow()
        recent = verification_method(job, now) != "unconfirmed"
        checks = [
            {"label": "Vacante habilitada en el catálogo", "passed": job.status == "active"},
            {"label": "Vigencia confirmada recientemente", "passed": recent},
            {"label": "Fecha de publicación y habilidades suficientes", "passed": not admission_reasons(job.external_published_at, job.skills, now=now)},
            {"label": "Funciones y requisitos claros", "passed": bool(((job.external_content or {}).get("admission") or {}).get("clarity_passed"))},
            {"label": "Dentro del plazo de la oferta", "passed": not job.expires_at or job.expires_at > now},
        ]
        data["review"] = {"checks": checks, "can_publish": all(row["passed"] for row in checks), "can_activate": all(row["passed"] for row in checks[1:]), "score": None}
    else:
        review = review_offer(job)
        checks = [{"label": row["label"], "passed": row["passed"]} for row in review["checks"]]
        checks.extend({"label": row["message"], "passed": False} for row in review["issues"] if row["severity"] == "critical")
        company_ready = bool(job.company and (not job.company.verification_required or job.company.verification_status == "verified"))
        checks.append({"label": "Empresa habilitada para publicar", "passed": company_ready})
        data["review"] = {"checks": checks, "can_publish": review["can_publish"] and company_ready, "score": review["score"]}
    data["history"] = [{"id": row.id, "event": row.event_type, "created_at": row.created_at, "actor_user_id": row.actor_user_id, "details": row.details} for row in db.events.for_entity("job", job.id, limit=20)]
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
    data["logo_url"] = record.logo_url
    data["cover_url"] = record.cover_url
    data["jobs"] = [{"id": item.id, "title": item.title, "status": item.status, "applications_count": len(item.applications)} for item in sorted(record.jobs, key=lambda item: item.id, reverse=True)[:30]]
    data["jobs_count"] = len(record.jobs)
    return data


def edit_external_content(db, user, job_id, payload, *, nlp):
    require_admin(user)
    job = db.jobs.get(job_id)
    if job is None or job.source_kind != "external":
        raise UseCaseError(404, "Vacante externa no encontrada")
    db.jobs.lock(job)
    if job.moderation_revision != payload["revision"]:
        raise UseCaseError(409, "La ficha cambió. Actualiza antes de guardar el contenido")
    if exclusion_key(str(payload["source_url"])) != exclusion_key(job.external_url):
        raise UseCaseError(422, "El complemento debe referenciar la oferta original de esta vacante")
    fields = dict(payload["fields"])
    if not fields:
        raise UseCaseError(422, "Indica al menos un campo para complementar")
    if "skills" in fields:
        fields["skills"] = normalize_skills(fields["skills"])
    if "skills" in fields and "skill_requirements" in fields and set(fields["skills"]) != {row["skill"] for row in fields["skill_requirements"]}:
        raise UseCaseError(422, "Las habilidades y los requisitos estructurados deben coincidir")
    if "skills" in fields and "skill_requirements" not in fields:
        existing = {row["skill"]: row for row in (job.skill_requirements or [])}
        fields["skill_requirements"] = [existing.get(name, {"skill": name, "essential": False, "weight": 1, "level": "unspecified"}) for name in fields["skills"]]
    previous = job.editorial_overrides or {}
    if "quality_details" in fields:
        quality = fields["quality_details"]
        if "experience_months" in quality:
            quality["experience_years"] = None
        fields["quality_details"] = {**previous.get("fields", {}).get("quality_details", {}), **quality}
    if "skill_requirements" in fields:
        fields["skills"] = [row["skill"] for row in fields["skill_requirements"]]
    source = dict(previous.get("source") or {})
    for key in fields:
        if key not in source:
            source[key] = source_value(getattr(job, key))
    metadata = {"fields": {**previous.get("fields", {}), **fields}, "source": source,
                "source_url": job.external_url, "note": payload["note"], "reviewed_at": datetime.utcnow().isoformat() + "Z"}
    if not db.jobs.update_editorial(job.id, payload["revision"], metadata):
        raise UseCaseError(409, "Otra revisión se guardó primero. Actualiza la ficha")
    db.refresh(job)
    apply_editorial(job)
    maximum = (job.quality_details or {}).get("salary_max")
    if maximum is not None and job.salary is not None and maximum < job.salary:
        raise UseCaseError(422, "El salario máximo debe ser mayor o igual al salario base")
    job.embedding = nlp.analyze_job(f"{job.title} {job.description} {job.requirements}").embedding
    record_event(db, "job.content_reviewed", "job", job.id, actor_user_id=user.id,
                 details={"version": job.moderation_revision, "source": "original_listing"})
    db.commit()
    return job_detail(db, user, job.id)


def cleanup_reason(job, *, now=None):
    now = now or datetime.utcnow()
    if job.source_kind != "external" or job.applications:
        return None
    if job.status == "active" and externally_available(job, now):
        return None
    if job.status == "closed" or job.external_check_state == "closed":
        return "closed_at_source"
    if job.expires_at and job.expires_at <= now:
        return "expired"
    if "publication_too_old" in admission_reasons(job.external_published_at, job.skills, now=now):
        return "old_publication"
    if not job.external_url:
        return "missing_original_url"
    if len((job.description or "").strip()) < 40 and len((job.requirements or "").strip()) < 20:
        return "empty_content"
    return None


def catalog_cleanup_preview(db, user):
    require_admin(user)
    rows = []
    for job in db.jobs.external_listings():
        reason = cleanup_reason(job)
        if reason:
            rows.append({"id": job.id, "title": job.title, "company_name": job.company.name if job.company else "",
                         "reason": reason, "external_url": job.external_url})
    return {"total": len(rows), "items": rows[:200], "protected": "Los fallos temporales y las ofertas incompletas con fuente válida se conservan para revisión."}


def catalog_cleanup(db, user, ids):
    require_admin(user)
    deleted, skipped = [], []
    for job_id in dict.fromkeys(ids):
        job = db.jobs.get(job_id)
        if job is None:
            skipped.append(job_id)
            continue
        db.jobs.lock(job)
        reason = cleanup_reason(job)
        if not reason:
            skipped.append(job_id)
            continue
        if job.external_url:
            db.jobs.exclude_external(exclusion_key(job.external_url), source_name=job.source_name,
                                    external_id=job.external_id, external_url=job.external_url,
                                    reason=reason, actor_user_id=user.id)
        record_event(db, "job.catalog_removed", "job", job.id, actor_user_id=user.id, details={"reason_code": reason})
        db.delete(job)
        deleted.append(job_id)
    db.commit()
    return {"deleted": len(deleted), "deleted_ids": deleted, "skipped": skipped}


def change_external_status(db, user, job_id, payload):
    require_admin(user)
    job = db.jobs.get(job_id)
    if job is None or job.source_kind != "external":
        raise UseCaseError(404, "Vacante externa no encontrada")
    db.jobs.lock(job)
    if job.moderation_revision != payload["revision"]:
        raise UseCaseError(409, "La ficha cambió. Actualiza antes de cambiar el estado")
    apply_editorial(job)
    manual = payload.get("manual_verification")
    if manual:
        if payload["status"] != "active" or manual.get("confirmed_open") is not True:
            raise UseCaseError(422, "La revisión manual de vigencia debe confirmar la fuente al publicar")
        if exclusion_key(str(manual["source_url"])) != exclusion_key(job.external_url):
            raise UseCaseError(422, "Debes revisar la oferta original de esta vacante")
        now = datetime.utcnow()
        job.external_manual_verified_at = now
        job.external_manual_verified_until = now + timedelta(hours=FRESH_HOURS)
        job.external_manual_verified_by = user.id
        job.external_manual_source_url = job.external_url
        job.external_manual_note = manual["note"]
        # Persist inside the same transaction before CAS refresh; errors roll
        # back both the review and the publication decision.
        db.flush()
    if payload["status"] == "active" and not externally_available(job, ignore_moderation=True):
        detail = job_detail(db, user, job_id)
        missing = [row["label"] for row in detail["review"]["checks"][1:] if not row["passed"]]
        raise UseCaseError(422, "Antes de publicar, revisa: " + "; ".join(missing))
    previous = job.status
    metadata = {**(job.editorial_overrides or {}), "catalog_status": payload["status"]}
    if not db.jobs.update_editorial(job.id, payload["revision"], metadata):
        raise UseCaseError(409, "Otra revisión se guardó primero. Actualiza la ficha")
    db.refresh(job)
    job.status = payload["status"]
    job.moderation_status = "approved" if job.status == "active" else "held"
    job.moderation_note = payload["note"]
    if manual:
        record_event(db, "job.manual_verified", "job", job.id, actor_user_id=user.id,
                     details={"source": "original_listing", "version": job.moderation_revision,
                              "deadline": job.external_manual_verified_until.isoformat() + "Z"})
    record_event(db, "job.status_updated", "job", job.id, actor_user_id=user.id,
                 details={"previous_status": previous, "status": job.status, "version": job.moderation_revision})
    db.commit()
    return job_detail(db, user, job.id)
