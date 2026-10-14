from copy import deepcopy
from datetime import datetime
from uuid import uuid4

from app.application.errors import UseCaseError
from app.application.use_cases.learning_resources import resources
from app.domain.services.career_coach import (
    demand_report,
    fingerprint,
    job_version,
    select_jobs,
    snapshot,
    star_text,
    vacancy_projection,
)


def owner_profile(user):
    if user.profile is None:
        raise UseCaseError(status_code=404, detail="Completa primero tu perfil")
    return user.profile


def state(db, user, *, locked=False):
    profile = owner_profile(user)
    if locked:
        db.profiles.lock_owner(user.id)
        db.refresh(profile)
    row = db.profiles.coach_state(user.id)
    if row is None:
        row = db.profiles.new_coach_state(user.id)
        if locked:
            db.add(row)
            db.flush()
    elif locked:
        db.refresh(row)
    return row, deepcopy(row.content or {"writing": [], "drafts": []})


def overview(db, user):
    _, data = state(db, user)
    submitted = [{"application_id": item.id, "job_id": item.job_id, "created_at": item.created_at.isoformat() + "Z", **deepcopy(item.coach_snapshot)}
                 for item in db.applications.for_user(user.id) if item.coach_snapshot][:20]
    return {**data, "submitted": submitted, "source_version": fingerprint(snapshot(user.profile)), "experiences": user.profile.experiences or []}


def save(db, row, data):
    row.content = data
    db.add(row)
    db.commit()


def prepare_writing(db, user, payload):
    row, data = state(db, user, locked=True)
    profile = user.profile
    if payload["source_version"] != fingerprint(snapshot(profile)):
        raise UseCaseError(status_code=409, detail="El perfil cambió; actualiza antes de preparar la propuesta")
    index = payload["experience_index"]
    if index >= len(profile.experiences or []):
        raise UseCaseError(status_code=404, detail="Experiencia no encontrada")
    try:
        text = star_text(payload["facts"])
    except ValueError as error:
        raise UseCaseError(status_code=422, detail=str(error)) from None
    record = deepcopy(profile.experiences[index])
    proposal = {"id": uuid4().hex, "index": index, "record": record, "before": record.get("description") or "", "after": text,
                "status": "prepared", "created_at": datetime.utcnow().isoformat() + "Z"}
    data["writing"] = [proposal, *data.get("writing", [])][:20]
    save(db, row, data)
    return proposal


def decide_writing(db, user, proposal_id, payload):
    row, data = state(db, user, locked=True)
    proposal = next((item for item in data.get("writing", []) if item["id"] == proposal_id), None)
    if proposal is None:
        raise UseCaseError(status_code=404, detail="Propuesta no encontrada")
    applying = payload["action"] == "apply"
    if proposal["status"] != ("prepared" if applying else "applied"):
        raise UseCaseError(status_code=409, detail="La propuesta ya cambió de estado")
    records = deepcopy(user.profile.experiences or [])
    index = proposal["index"]
    expected = proposal["record"] if applying else {**proposal["record"], "description": proposal["after"]}
    if index >= len(records) or records[index] != expected:
        raise UseCaseError(status_code=409, detail="La experiencia cambió; no se sobrescribió tu texto")
    if applying and payload.get("text") is not None:
        proposal["after"] = payload["text"].strip()
        if not proposal["after"]:
            raise UseCaseError(status_code=422, detail="Escribe una propuesta antes de aplicarla")
    records[index]["description"] = proposal["after"] if applying else proposal["before"]
    user.profile.experiences = records
    db.add(user.profile)
    proposal["status"] = "applied" if applying else "undone"
    save(db, row, data)
    return proposal


def available_job(db, job_id):
    job = db.jobs.get(job_id)
    if job is None or job.status != "active" or job.expires_at and job.expires_at < datetime.utcnow():
        raise UseCaseError(status_code=404, detail="La vacante no está disponible")
    return job


def prepare_draft(db, user, job_id):
    job = available_job(db, job_id)
    row, data = state(db, user, locked=True)
    projection = vacancy_projection(user.profile, job)
    draft = {"id": uuid4().hex, "job_id": job.id, "job_title": job.title, "revision": 1, "confirmed": False,
             "source_version": fingerprint(snapshot(user.profile)), "job_version": job_version(job),
             "created_at": datetime.utcnow().isoformat() + "Z", **projection}
    data["drafts"] = [draft, *data.get("drafts", [])][:20]
    save(db, row, data)
    return draft


def own_draft(db, user, draft_id):
    _, data = state(db, user)
    draft = next((item for item in data.get("drafts", []) if item["id"] == draft_id), None)
    if draft is None:
        raise UseCaseError(status_code=404, detail="Versión no encontrada")
    return draft


def update_draft(db, user, draft_id, payload):
    row, data = state(db, user, locked=True)
    draft = next((item for item in data.get("drafts", []) if item["id"] == draft_id), None)
    if draft is None:
        raise UseCaseError(status_code=404, detail="Versión no encontrada")
    if draft["revision"] != payload["revision"]:
        raise UseCaseError(status_code=409, detail="La versión cambió; actualiza antes de guardar")
    if draft["source_version"] != fingerprint(snapshot(user.profile)) or draft["job_version"] != job_version(available_job(db, draft["job_id"])):
        raise UseCaseError(status_code=409, detail="El perfil o la vacante cambió; prepara una nueva versión")
    draft.update(intro=payload["intro"].strip(), confirmed=True, revision=draft["revision"] + 1)
    if not draft["intro"]:
        raise UseCaseError(status_code=422, detail="La presentación no puede estar vacía")
    save(db, row, data)
    return draft


def application_snapshot(db, user, job, draft_id):
    draft = own_draft(db, user, draft_id)
    if draft["job_id"] != job.id or not draft["confirmed"]:
        raise UseCaseError(status_code=422, detail="Selecciona una versión revisada para esta vacante")
    if draft["source_version"] != fingerprint(snapshot(user.profile)) or draft["job_version"] != job_version(job):
        raise UseCaseError(status_code=409, detail="Tu perfil o la vacante cambió; prepara y revisa una nueva versión")
    return {"draft_id": draft["id"], "job_title": draft["job_title"], "intro": draft["intro"], "profile": deepcopy(draft["profile"])}


def radar(db, user, search="", sector="", location=""):
    return demand_report(owner_profile(user), db.jobs.active(), resources(db), search, sector, location)


def jobs(db, search=""):
    matches = select_jobs(db.jobs.active(), search, recent_days=None)
    return {"total": len(matches), "items": [{"id": job.id, "title": job.title, "location": job.location} for job in matches[:30]]}
