import random
from collections import Counter
from datetime import datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.application.use_cases.jobs import get_job
from app.application.use_cases.learning_resources import resources as catalog_resources
from app.application.use_cases.matching import candidate_match
from app.domain.services.learning_catalog import ASSESSMENTS
from app.domain.services.match_explanations import requirements_for
from app.domain.services.skills import normalize_skills, skill_gap, skill_set


class ProjectedProfile:
    def __init__(self, profile, skills):
        self.profile = profile
        self.skills = skills

    def __getattr__(self, name):
        return getattr(self.profile, name)


def catalog(db):
    return {"resources": catalog_resources(db), "assessments": [{"id": key, "title": row["title"], "skill": row["skill"], "minutes": row["minutes"], "level": "fundamentals"} for key, row in ASSESSMENTS.items()],
            "external_catalogs_enabled": False, "notice": "Catálogo local y enlaces revisados por administración. Horas y costes orientativos; no se verifican compras ni certificados externos. La publicidad no mejora el orden de recomendación."}


def opportunities(db, user, job_id, nlp):
    job = get_job(job_id, db, user)
    gaps = [row for row in skill_gap(user.profile.skills, requirements_for(job)) if not row["covered"]]
    missing = {row["key"] for row in gaps}
    baseline = candidate_match(user.profile, job, nlp=nlp)[0]
    active = db.jobs.active()[:200]
    resources = []
    eligible = [resource for resource in catalog_resources(db) if missing & skill_set(resource["skills"])]
    eligible.sort(key=lambda row: (-len(missing & skill_set(row["skills"])), row["hours"], row["id"]))
    baselines = {other.id: candidate_match(user.profile, other, nlp=nlp)[0] for other in active}
    for resource in eligible[:10]:
        targeted = missing & skill_set(resource["skills"])
        if not targeted:
            continue
        projected_profile = ProjectedProfile(user.profile, normalize_skills([*user.profile.skills, *resource["skills"]]))
        projected = candidate_match(projected_profile, job, nlp=nlp)[0]
        affected = sum(candidate_match(projected_profile, other, nlp=nlp)[0] > baselines[other.id] for other in active)
        resources.append({**resource, "targeted_skills": sorted(targeted), "current_match": baseline, "projected_match": projected,
                          "estimated_gain": round(projected - baseline, 2), "other_jobs_impacted": affected,
                          "notice": "Escenario hipotético si acreditas la habilidad; completar el recurso no garantiza este resultado ni una entrevista."})
    return {"job_id": job.id, "gaps": gaps, "resources": sorted(resources, key=lambda row: (-row["estimated_gain"] / row["hours"], row["id"])),
            "sampled_jobs": len(active), "current_match": baseline, "eligible_resources": len(eligible), "resource_limit": 10}


def plans(db, user, resource_id=None, status=None):
    resources = {row["id"]: row for row in catalog_resources(db, include_inactive=True)}
    if resource_id is not None:
        if resource_id not in resources:
            raise UseCaseError(status_code=404, detail="Recurso no encontrado")
        row = db.learning.plan(user.id, resource_id)
        if row is None and not resources[resource_id]["active"]:
            raise UseCaseError(status_code=404, detail="El recurso ya no está disponible para planes nuevos")
        if row is None:
            row = db.learning.new_plan(user_id=user.id, resource_id=resource_id, status=status)
            db.add(row)
        row.status = status
        row.completed_at = datetime.utcnow() if status == "completed" else None
        record_event(db, "learning.plan_updated", "profile", user.profile.id, actor_user_id=user.id, details={"status": status})
        db.commit()
    return [{"id": row.id, "resource": resources.get(row.resource_id), "status": row.status, "created_at": row.created_at, "completed_at": row.completed_at} for row in db.learning.plans(user.id)]


def public_attempt(row):
    result = {"id": row.id, "assessment_id": row.assessment_id, "skill": row.skill, "version": row.version, "started_at": row.started_at,
              "expires_at": row.expires_at, "status": row.status, "score": row.score, "passed": row.passed, "feedback": row.feedback,
              "valid_until": row.valid_until, "level": "fundamentals"}
    if row.status == "active":
        result["questions"] = [{"id": item["id"], "prompt": item["prompt"], "choices": item["choices"]} for item in row.snapshot]
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
    snapshot = [dict(row) for row in bank["questions"]]
    random.SystemRandom().shuffle(snapshot)
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
    if row.status != "active" or row.expires_at < now:
        raise UseCaseError(status_code=409, detail="El intento ya se entregó o venció")
    expected = {question["id"] for question in row.snapshot}
    if set(answers) != expected:
        raise UseCaseError(status_code=422, detail="Responde exactamente las preguntas del intento")
    if not db.learning.claim_submission(row.id, user.id, now):
        raise UseCaseError(status_code=409, detail="El intento ya se entregó o venció")
    correct = sum(answers[item["id"]] == item["answer"] for item in row.snapshot)
    row.score = round(correct / len(row.snapshot) * 100, 2)
    row.passed = row.score >= 80
    row.feedback = [{"question_id": item["id"], "correct": answers[item["id"]] == item["answer"], "message": item["feedback"]} for item in row.snapshot]
    row.valid_until = now + timedelta(days=180) if row.passed else None
    if row.passed:
        grant_fundamentals(db, user, row, now)
    record_event(db, "assessment.completed", "profile", user.profile.id, actor_user_id=user.id, details={"assessment_id": row.assessment_id, "result": "passed" if row.passed else "not_passed", "version": row.version})
    db.commit()
    return public_attempt(row)


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
    return {"assessments": [{**public_attempt(row), "valid": bool(row.passed and row.valid_until and row.valid_until >= now)} for row in db.learning.attempts(user.id) if row.status == "completed"],
            "notice": "Las micropruebas acreditan únicamente fundamentos evaluados por TalentSync; no equivalen a certificaciones profesionales ni experiencia laboral."}


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
