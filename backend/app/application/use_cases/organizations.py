import secrets
from datetime import datetime, timedelta
from urllib.parse import quote

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.domain.entities.enums import UserRole
from app.domain.services.authentication import token_digest
from app.domain.services.blind_hiring import candidate_alias, identity_hidden
from app.domain.services.pipeline import stages_for


def context(db, user, *, owner=False):
    company = db.companies.find_by_owner(user.id)
    if company is None:
        raise UseCaseError(status_code=404, detail="No tienes una empresa asociada")
    if owner and company.owner_user_id != user.id:
        raise UseCaseError(status_code=403, detail="Solo el propietario puede administrar el equipo")
    return company


def company_summary(db, user):
    company = context(db, user)
    member = db.organizations.member_for_user(user.id)
    return {"id": company.id, "name": company.name, "nit": company.nit, "role": "owner" if company.owner_user_id == user.id else member.role,
            "verification_status": company.verification_status, "verification_required": company.verification_required,
            "submission": company.verification_submission if company.owner_user_id == user.id else {},
            "feedback": company.verification_feedback, "verification_missing": verification_missing(company.verification_submission)}


def authorize_request(db, user, path, method):
    if user.role != UserRole.COMPANY or path.startswith(("/api/v1/auth/", "/api/v1/account/")):
        return
    if path in {"/api/v1/organization/invitations/accept", "/api/v1/organization/invitation"}:
        return
    if path in {"/api/v1/organization/access", "/api/v1/organization/access-review"}:
        return
    company = context(db, user)
    member = db.organizations.member_for_user(user.id)
    owner = company.owner_user_id == user.id
    if company.verification_status == "suspended" and not path.startswith(("/api/v1/organization/", "/api/v1/trust/")):
        raise UseCaseError(status_code=403, detail="La empresa está suspendida; consulta el estado de verificación")
    if not owner:
        if member is None or not member.active:
            raise UseCaseError(status_code=403, detail="Tu acceso a la empresa fue retirado")
        if path.startswith("/api/v1/companies") and method not in {"GET", "HEAD"}:
            raise UseCaseError(status_code=403, detail="Esta acción requiere al propietario")
        assigned_timeline = path.startswith("/api/v1/workflow/applications/") and (method == "GET" or method == "POST" and path.endswith("/evaluation"))
        if member.role == "interviewer" and not (assigned_timeline or path.startswith(("/api/v1/organization/", "/api/v1/notifications"))):
            raise UseCaseError(status_code=403, detail="Tu acceso se limita a entrevistas asignadas")
    if company.verification_required and company.verification_status != "verified":
        if not path.startswith(("/api/v1/organization/", "/api/v1/companies", "/api/v1/jobs", "/api/v1/notifications", "/api/v1/hiring/quality/", "/api/v1/trust/")):
            raise UseCaseError(status_code=403, detail="La empresa debe verificarse antes de consultar talento")


def submit_verification(db, user, payload):
    company = context(db, user, owner=True)
    if not user.email_verified:
        raise UseCaseError(status_code=403, detail="Confirma primero tu correo en Seguridad")
    if company.verification_status == "verified":
        raise UseCaseError(status_code=409, detail="Este estado requiere revisión administrativa")
    company.verification_required = True
    company.verification_submission = {**payload, "submitted_at": datetime.utcnow().isoformat()}
    suspended = company.verification_status == "suspended"
    if not suspended:
        company.verification_status = "reviewing"
        company.verification_feedback = None
    else:
        admin = db.users.first_admin()
        if admin:
            db.add(db.notifications.new(user_id=admin.id, type="company_verification", title="Empresa suspendida solicita revisión", body=f"{company.name} actualizó sus datos y soportes para revisión.", action_url="/admin/verificaciones"))
    record_event(db, "company.verification_submitted", "company", company.id, actor_user_id=user.id)
    db.commit()
    return company_summary(db, user)


def review_verification(db, admin, company_id, payload):
    if admin.role != UserRole.ADMIN:
        raise UseCaseError(status_code=403, detail="Acceso administrativo requerido")
    company = db.companies.get(company_id)
    if company is None or company.is_external:
        raise UseCaseError(status_code=404, detail="Empresa interna no encontrada")
    if payload["status"] == "verified" and (verification_missing(company.verification_submission) or not company.owner.email_verified):
        raise UseCaseError(status_code=422, detail="Completa los datos y soportes de la solicitud y confirma el correo antes de aprobar")
    previous = company.verification_status
    company.verification_required = True
    company.verification_status = payload["status"]
    company.verification_feedback = payload["feedback"]
    if company.verification_status == "suspended":
        for job in company.jobs:
            if job.status == "active":
                job.status = "paused"
    db.add(db.notifications.new(user_id=company.owner_user_id, type="company_verification", title="Verificación de empresa actualizada",
        body=f"Estado: {company.verification_status}. {payload['feedback']}", action_url="/empresa/equipo"))
    record_event(db, "company.verification_reviewed", "company", company.id, actor_user_id=admin.id,
                 details={"status": company.verification_status, "previous_status": previous})
    db.commit()
    return {"id": company.id, "status": company.verification_status}


def team(db, user):
    company = context(db, user, owner=True)
    result = []
    for member in db.organizations.members(company.id):
        account = db.users.get(member.user_id)
        if account:
            result.append({"id": member.id, "user_id": member.user_id, "name": account.name,
                           "email": account.email, "role": member.role, "active": member.active,
                           "assigned_job_ids": member.assigned_job_ids})
    return result


def _job_ids(db, company, ids):
    for job_id in ids:
        job = db.jobs.get(job_id)
        if job is None or job.company_id != company.id:
            raise UseCaseError(status_code=422, detail="Las asignaciones deben pertenecer a tu empresa")
    return sorted(set(ids))


def invite(db, user, payload, *, app_url, mail_enabled, delivery_mode="local"):
    company = context(db, user, owner=True)
    if not user.email_verified:
        raise UseCaseError(status_code=403, detail="Confirma tu correo antes de invitar")
    if not mail_enabled:
        raise UseCaseError(status_code=503, detail="Correo no configurado")
    token = secrets.token_urlsafe(40)
    ids = _job_ids(db, company, payload["assigned_job_ids"])
    db.add(db.organizations.new_invitation(company_id=company.id, email=payload["email"].casefold(), role=payload["role"],
        assigned_job_ids=ids, token_hash=token_digest(token), expires_at=datetime.utcnow() + timedelta(days=3)))
    link = f"{app_url.rstrip('/')}/equipo/invitacion?token={quote(token)}"
    db.add(db.accounts.new_message(recipient=payload["email"].casefold(), subject=f"Invitación a {company.name}",
        delivery_state=delivery_mode, expires_at=datetime.utcnow() + timedelta(days=3),
        body=f"Te invitaron como {payload['role']} a {company.name}. Abre {link}\nVence en 3 días. Confirma tu correo antes de aceptar."))
    record_event(db, "company.member_invited", "company", company.id, actor_user_id=user.id, details={"role": payload["role"]})
    db.commit()
    return {"message": "Invitación preparada para enviar por correo"}


def invitations(db, user):
    company = context(db, user, owner=True)
    now = datetime.utcnow()
    return [{"id": row.id, "email": row.email, "role": row.role, "assigned_job_ids": row.assigned_job_ids,
             "expires_at": row.expires_at, "status": "accepted" if row.used_at else "expired" if row.expires_at <= now else "pending"}
            for row in db.organizations.invitations(company.id)]


def cancel_invitation(db, user, invitation_id):
    company = context(db, user, owner=True)
    if not db.organizations.cancel_invitation(company.id, invitation_id):
        raise UseCaseError(status_code=404, detail="Invitación pendiente no encontrada")
    record_event(db, "company.invitation_cancelled", "company", company.id, actor_user_id=user.id)
    db.commit()
    return {"message": "Invitación cancelada; el enlace dejó de ser válido"}


def invitation_info(db, token):
    row = db.organizations.invitation(token_digest(token))
    if row is None or row.used_at or row.expires_at <= datetime.utcnow():
        raise UseCaseError(status_code=404, detail="Invitación no disponible")
    company = db.companies.get(row.company_id)
    return {"company": company.name, "role": row.role}


def accept_invitation(db, user, token):
    if user.role != UserRole.COMPANY or not user.email_verified:
        raise UseCaseError(status_code=403, detail="Usa una cuenta empresarial con correo confirmado")
    row = db.organizations.invitation(token_digest(token))
    if row is None or row.email != user.email.casefold() or row.used_at or row.expires_at <= datetime.utcnow():
        raise UseCaseError(status_code=404, detail="Invitación no disponible para esta cuenta")
    existing = db.companies.find_by_owner(user.id)
    if existing and existing.id != row.company_id:
        raise UseCaseError(status_code=409, detail="Esta cuenta ya pertenece a otra empresa")
    member = db.organizations.member_for_user(user.id)
    if member and member.company_id != row.company_id:
        raise UseCaseError(status_code=409, detail="Esta cuenta ya tiene una membresía")
    if not db.organizations.consume_invitation(row.id):
        raise UseCaseError(status_code=409, detail="La invitación ya fue utilizada")
    if member is None:
        member = db.organizations.new_member(company_id=row.company_id, user_id=user.id, role=row.role,
                                             assigned_job_ids=row.assigned_job_ids, active=True)
        db.add(member)
    else:
        member.active = True
        member.role = row.role
        member.assigned_job_ids = row.assigned_job_ids
    record_event(db, "company.member_joined", "company", row.company_id, actor_user_id=user.id, details={"role": row.role})
    db.commit()
    return {"message": "Ya formas parte del equipo"}


def update_member(db, user, member_id, payload):
    company = context(db, user, owner=True)
    member = next((row for row in db.organizations.members(company.id) if row.id == member_id), None)
    if member is None:
        raise UseCaseError(status_code=404, detail="Miembro no encontrado")
    member.role = payload["role"]
    member.active = payload["active"]
    member.assigned_job_ids = _job_ids(db, company, payload["assigned_job_ids"])
    db.accounts.revoke_sessions(member.user_id)
    record_event(db, "company.member_updated", "company", company.id, actor_user_id=user.id, details={"role": member.role})
    db.commit()
    return {"message": "Permisos actualizados y sesiones anteriores cerradas"}


def assignments(db, user):
    company = context(db, user)
    if company.verification_status == "suspended" or (company.verification_required and company.verification_status != "verified"):
        raise UseCaseError(status_code=403, detail="La empresa debe estar verificada para consultar postulaciones")
    member = db.organizations.member_for_user(user.id)
    allowed = set(member.assigned_job_ids) if member and member.role == "interviewer" else {job.id for job in company.jobs}
    return [{"job_id": job.id, "title": job.title, "modality": job.modality, "status": job.status,
             "applications": [{"id": row.id, "candidate_alias": candidate_alias(job.id, row.user_id) if identity_hidden(job, row) else row.user.name, "interview_at": row.interview_at,
                               "stage": row.pipeline_stage, "stage_title": next((stage["title"] for stage in stages_for(job) if stage["id"] == row.pipeline_stage), row.pipeline_stage), "status": row.status.value, "released_at": row.released_at} for row in job.applications]}
            for job in company.jobs if job.id in allowed]


def verification_queue(db):
    return [{"id": row.id, "name": row.name, "nit": row.nit, "status": row.verification_status,
             "submission": row.verification_submission, "feedback": row.verification_feedback, "email_verified": row.owner.email_verified, "verification_missing": verification_missing(row.verification_submission)}
            for row in db.organizations.verification_queue()]


VERIFICATION_FIELDS = {"legal_name": "Razón social", "tax_id": "Identificación tributaria", "business_activity": "Actividad de la empresa",
    "address": "Dirección", "city": "Ciudad", "contact_email": "Correo de contacto", "contact_phone": "Teléfono",
    "representative_name": "Nombre del representante", "representative_role": "Cargo del representante",
    "registry_authority": "Entidad de registro", "registry_reference": "Referencia del registro",
    "registry_document_url": "Soporte del registro", "accuracy_confirmed": "Declaración de veracidad"}


def verification_missing(submission):
    return [label for key, label in VERIFICATION_FIELDS.items() if not (submission or {}).get(key)]


def access_status(db, user):
    member = db.organizations.member_for_user(user.id)
    company = db.companies.get(member.company_id) if member else db.companies.find_by_owner(user.id)
    if company is None:
        return {"active": True, "role": "owner", "company_name": None, "verification_status": "pending", "feedback": None}
    return {"active": member.active if member else True, "role": member.role if member else "owner",
            "company_name": company.name, "verification_status": company.verification_status,
            "feedback": company.verification_feedback}


def request_access_review(db, user, message):
    member = db.organizations.member_for_user(user.id)
    if member is None or member.active:
        raise UseCaseError(status_code=409, detail="Esta solicitud corresponde a un acceso retirado")
    company = db.companies.get(member.company_id)
    previous = [row for row in db.events.for_entity("company_access", member.id) if row.event_type == "company.access_review_requested"]
    if previous and previous[0].created_at > datetime.utcnow() - timedelta(hours=24):
        raise UseCaseError(status_code=409, detail="Tu aviso ya fue enviado. Puedes enviar otro después de 24 horas")
    db.add(db.notifications.new(user_id=company.owner_user_id, type="team_access", title="Solicitud de revisión de acceso",
        body=f"{user.name} solicita revisar su acceso retirado: {message}", action_url="/empresa/equipo#equipo"))
    record_event(db, "company.access_review_requested", "company_access", member.id, actor_user_id=user.id)
    db.commit()
    return {"message": "Aviso enviado al propietario. Tu acceso seguirá retirado hasta que lo reactive."}
