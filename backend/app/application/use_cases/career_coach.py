from copy import deepcopy
from datetime import datetime
from uuid import uuid4

from app.application.errors import UseCaseError
from app.application.use_cases.learning_resources import resources
from app.domain.services.career_coach import (
    demand_report,
    fingerprint,
    snapshot,
    star_text,
)
from app.domain.services.career_writing import validate_generated_text


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
    return {"writing": data.get("writing", []), "source_version": fingerprint(snapshot(user.profile)), "experiences": user.profile.experiences or []}


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


def generate_writing(db, user, payload, *, writer=None):
    profile = owner_profile(user)
    if payload["source_version"] != fingerprint(snapshot(profile)):
        raise UseCaseError(status_code=409, detail="Tu perfil cambió. Actualiza y vuelve a generar la propuesta")
    index = payload["experience_index"]
    if index >= len(profile.experiences or []):
        raise UseCaseError(status_code=404, detail="Experiencia no encontrada")
    record = deepcopy(profile.experiences[index])
    if not str(record.get("description") or "").strip():
        raise UseCaseError(status_code=422, detail="Escribe primero una frase sobre lo que hiciste en esta experiencia")
    if writer is None:
        raise UseCaseError(status_code=503, detail="La IA local todavía no está preparada. No se conectará una API de pago")
    try:
        generated = validate_generated_text(writer.generate(record, style=payload["style"], result=payload["result"]), record, payload["result"])
    except ValueError as error:
        raise UseCaseError(status_code=422, detail=str(error)) from None
    row, data = state(db, user, locked=True)
    if payload["source_version"] != fingerprint(snapshot(user.profile)):
        raise UseCaseError(status_code=409, detail="Editaste el perfil mientras se preparaba la propuesta. Genera otra con tu información actualizada")
    proposal = {"id": uuid4().hex, "index": index, "record": record, "before": record.get("description") or "", "after": generated.pop("text"),
                "status": "prepared", "created_at": datetime.utcnow().isoformat() + "Z", **generated}
    data["writing"] = [proposal, *data.get("writing", [])][:20]
    save(db, row, data)
    return proposal


def available_job(db, job_id):
    job = db.jobs.get(job_id)
    if job is None or job.status != "active" or job.expires_at and job.expires_at < datetime.utcnow():
        raise UseCaseError(status_code=404, detail="La vacante no está disponible")
    return job


def vacancy_advice(db, user, job_id):
    from app.domain.services.requirement_analysis import requirement_rows
    profile = owner_profile(user)
    job = available_job(db, job_id)
    rows = requirement_rows(profile, job)
    supported = [row["skill"] for row in rows if row["covered"]]
    review = [row["skill"] for row in rows if not row["covered"]]
    items = []
    if supported:
        items.append({"key": "supported", "title": "Haz visible tu experiencia relacionada", "detail": f"Esta oferta pide {', '.join(supported[:6])}, que ya aparecen en tu perfil. En la experiencia donde las usaste, explica qué hiciste, con qué herramienta y qué entregaste. Mantén tus cargos y fechas reales.", "href": "/perfil#profile-experiences", "action": "Revisar mi experiencia"})
    if review:
        items.append({"key": "review", "title": "Aclara estos requisitos", "detail": f"No hay respaldo suficiente en tu perfil para {', '.join(review[:6])}. Si los conoces, añade una descripción real de dónde los aplicaste. Si todavía no los conoces, puedes buscar formación; no los añadas solo por aparecer en la oferta.", "href": "/perfil#profile-skills", "action": "Revisar mis habilidades"})
    if not profile.experiences or not supported:
        items.append({"key": "experience", "title": f"Conecta tu trayectoria con {job.title}", "detail": "Describe las funciones de tu experiencia que se relacionan con las responsabilidades del anuncio. Puedes incluir prácticas o proyectos reales, indicando su contexto. Un entregable concreto ayuda aunque no tengas cifras.", "href": "/perfil#profile-experiences", "action": "Completar mi experiencia"})
    if job.required_education_level or job.required_study_fields:
        items.append({"key": "education", "title": "Presenta tu formación con claridad", "detail": "Revisa la formación solicitada en esta oferta y comprueba que tu perfil indique el título, la institución y el estado real de tus estudios. No cambies el nombre oficial de tu título para hacerlo coincidir.", "href": "/perfil#profile-educations", "action": "Revisar mi formación"})
    return {"job_id": job.id, "job_title": job.title, "items": items}


def radar(db, user, search="", sector="", location=""):
    return demand_report(owner_profile(user), db.jobs.active(), resources(db), search, sector, location)
