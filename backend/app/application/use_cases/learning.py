import random
from collections import Counter
from datetime import datetime, timedelta
from uuid import NAMESPACE_URL, uuid4, uuid5

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.application.use_cases.jobs import get_job
from app.application.use_cases.learning_resources import resources as catalog_resources
from app.application.use_cases.matching import candidate_match, prepare_scores
from app.domain.services.career_learning import AREAS, profile_areas
from app.domain.services.challenge_tracks import (
    SOURCES,
    course_skills_for,
    related_assessments,
)
from app.domain.services.course_practices import (
    course_practice,
    practice_for_plan,
    public_practice,
    public_resource,
)
from app.domain.services.learning_activities import (
    InvalidActivity,
    evaluate,
    public_activity,
)
from app.domain.services.learning_catalog import ASSESSMENTS
from app.domain.services.match_explanations import requirements_for
from app.domain.services.requirement_analysis import requirement_rows
from app.domain.services.skills import normalize_skills, skill_gap, skill_set
from app.domain.services.sql_challenges import CHALLENGES


def _evaluate(item, value):
    try:
        return evaluate(item, value)
    except InvalidActivity as failure:
        raise UseCaseError(status_code=422, detail=str(failure)) from None


class ProjectedProfile:
    def __init__(self, profile, skills):
        self.profile = profile
        self.skills = skills

    def __getattr__(self, name):
        return getattr(self.profile, name)


def catalog(db, user, area="recommended"):
    if area not in {"recommended", "all", *AREAS}:
        raise UseCaseError(status_code=422, detail="Área de aprendizaje desconocida")
    recommended = profile_areas(user.profile)
    selected = {*recommended, "general"} if area == "recommended" else set(AREAS) if area == "all" else {area}
    available = catalog_resources(db)
    from app.domain.services.learning_relevance import ranked_resources
    ranked = ranked_resources(available, user.profile, recommended)
    if area == "recommended":
        specific = [row for row in ranked if row["relevance"]["kind"] != "complementary"]
        complementary = [row for row in ranked if row["relevance"]["kind"] == "complementary" and row.get("category", "general") == "general"]
        visible = [*specific, *complementary[:3]] if specific else complementary
    else:
        visible = [row for row in ranked if row.get("category", "general") in selected]
    latest = {}
    for attempt in db.learning.attempts(user.id):
        latest.setdefault(attempt.assessment_id, attempt)
    def attempt_summary(key):
        row = latest.get(key)
        return {field: getattr(row, field) for field in ("id", "status", "started_at", "expires_at", "score", "passed")} if row else None
    from app.domain.services.market_radar import synthetic_job
    demand = Counter(skill for job in db.jobs.active() if not synthetic_job(job) for skill in skill_set(job.skills))
    return {"resources": visible,
            "assessments": [{"id": key, "title": row["title"], "skill": row["skill"], "minutes": row["minutes"], "last_attempt": attempt_summary(key), "relevance_reason": "Practica una habilidad que declaraste en tu perfil." if skill_set([row["skill"]]) & skill_set(user.profile.skills or []) else "Relacionada con el área que estás explorando.", "level": row.get("level", "fundamentals"), "category": row["category"], "formats": sorted({q.get("type", "choice") for q in row["questions"]}), "context": row.get("context", "Resuelve tareas concretas de esta habilidad."), "question_count": row.get("question_count", len(row["questions"])), "topics": list(dict.fromkeys(q.get("topic", "Fundamentos") for q in row["questions"])), "scope": row.get("scope"), "source_ids": row.get("source_ids", []), "demand_count": sum(demand[skill] for skill in skill_set([row["skill"], *row.get("related_skills", [])]))}
                            for key, row in ASSESSMENTS.items() if row["category"] in selected and (not row.get("retired") or latest.get(key) and latest[key].status == "active")],
            "challenge_sources": SOURCES, "challenge_demand_note": "Menciones de habilidades en las ofertas activas disponibles, excluyendo demostraciones identificables. Una oferta puede mencionar varias habilidades relacionadas; no representa todo el mercado colombiano.",
            "areas": [{"id": key, "label": row["label"]} for key, row in AREAS.items()],
            "recommended_areas": recommended, "selected_area": area,
            "plan_limit": 3, "external_catalogs_enabled": False, "notice": "Sugerencias ordenadas por habilidades, funciones, experiencia y contexto del CV. Las coincidencias se explican en cada recurso. Puedes explorar otra área. Los retos de TalentSync no son certificaciones profesionales; los cursos externos requieren revisión independiente."}


def opportunities(db, user, job_id, nlp):
    job = get_job(job_id, db, user)
    gaps = [row for row in requirement_rows(user.profile, job) if not row["covered"]]
    missing = {row["key"] for row in gaps}
    active = [other for other in db.jobs.active() if other.id != job.id][:200]
    resources = []
    eligible = [resource for resource in catalog_resources(db) if missing & skill_set(resource["skills"])]
    eligible.sort(key=lambda row: (-len(missing & skill_set(row["skills"])), row["hours"], row["id"]))
    projections = [(resource, ProjectedProfile(user.profile, normalize_skills([*user.profile.skills, *resource["skills"]]))) for resource in eligible[:10]]
    prepare_scores(nlp, [(user.profile, job), *[(profile, job) for _, profile in projections]])
    baseline = candidate_match(user.profile, job, nlp=nlp)[0]
    # Other offers need only an explicit missing-skill intersection. Running
    # the neural model for every course/offer pair blocked ordinary requests.
    known = skill_set(user.profile.skills)
    other_gaps = [skill_set([row["skill"] for row in requirements_for(other)]) - known for other in active]
    for resource, projected_profile in projections:
        targeted = missing & skill_set(resource["skills"])
        if not targeted:
            continue
        projected = candidate_match(projected_profile, job, nlp=nlp)[0]
        affected = sum(bool(missing_skills & skill_set(resource["skills"])) for missing_skills in other_gaps)
        resources.append({**resource, "targeted_skills": sorted(targeted), "current_match": baseline, "projected_match": projected,
                          "estimated_gain": round(projected - baseline, 2), "other_jobs_impacted": affected,
                          "notice": "Escenario hipotético si acreditas la habilidad. Otras vacantes cuentan requisitos relacionados, sin recalcular su compatibilidad. Completar el curso no acredita dominio ni garantiza una entrevista."})
    return {"job_id": job.id, "gaps": gaps, "resources": sorted(resources, key=lambda row: (-row["estimated_gain"] / row["hours"], row["id"])),
            "sampled_jobs": len(active), "current_match": baseline, "eligible_resources": len(eligible), "resource_limit": 10}


def plans(db, user, resource_id=None, status=None):
    resources = {row["id"]: row for row in catalog_resources(db, include_inactive=True, private=True)}
    if resource_id is not None:
        if resource_id not in resources:
            raise UseCaseError(status_code=404, detail="Recurso no encontrado")
        db.learning.lock_owner(user.id)
        row = db.learning.plan(user.id, resource_id)
        if status == "in_progress" and (row is None or row.status == "completed") and sum(item.status != "completed" for item in db.learning.plans(user.id)) >= 3:
            raise UseCaseError(status_code=409, detail="Tu plan admite tres recursos activos. Finaliza o abandona uno antes de añadir otro.")
        if row is None and not resources[resource_id]["active"]:
            raise UseCaseError(status_code=404, detail="El recurso ya no está disponible para planes nuevos")
        if row is None:
            row = db.learning.new_plan(user_id=user.id, resource_id=resource_id, status=status)
            row.progress = {"practice_spec": course_practice(resources[resource_id]), "course_tracking": bool(resources[resource_id].get("url")), "course_completed": False}
            db.add(row)
        if resources[resource_id].get("url") and status == "completed":
            row.progress = {**(row.progress or {}), "course_tracking": True, "course_completed": True, "course_completed_at": datetime.utcnow().isoformat()}
        elif resources[resource_id].get("url") and row.status == "completed":
            row.progress = {**(row.progress or {}), "course_tracking": True, "course_completed": False, "course_completed_at": None}
        row.status = status
        row.completed_at = datetime.utcnow() if status == "completed" else None
        row.version = (row.version or 0) + 1
        record_event(db, "learning.plan_updated", "profile", user.profile.id, actor_user_id=user.id, details={"status": status})
        db.commit()
    return [{"id": row.id, "resource": _plan_resource(resources.get(row.resource_id), row.progress or {}), "status": row.status, "created_at": row.created_at, "completed_at": row.completed_at,
             "version": row.version, "certificate": next((item for item in user.profile.certifications or [] if item.get("resource_id") == row.resource_id), None),
             "skills_added": skill_set(resources.get(row.resource_id, {}).get("skills", [])) <= skill_set(user.profile.skills or []), "remaining_skills": [skill for skill in resources.get(row.resource_id, {}).get("skills", []) if skill_set([skill]) - skill_set(user.profile.skills or [])], "progress": {**{key: value for key, value in (row.progress or {}).items() if key != "practice_spec"}, "activity_feedback": (row.progress or {}).get("activity_feedback", []) if row.status == "completed" or (row.progress or {}).get("submitted") else [], "published": bool((row.progress or {}).get("published")) and any(item.get("id") == (row.progress or {}).get("evidence_id") for item in user.profile.evidence or [])}} for row in db.learning.plans(user.id)]


def _plan_resource(resource, progress):
    if resource is None:
        return None
    practice = practice_for_plan(resource, progress)
    if practice is None:
        return {**public_resource(resource), "journey": None}
    from app.domain.services.learning_journeys import journey_for
    base = resource.get("journey") or journey_for({**resource, "url": None})
    return {**public_resource(resource), "journey": {**base, **public_practice(practice)}}


def course_challenges(db, user, resource_id):
    if db.learning.plan(user.id, resource_id) is None:
        raise UseCaseError(status_code=404, detail="Recurso no encontrado en tu plan")
    resource = next((item for item in catalog_resources(db, include_inactive=True) if item["id"] == resource_id), None)
    if resource is None:
        raise UseCaseError(status_code=404, detail="Recurso no disponible")
    related = set(resource.get("assessment_ids", []))
    report = catalog(db, user, "all")
    return {"skills": resource["skills"], "course_level": (resource.get("details") or {}).get("level", "any"),
            "assessments": [{**item, "course_skills": course_skills_for(resource, ASSESSMENTS[item["id"]])} for item in report["assessments"] if item["id"] in related],
            "notice": "Relacionados por habilidades del catálogo. El resultado se comparte entre cursos que desarrollan esa habilidad; no demuestra haber completado el temario de un proveedor."}


def save_course_progress(db, user, resource_id, version, completed):
    resource = next((item for item in catalog_resources(db, include_inactive=True) if item["id"] == resource_id), None)
    row = db.learning.plan(user.id, resource_id)
    if row is None or resource is None or not resource.get("url"):
        raise UseCaseError(status_code=404, detail="Curso externo no encontrado en tu plan")
    db.learning.lock_owner(user.id)
    if not completed and row.status == "completed" and sum(item.status != "completed" for item in db.learning.plans(user.id)) >= 3:
        raise UseCaseError(status_code=409, detail="Tu plan ya tiene tres recursos activos")
    if not db.learning.claim_progress(row.id, user.id, version):
        raise UseCaseError(status_code=409, detail="El plan cambió. Actualiza antes de guardar")
    now = datetime.utcnow()
    row.progress = {**(row.progress or {}), "course_tracking": True, "course_completed": completed, "course_completed_at": now.isoformat() if completed else None}
    row.status, row.completed_at = ("completed", now) if completed else ("in_progress", None)
    record_event(db, "learning.course_progress", "profile", user.profile.id, actor_user_id=user.id, details={"status": row.status, "source": "declared"})
    db.commit()
    return plans(db, user)


def leave_plan(db, user, resource_id, version):
    row = db.learning.plan(user.id, resource_id)
    if row is None:
        raise UseCaseError(status_code=404, detail="El recurso no está en tu plan")
    if not db.learning.claim_progress(row.id, user.id, version):
        raise UseCaseError(status_code=409, detail="El plan cambió; actualiza antes de abandonarlo")
    db.delete(row)
    record_event(db, "learning.plan_left", "profile", user.profile.id, actor_user_id=user.id, details={"status": "left"})
    db.commit()
    return plans(db, user)


def save_journey(db, user, resource_id, payload):
    resource = next((item for item in catalog_resources(db, include_inactive=True, private=True) if item["id"] == resource_id), None)
    row = db.learning.plan(user.id, resource_id)
    if resource is None or row is None:
        raise UseCaseError(status_code=404, detail="Añade primero esta práctica a tu plan")
    previous = row.progress or {}
    if practice_for_plan(resource, previous) is None:
        raise UseCaseError(status_code=409, detail="Este curso no tiene una práctica asociada. Su avance se gestiona por separado")
    resource = {**resource, "journey": _plan_resource(resource, previous)["journey"]}
    if payload.get("retry"):
        legacy_attempt = row.status == "completed" and bool(previous.get("activity_feedback"))
        if not previous.get("submitted") and not legacy_attempt:
            raise UseCaseError(status_code=409, detail="Entrega el intento actual antes de iniciar otro")
        db.learning.lock_owner(user.id)
        if row.status == "completed" and not previous.get("course_completed") and sum(item.status != "completed" for item in db.learning.plans(user.id)) >= 3:
            raise UseCaseError(status_code=409, detail="Finaliza o abandona un recurso antes de volver a intentarlo")
        if not db.learning.claim_progress(row.id, user.id, payload["version"]):
            raise UseCaseError(status_code=409, detail="El plan cambió; actualiza antes de reintentar")
        history = (user.profile.preferences or {}).get("learning_results", [])
        if legacy_attempt and not any(item["resource_id"] == resource_id for item in history):
            feedback = previous["activity_feedback"]
            score = round(sum(item["correct"] for item in feedback) / len(feedback) * 100, 1)
            result = {"id": uuid4().hex, "resource_id": resource_id, "title": resource["title"], "provider": resource["provider"],
                      "score": score, "passed": score >= 80, "feedback": [{**item, "message": item["message"] if item["correct"] else "Revisa esta actividad en otro intento."} for item in feedback],
                      "completed_at": row.completed_at.isoformat() if row.completed_at else datetime.utcnow().isoformat(),
                      "attempt_number": 1, "skills": resource["skills"], "published": previous.get("published", False)}
            user.profile.preferences = {**(user.profile.preferences or {}), "learning_results": [*history, result][-100:]}
        row.progress = {**{key: previous.get(key) for key in ("course_tracking", "course_completed", "course_completed_at")}, "answers": {}, "activity_answers": {}, "activity_feedback": [], "submitted": False,
                        "practice_spec": course_practice(resource) or practice_for_plan(resource, previous),
                        "published": previous.get("published", False), "evidence_id": previous.get("evidence_id"),
                        "attempt_number": previous.get("attempt_number", 1) + 1}
        if not previous.get("course_completed"):
            row.status, row.completed_at = "in_progress", None
        db.commit()
        return plans(db, user)
    if previous.get("submitted"):
        raise UseCaseError(status_code=409, detail="Este intento ya se entregó. Inicia otro para cambiar las respuestas")
    if row.status == "completed" and not payload.get("finish"):
        db.learning.lock_owner(user.id)
        if row.status == "completed" and not previous.get("course_completed") and sum(item.status != "completed" for item in db.learning.plans(user.id)) >= 3:
            raise UseCaseError(status_code=409, detail="Finaliza o abandona un recurso antes de reabrir esta práctica")
    steps = resource["journey"]["steps"]
    answers = {key: value.strip() for key, value in payload["answers"].items()}
    if set(answers) - {step["id"] for step in steps}:
        raise UseCaseError(status_code=422, detail="La práctica contiene un paso desconocido")
    finish = payload.get("finish", False)
    activity_answers = payload.get("activity_answers")
    practice = practice_for_plan(resource, previous)
    feedback = []
    if activity_answers is not None:
        activities = practice["activities"]
        if set(activity_answers) - {item["id"] for item in activities}:
            raise UseCaseError(status_code=422, detail="Actividad desconocida")
        if finish and set(activity_answers) != {item["id"] for item in activities}:
            raise UseCaseError(status_code=422, detail="Responde las tres actividades antes de entregar")
        for index, item in enumerate(activities):
            if item["id"] not in activity_answers:
                continue
            value = activity_answers[item["id"]]
            partial = value == "" or item["type"] == "matching" and isinstance(value, list) and -1 in value
            if partial:
                if finish:
                    raise UseCaseError(status_code=422, detail="Completa las respuestas antes de entregar")
                if isinstance(value, list) and (len(value) != len(item["terms"]) or any(type(key) is not int or key < -1 or key >= len(item["choices"]) for key in value)):
                    raise UseCaseError(status_code=422, detail="Relaciones de la actividad inválidas")
            else:
                correct = False if item["type"] == "matching" and isinstance(value, list) and len(set(value)) != len(value) and len(value) == len(item["terms"]) and all(type(key) is int and 0 <= key < len(item["choices"]) for key in value) else _evaluate(item, value)
                if finish:
                    feedback.append({"question_id": item["id"], "prompt": item["prompt"], "correct": correct,
                                     "message": item["feedback"] if correct else "Revisa los datos del caso y tu decisión en un nuevo intento."})
            detail = " → ".join(item["choices"][key] if key >= 0 else "Sin relacionar" for key in value) if isinstance(value, list) else str(value)
            answers[steps[index]["id"]] = f"{item['prompt']} Mi respuesta: {detail}."[:550]
    if finish and activity_answers is None and any(len(answers.get(step["id"], "")) < 40 for step in steps):
        raise UseCaseError(status_code=422, detail="Desarrolla cada paso con al menos 40 caracteres antes de publicar")
    score = round(sum(item["correct"] for item in feedback) / len(feedback) * 100, 1) if finish and feedback else None
    passed = score is None or score >= 80
    publish = finish and passed
    evidence_id = uuid5(NAMESPACE_URL, f"talentsync:learning-evidence:{user.id}:{resource_id}").hex
    existing = [item for item in user.profile.evidence or [] if item["id"] != evidence_id]
    if publish and len(existing) >= 50:
        raise UseCaseError(status_code=422, detail="Tu perfil admite hasta cincuenta evidencias; retira una antes de publicar")
    skills = normalize_skills([*(user.profile.skills or []), *resource["skills"]]) if payload.get("add_to_profile") else user.profile.skills
    if finish and len(skills) > 100:
        raise UseCaseError(status_code=422, detail="Tu perfil admite hasta cien habilidades")
    if not db.learning.claim_progress(row.id, user.id, payload["version"]):
        raise UseCaseError(status_code=409, detail="El plan cambió en otra pestaña. Actualiza para conservar el avance más reciente")
    now = datetime.utcnow()
    row.progress = {**{key: previous.get(key) for key in ("course_tracking", "course_completed", "course_completed_at")}, "practice_spec": practice, "activity_answers": activity_answers if activity_answers is not None else previous.get("activity_answers"),
                    "activity_feedback": feedback, "answers": answers, "published": publish or bool(previous.get("published")),
                    "submitted": finish and activity_answers is not None, "score": score, "passed": passed if finish else None,
                    "attempt_number": previous.get("attempt_number", 1),
                    "has_unpublished_changes": not finish and (bool(previous.get("has_unpublished_changes")) or answers != previous.get("answers", {})),
                    "evidence_id": evidence_id if publish else previous.get("evidence_id")}
    if resource.get("url"):
        row.status = "completed" if previous.get("course_completed") else "in_progress"
        if not previous.get("course_completed"):
            row.completed_at = None
    else:
        row.status, row.completed_at = ("completed", now) if finish else ("in_progress", None)
    if publish:
        user.profile.evidence = [*existing, {"id": evidence_id, "title": practice["lab_title"] if activity_answers is not None else resource["journey"]["title"], "kind": "project", "url": None,
            "skills": resource["skills"], "description": "\n\n".join(f"{step['title']}: {answers[step['id']]}" for step in steps),
            "verified": False, "add_to_profile": bool(payload.get("add_to_profile")), "source": "learning_practice", "created_at": now.isoformat()}]
    if finish:
        if payload.get("add_to_profile"):
            user.profile.skills = skills
        user.profile.updated_at = now
        result = {"id": uuid4().hex, "resource_id": resource_id, "title": practice["lab_title"], "course_title": resource["title"] if resource.get("url") else None, "provider": "TalentSync", "practice_binding": practice.get("binding", {"mode": "legacy"}),
                  "score": score, "passed": passed, "feedback": feedback, "completed_at": now.isoformat(),
                  "attempt_number": previous.get("attempt_number", 1), "skills": resource["skills"], "published": publish}
        history = (user.profile.preferences or {}).get("learning_results", [])
        user.profile.preferences = {**(user.profile.preferences or {}), "learning_results": [*history, result][-100:]}
    record_event(db, "learning.practice_published" if publish else "learning.practice_saved", "profile", user.profile.id,
                 actor_user_id=user.id, details={"status": row.status})
    db.commit()
    return plans(db, user)


def add_plan_skills(db, user, resource_id, payload=None, nlp=None):
    row = db.learning.plan(user.id, resource_id)
    resource = next((item for item in catalog_resources(db, include_inactive=True) if item["id"] == resource_id), None)
    if row is None or resource is None:
        raise UseCaseError(status_code=404, detail="Recurso no encontrado en tu plan")
    db.learning.lock_owner(user.id)
    db.refresh(row)
    db.refresh(user.profile)
    if resource.get("url"):
        if not (row.progress or {}).get("course_completed") or row.status != "completed":
            raise UseCaseError(status_code=409, detail="Marca el curso como finalizado antes de añadir sus habilidades")
        if resource.get("retired") or not payload or not payload.get("confirm"):
            raise UseCaseError(status_code=422, detail="Selecciona y confirma las habilidades que aprendiste en este curso")
        claimed = normalize_skills(payload["skills"])
        if not claimed or not skill_set(claimed) <= skill_set(resource["skills"]):
            raise UseCaseError(status_code=422, detail="Selecciona únicamente habilidades que desarrolla este curso")
    else:
        if row.status != "completed" and not (row.progress or {}).get("submitted"):
            raise UseCaseError(status_code=409, detail="Finaliza el intento antes de incorporar sus habilidades")
        claimed = resource["skills"]
    skills = normalize_skills([*(user.profile.skills or []), *claimed])
    if len(skills) > 100:
        raise UseCaseError(status_code=422, detail="Tu perfil admite hasta cien habilidades")
    user.profile.skills, user.profile.updated_at = skills, datetime.utcnow()
    if nlp is not None:
        user.profile.embedding = nlp.embed(" ".join(filter(None, [user.profile.profession, user.profile.experience, " ".join(skills)])))
    record_event(db, "learning.skills_added", "profile", user.profile.id, actor_user_id=user.id, details={"source": "declared"})
    db.commit()
    return plans(db, user)


def public_attempt(row):
    result = {"id": row.id, "assessment_id": row.assessment_id, "title": (ASSESSMENTS.get(row.assessment_id) or CHALLENGES.get(row.assessment_id) or {}).get("title", row.skill), "skill": row.skill, "version": row.version, "started_at": row.started_at,
              "expires_at": row.expires_at, "status": row.status, "score": row.score, "passed": row.passed, "feedback": row.feedback,
              "valid_until": row.valid_until, "level": (ASSESSMENTS.get(row.assessment_id) or {}).get("level", "fundamentals"), "question_count": len(row.snapshot),
              "topic_results": [{"topic": topic, "correct": sum(bool(item["correct"]) for item in row.feedback if item.get("topic", "Fundamentos") == topic), "total": sum(item.get("topic", "Fundamentos") == topic for item in row.feedback)} for topic in dict.fromkeys(item.get("topic", "Fundamentos") for item in row.feedback or [])]}
    if row.status == "active":
        result["questions"] = [public_activity(item) for item in row.snapshot]
    return result


def start_assessment(db, user, assessment_id):
    bank = ASSESSMENTS.get(assessment_id)
    if bank is None:
        raise UseCaseError(status_code=404, detail="Evaluación no disponible para esa habilidad")
    now = datetime.utcnow()
    attempts = [row for row in db.learning.attempts(user.id) if row.assessment_id == assessment_id]
    if attempts and attempts[0].status == "active" and attempts[0].expires_at > now:
        return public_attempt(attempts[0])
    if attempts and attempts[0].started_at > now - timedelta(days=1):
        raise UseCaseError(status_code=429, detail="Puedes realizar un nuevo intento después de 24 horas")
    from copy import deepcopy
    rng = random.SystemRandom()
    by_id = {item["id"]: item for item in bank["questions"]}
    snapshot = [deepcopy(by_id[key]) for section in bank.get("selection", []) for key in rng.sample(section["ids"], section["count"])] if bank.get("selection") else deepcopy(bank["questions"])
    # Remap solutions when shuffling choices. Matching answers map one index per
    # term; order answers map the ordered choice indices. Never mutate the bank.
    for item in snapshot if bank.get("selection") else []:
        choices = item.get("choices", [])
        if not choices:
            continue
        order = list(range(len(choices))); rng.shuffle(order)
        item["choices"] = [choices[index] for index in order]
        answer = item["answer"]
        item["answer"] = [order.index(index) for index in answer] if isinstance(answer, list) else order.index(answer)
    rng.shuffle(snapshot)
    attempt_id = uuid5(NAMESPACE_URL, f"talentsync:{user.id}:{assessment_id}:{now.date().isoformat()}").hex
    row = db.learning.new_attempt(id=attempt_id, user_id=user.id, assessment_id=assessment_id, skill=bank["skill"], version=bank["version"],
                                 snapshot=snapshot, started_at=now, expires_at=now + timedelta(minutes=bank["minutes"]), status="active", feedback=[])
    db.add(row)
    record_event(db, "assessment.started", "profile", user.profile.id, actor_user_id=user.id, details={"assessment_id": assessment_id})
    db.commit()
    return public_attempt(row)


def submit_assessment(db, user, attempt_id, answers):
    row = db.learning.attempt(attempt_id)
    now = datetime.utcnow()
    if row is None or row.user_id != user.id:
        raise UseCaseError(status_code=404, detail="Intento no encontrado")
    if row.assessment_id not in ASSESSMENTS:
        raise UseCaseError(status_code=422, detail="Este intento utiliza el formulario de reto práctico")
    if row.status != "active" or row.expires_at <= now:
        raise UseCaseError(status_code=409, detail="El intento ya se entregó o venció")
    expected = {question["id"] for question in row.snapshot}
    if set(answers) != expected:
        raise UseCaseError(status_code=422, detail="Responde exactamente las preguntas del intento")
    grades = {item["id"]: _evaluate(item, answers[item["id"]]) for item in row.snapshot}
    if not db.learning.claim_submission(row.id, user.id, now):
        raise UseCaseError(status_code=409, detail="El intento ya se entregó o venció")
    correct = sum(grades.values())
    row.score = round(correct / len(row.snapshot) * 100, 2)
    row.passed = row.score >= 80
    row.feedback = [{"question_id": item["id"], "correct": grades[item["id"]], "prompt": item["prompt"], "topic": item.get("topic", "Fundamentos"), "context": item.get("context"), "submitted": answers[item["id"]], "message": item["feedback"]} for item in row.snapshot]
    row.valid_until = now + timedelta(days=180) if row.passed else None
    if row.passed:
        grant_fundamentals(db, user, row, now)
    record_event(db, "assessment.completed", "profile", user.profile.id, actor_user_id=user.id, details={"assessment_id": row.assessment_id, "result": "passed" if row.passed else "not_passed", "version": row.version})
    db.commit()
    result = public_attempt(row)
    result["improvement_resources"] = [resource for resource in catalog_resources(db) if row.assessment_id in related_assessments(resource, ASSESSMENTS) or skill_set([row.skill]) & skill_set(resource["skills"])][:4] if correct < len(row.snapshot) else []
    return result


def grant_fundamentals(db, user, row, now):
    user.profile.skills = normalize_skills([*(user.profile.skills or []), row.skill])
    user.profile.updated_at = now
    if (user.privacy_preferences or {}).get("notify_new_skills", False):
        recipients = {application.job.company.owner_user_id for application in user.applications if application.released_at is None and application.status.value not in {"rejected", "hired", "accepted"}}
        for recipient in recipients:
            db.add(db.notifications.new(user_id=recipient, type="candidate_skill_validated", title="Nueva evaluación de fundamentos aprobada",
                body=f"Un candidato de tus procesos aprobó fundamentos de {row.skill}.", action_url="/empresa/postulaciones"))


def passport(db, user):
    now = datetime.utcnow()
    resources = catalog_resources(db)
    results = list((user.profile.preferences or {}).get("learning_results", []))
    represented = {item["resource_id"] for item in results}
    for plan in plans(db, user):
        if plan["status"] != "completed" or not plan["resource"] or plan["resource"]["id"] in represented or not any(plan["progress"].get(key) for key in ("activity_feedback", "answers", "published")):
            continue
        progress = plan["progress"]
        feedback = progress.get("activity_feedback") or []
        results.append({"id": f"legacy-plan-{plan['id']}", "resource_id": plan["resource"]["id"], "title": plan["resource"]["title"],
                        "provider": plan["resource"]["provider"], "score": round(sum(item["correct"] for item in feedback) / len(feedback) * 100, 1) if feedback else None,
                        "passed": all(item["correct"] for item in feedback) if feedback else True, "feedback": [{**item, "message": item["message"] if item["correct"] else "Revisa esta actividad en un nuevo intento."} for item in feedback],
                        "completed_at": plan["completed_at"], "attempt_number": 1, "skills": plan["resource"]["skills"], "published": progress.get("published", False)})
    return {"practice_evidence": [{"id": item["id"], "title": item["title"], "skills": item["skills"]} for item in user.profile.evidence or [] if item.get("source") == "learning_practice"],
            "learning_results": list(reversed(results)), "certificates": user.profile.certifications or [],
            "course_results": [{"resource_id": item["resource"]["id"], "title": item["resource"]["title"], "provider": item["resource"]["provider"], "completed_at": item["progress"].get("course_completed_at")} for item in plans(db, user) if item["resource"] and item["progress"].get("course_completed")],
            "assessments": [{**public_attempt(row), "valid": bool(row.passed and row.valid_until and row.valid_until >= now),
                             "improvement_resources": [resource for resource in resources if skill_set([row.skill]) & skill_set(resource["skills"])][:4] if any(not item["correct"] for item in row.feedback) else []}
                            for row in db.learning.attempts(user.id) if row.status == "completed"],
            "notice": "Las prácticas, habilidades declaradas y certificados aportados aparecen separados de las evaluaciones de fundamentos. TalentSync no valida certificados externos."}


def patterns(db, user):
    observed = Counter()
    communicated = Counter()
    for application in db.applications.for_user(user.id):
        if application.status.value != "rejected" or application.released_at:
            continue
        observed.update(row["key"] for row in skill_gap(user.profile.skills, requirements_for(application.job)) if not row["covered"])
        feedback = application.candidate_feedback or {}
        if feedback.get("source") == "company":
            communicated.update([feedback["reason_code"]])
    return {"repeated_gaps": [{"skill": skill, "processes": count} for skill, count in observed.most_common(10) if count >= 2],
            "communicated_reasons": dict(communicated), "notice": "Brechas observadas en ofertas finalizadas; no se infiere que hayan causado el rechazo."}


def register_external_certificate(db, user, resource_id, payload):
    plan = db.learning.plan(user.id, resource_id)
    resource = next((row for row in catalog_resources(db, include_inactive=True) if row["id"] == resource_id), None)
    if plan is None or resource is None or not resource.get("url"):
        raise UseCaseError(status_code=404, detail="Plan de formación externa no encontrado")
    db.learning.lock_owner(user.id)
    db.refresh(plan)
    db.refresh(user.profile)
    if not (plan.progress or {}).get("course_completed") or plan.status != "completed":
        raise UseCaseError(status_code=409, detail="Marca el curso como finalizado antes de aportar su certificado")
    if (resource.get("details") or {}).get("certificate_cost") == "none" and not any(item.get("resource_id") == resource_id for item in user.profile.certifications or []):
        raise UseCaseError(status_code=422, detail="Este recurso es para aprendizaje sin certificado anunciado")
    if payload["year"] > datetime.utcnow().year:
        raise UseCaseError(status_code=422, detail="La fecha de expedición no puede estar en el futuro")
    identifier = uuid5(NAMESPACE_URL, f"talentsync:external-certificate:{user.id}:{resource_id}").hex
    certificate = {"id": identifier, "name": payload["name"], "issuer": resource["provider"], "year": str(payload["year"]),
        "url": payload["credential_url"], "certificate_id": payload["certificate_id"], "source": "external_certificate",
        "resource_id": resource_id, "verified": False}
    previous_evidence = next((item for item in user.profile.evidence or [] if item.get("id") == identifier), {})
    user.profile.certifications = [item for item in user.profile.certifications or [] if item.get("id") != identifier] + [certificate]
    user.profile.evidence = [item for item in user.profile.evidence or [] if item.get("id") != identifier] + [{
        "id": identifier, "title": payload["name"], "kind": "certificate", "url": payload["credential_url"], "skills": resource["skills"],
        "issuer": resource["provider"], "year": str(payload["year"]), "certificate_id": payload["certificate_id"],
        "description": f"Certificado externo aportado por el candidato. Emisor: {resource['provider']}. TalentSync no valida certificados.",
        "verified": False, "add_to_profile": previous_evidence.get("add_to_profile", False), "source": "external_certificate", "created_at": datetime.utcnow().isoformat()}]
    record_event(db, "learning.external_certificate_added", "user", user.id, actor_user_id=user.id, details={"source": "external_certificate"})
    db.commit()
    return {"message": "Certificado aportado añadido al perfil. TalentSync no valida certificados.", "certificate": certificate}
