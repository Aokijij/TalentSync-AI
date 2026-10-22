from copy import deepcopy
from datetime import datetime
from hashlib import sha256
from types import SimpleNamespace
from uuid import uuid4

from app.application.errors import UseCaseError
from app.application.use_cases.career_coach import (
    available_job,
    owner_profile,
    save,
    state,
)
from app.application.use_cases.workflow import accessible_application
from app.domain.entities.enums import UserRole
from app.domain.services.application_preparation import (
    answer_review,
    interview_questions,
    job_snapshot,
    preparation_revision,
    resume_profile,
    source_version,
    suggested_skills,
)
from app.domain.services.blind_hiring import identity_hidden
from app.domain.services.career_coach import fingerprint
from app.domain.services.resume_filename import resume_filename


def version_view(row):
    return {"id": row.id, "job_id": row.job_id, "created_at": row.created_at,
            "filename": row.filename, "sha256": row.pdf_sha256,
            "summary": row.snapshot["profile"].get("experience") or "",
            "skills": row.snapshot["profile"].get("skills") or [],
            "experiences": row.snapshot["profile"].get("experiences") or [],
            "style": row.snapshot["profile"].get("resume_style"),
            "source_version": row.source_version}


def preparation(db, user, job_id, *, application_id=None):
    profile = resume_profile(owner_profile(user))
    application = None
    if application_id is not None:
        application = accessible_application(db, user, application_id)
        if application.user_id != user.id or application.job_id != job_id:
            raise UseCaseError(status_code=404, detail="Postulación no encontrada")
        job = application.job
    else:
        job = available_job(db, job_id)
    submitted = (application.coach_snapshot or {}) if application else {}
    facts = deepcopy(submitted.get("profile") or profile)
    if submitted.get("intro") is not None:
        facts["experience"] = submitted["intro"]
    offer = deepcopy(submitted.get("job") or job_snapshot(job))
    _, content = state(db, user)
    note = content.get("interview_notes", {}).get(str(job_id), {})
    questions = interview_questions(facts, offer, saved_question_ids=note.get("answers", {}))
    revision = preparation_revision(facts, offer)
    known = {question["id"] for question in questions}
    answers = {key: value for key, value in note.get("answers", {}).items() if key in known}
    return {"job": offer, "source": "submitted" if submitted.get("profile") else "current",
            "source_version": source_version(user), "job_version": fingerprint(offer), "revision": revision,
            "profile": {"profession": profile.get("profession"), "summary": profile.get("experience") or "", "experiences": profile.get("experiences") or [], "skills": suggested_skills(profile, offer)},
            "versions": [version_view(row) for row in db.resume_versions.for_job(user.id, job_id)],
            "submitted_resume_id": submitted.get("resume_version_id"),
            "interview": {"questions": questions, "answers": answers, "version": note.get("version", 0),
                "outdated": bool(note and note.get("revision") != revision), "saved_at": note.get("updated_at"),
                "reviews": {row["id"]: answer_review(answers.get(row["id"], {})) for row in questions},
                "ask_company": ["¿Qué resultados esperan de esta persona durante los primeros tres meses?", "¿Cómo se organiza el equipo y con quién trabajaría?", "¿Cuáles son los siguientes pasos y el plazo de respuesta?"]}}


def create_version(db, user, job_id, payload, exporter):
    owner_profile(user)
    digest = fingerprint({"job_id": job_id, "payload": payload})
    previous = db.resume_versions.find_request(user.id, payload["request_key"])
    if previous:
        if previous.request_digest != digest:
            raise UseCaseError(status_code=409, detail="Esta solicitud ya guardó otra versión. Revisa la versión existente")
        return version_view(previous)
    job = available_job(db, job_id)
    db.profiles.lock_owner(user.id)
    db.refresh(user.profile)
    previous = db.resume_versions.find_request(user.id, payload["request_key"])
    if previous:
        if previous.request_digest != digest:
            raise UseCaseError(status_code=409, detail="Esta solicitud ya guardó otra versión")
        return version_view(previous)
    if source_version(user) != payload["source_version"]:
        raise UseCaseError(status_code=409, detail="Tu perfil cambió. Actualiza la preparación antes de guardar el CV")
    if fingerprint(job_snapshot(job)) != payload["job_version"]:
        raise UseCaseError(status_code=409, detail="La oferta cambió. Actualiza la preparación y revisa sus requisitos antes de guardar el CV")
    if db.resume_versions.count_for_job(user.id, job_id) >= 30:
        raise UseCaseError(status_code=409, detail="Ya tienes 30 versiones para esta vacante. Puedes reutilizar una versión guardada")
    profile = resume_profile(user.profile)
    indices = payload.get("experience_indices")
    if indices is not None:
        records = profile.get("experiences") or []
        if len(indices) != len(set(indices)) or any(index < 0 or index >= len(records) for index in indices):
            raise UseCaseError(status_code=422, detail="Selecciona experiencias que existan en tu perfil, sin repetirlas")
        profile["experiences"] = [records[index] for index in indices]
    skills = payload.get("skills")
    if skills is not None:
        available = set(profile.get("skills") or [])
        if len(skills) != len(set(skills)) or any(skill not in available for skill in skills):
            raise UseCaseError(status_code=422, detail="El CV solo puede incluir habilidades guardadas en tu perfil")
        profile["skills"] = skills
    else:
        profile["skills"] = suggested_skills(profile, job_snapshot(job))
    if payload.get("summary") is not None:
        profile["experience"] = payload["summary"].strip()
    profile["resume_style"] = payload["style"]
    include_photo = payload["include_photo"]
    document = SimpleNamespace(name=user.name, email=user.email, profile=SimpleNamespace(**profile))
    pdf = exporter(document, include_photo=include_photo)
    if len(pdf) > 5_000_000:
        raise UseCaseError(status_code=422, detail="El PDF supera el límite de 5 MB. Prueba sin foto")
    row = db.resume_versions.new(id=uuid4().hex, user_id=user.id, job_id=job_id,
        request_key=payload["request_key"], request_digest=digest, source_version=payload["source_version"],
        snapshot={"schema": 2, "name": user.name, "email": user.email, "profile": profile, "job": job_snapshot(job), "include_photo": include_photo},
        filename=resume_filename(user.name), pdf_sha256=sha256(pdf).hexdigest(), pdf=pdf)
    db.add(row); db.commit(); db.refresh(row)
    return version_view(row)


def owned_version(db, user, version_id):
    row = db.resume_versions.get(version_id)
    if row is None or row.user_id != user.id:
        raise UseCaseError(status_code=404, detail="Versión no encontrada")
    return row


def for_application(db, user, application_id):
    application = accessible_application(db, user, application_id)
    return preparation(db, user, application.job_id, application_id=application_id)


def save_application_interview(db, user, application_id, payload):
    application = accessible_application(db, user, application_id)
    return save_interview(db, user, application.job_id, payload, application_id=application_id)


def submitted_resume(db, user, application_id):
    application = accessible_application(db, user, application_id)
    if user.role != UserRole.CANDIDATE and user.role != UserRole.ADMIN and identity_hidden(application.job, application):
        raise UseCaseError(status_code=403, detail="El CV estará disponible cuando se revele la identidad en este proceso")
    version_id = (application.coach_snapshot or {}).get("resume_version_id")
    row = db.resume_versions.get(version_id) if version_id else None
    if row is None or row.user_id != application.user_id or row.job_id != application.job_id:
        raise UseCaseError(status_code=404, detail="Esta postulación no tiene un PDF guardado")
    return row


def save_interview(db, user, job_id, payload, *, application_id=None):
    row, content = state(db, user, locked=True)
    pack = preparation(db, user, job_id, application_id=application_id)
    notes = content.get("interview_notes", {})
    previous = notes.get(str(job_id), {})
    if previous.get("version", 0) != payload["expected_version"] or pack["revision"] != payload["revision"]:
        raise UseCaseError(status_code=409, detail="La preparación cambió en otra ventana. Recarga antes de guardar; conserva tus respuestas")
    known = {question["id"] for question in pack["interview"]["questions"]}
    if set(payload["answers"]) - known:
        raise UseCaseError(status_code=422, detail="Hay respuestas para preguntas que no pertenecen a esta preparación")
    note = {"version": previous.get("version", 0) + 1, "revision": pack["revision"],
            "answers": payload["answers"], "updated_at": datetime.utcnow().isoformat() + "Z"}
    content["interview_notes"] = {**notes, str(job_id): note}
    save(db, row, content)
    return {**note, "reviews": {key: answer_review(answer) for key, answer in note["answers"].items()}}
