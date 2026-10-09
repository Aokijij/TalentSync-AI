from collections import Counter
from datetime import datetime
from math import log
from types import SimpleNamespace

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.application.use_cases.matching import candidate_match
from app.application.use_cases.organizations import context
from app.domain.services.match_explanations import MATCH_VERSION, requirements_for
from app.domain.services.reputation import company_health
from app.domain.services.skills import skill_key, skill_set


def trust(db, company_id):
    company = db.companies.get(company_id)
    if company is None:
        raise UseCaseError(status_code=404, detail="Empresa no encontrada")
    return {"company_id": company.id, "company_name": company.name, **company_health(company)}


def incident_view(row, *, private=False, db=None):
    result = {"id": row.id, "company_id": row.company_id, "category": row.category, "status": row.status,
              "shared_summary": row.shared_summary, "appeal": row.appeal, "created_at": row.created_at, "updated_at": row.updated_at}
    result["company_name"] = row.company.name
    if db:
        application = db.applications.get(row.application_id) if row.application_id else None
        result["job_title"] = application.job.title if application else "Proceso no disponible"
        result["history"] = [{"at": item.created_at, "type": item.event_type, "status": item.details.get("status")}
            for item in reversed(db.events.for_entity("incident", row.id))]
    if private:
        result.update({"reporter_user_id": row.reporter_user_id, "application_id": row.application_id, "details": row.details})
    return result


def report_incident(db, user, payload):
    row = db.applications.get(payload["application_id"])
    if row is None or row.user_id != user.id:
        raise UseCaseError(status_code=404, detail="Proceso propio no encontrado")
    pending = [item for item in db.ecosystem.incidents(reporter_id=user.id) if item.application_id == row.id and item.category == payload["category"] and item.status in {"open", "in_review", "appealed"}]
    if pending:
        raise UseCaseError(status_code=409, detail="Ya tienes una incidencia abierta de este tipo en el proceso")
    incident = db.ecosystem.new_incident(reporter_user_id=user.id, company_id=row.job.company_id, application_id=row.id,
        category=payload["category"], details=payload["details"], status="open", appeal={})
    db.add(incident)
    db.flush()
    record_event(db, "trust.incident_reported", "incident", incident.id, actor_user_id=user.id, details={"company_id": incident.company_id, "reason_code": incident.category})
    db.commit()
    return incident_view(incident, private=True, db=db)


def incidents(db, user, scope):
    if scope == "admin":
        return [incident_view(row, private=True, db=db) for row in db.ecosystem.incidents()]
    if scope == "organization":
        company = context(db, user, owner=True)
        return [incident_view(row, db=db) for row in db.ecosystem.incidents(company_id=company.id)]
    return [incident_view(row, private=True, db=db) for row in db.ecosystem.incidents(reporter_id=user.id)]


def review(db, user, incident_id, payload):
    row = db.ecosystem.incident(incident_id)
    if row is None:
        raise UseCaseError(status_code=404, detail="Incidencia no encontrada")
    previous = row.status
    row.status = payload["status"]
    row.shared_summary = payload["shared_summary"]
    record_event(db, "trust.incident_reviewed", "incident", row.id, actor_user_id=user.id,
                 details={"previous_status": previous, "status": row.status, "company_id": row.company_id})
    for recipient in [row.reporter_user_id, row.company.owner_user_id]:
        db.add(db.notifications.new(user_id=recipient, type="trust_incident", title="Incidencia actualizada", body=f"La incidencia #{row.id} está en estado {row.status}.", action_url="/confianza"))
    db.commit()
    return incident_view(row, private=True, db=db)


def appeal(db, user, incident_id, message):
    company = context(db, user, owner=True)
    row = db.ecosystem.incident(incident_id)
    if row is None or row.company_id != company.id:
        raise UseCaseError(status_code=404, detail="Incidencia no encontrada")
    if row.status != "confirmed":
        raise UseCaseError(status_code=409, detail="Solo puedes apelar una incidencia confirmada")
    row.appeal = {"message": message, "created_at": datetime.utcnow().isoformat()}
    row.status = "appealed"
    record_event(db, "trust.incident_appealed", "incident", row.id, actor_user_id=user.id, details={"company_id": company.id})
    db.commit()
    return incident_view(row, db=db)


def dashboard(db):
    candidates = db.users.candidates_with_profiles()[:500]
    jobs = db.jobs.active()[:500]
    demand = Counter(skill_key(row["skill"]) for job in jobs for row in requirements_for(job))
    supply = Counter(skill for user in candidates for skill in skill_set(user.profile.skills))
    skill_rows = [{"skill": skill, "vacancies": demand[skill], "candidate_profiles": supply[skill]} for skill in demand | supply]
    companies = [row for row in db.companies.list_owned(None) if not row.is_external][:200]
    return {"scope": "local_platform_data", "candidate_sample": len(candidates), "vacancy_sample": len(jobs),
            "skills": sorted(skill_rows, key=lambda row: (-row["vacancies"], row["skill"])),
            "companies": [{"id": row.id, "name": row.name, **company_health(row)} for row in companies],
            "audits": [{"id": row.id, "version": row.version, "created_at": row.created_at, "metrics": row.metrics} for row in db.ecosystem.audits()],
            "notice": "Muestras de esta plataforma. La semilla local contiene perfiles ficticios. Estas cifras no representan déficit del mercado laboral."}


class IdentityVariant:
    def __init__(self, profile):
        self.profile = profile
        self.user = SimpleNamespace(name="Identidad alternativa", email="alternative@example.com")
        self.photo_filename = "alternative.png"
        self.phone = "000000000"
        self.embedding = [0.0] * 384
        self.educations = [{**row, "institution": "Institución alternativa"} for row in profile.educations or []]

    def __getattr__(self, name):
        return getattr(self.profile, name)


def run_audit(db, user, nlp):
    version = f"{MATCH_VERSION}:{getattr(nlp, 'match_method', 'lexical-hashing-v1')}"
    candidates = db.users.candidates_with_profiles()[:20]
    jobs = db.jobs.active()[:10]
    scores = []
    violations = 0
    for candidate in candidates:
        for job in jobs:
            baseline = candidate_match(candidate.profile, job, nlp=nlp)[0]
            variant = candidate_match(IdentityVariant(candidate.profile), job, nlp=nlp)[0]
            violations += abs(baseline - variant) > .01
            scores.append(baseline)
    histogram = [sum(lower <= value < upper for value in scores) for lower, upper in [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]]
    previous = next((row.metrics for row in db.ecosystem.audits() if row.version == version), None)
    psi = None
    if previous and len(scores) >= 20 and previous.get("pair_count", 0) >= 20:
        current = [(value + .5) / (len(scores) + 2.5) for value in histogram]
        prior = [(value + .5) / (previous["pair_count"] + 2.5) for value in previous["score_histogram"]]
        psi = round(sum((a - b) * log(a / b) for a, b in zip(current, prior)), 4)
    metrics = {"pair_count": len(scores), "score_histogram": histogram, "identity_invariance_violations": violations,
               "identity_check_scope": ["name", "email", "photo", "phone", "institution", "legacy_embedding"],
               "demographic_fairness": "unavailable_no_consented_demographic_dataset", "distribution_psi": psi,
               "distribution_review_suggested": psi is not None and psi >= .2,
               "notice": "Control de invariancia sobre metadatos de identidad y distribución de puntuaciones; no demuestra ausencia de sesgos demográficos ni precisión predictiva."}
    audit = db.ecosystem.new_audit(actor_user_id=user.id, version=version, metrics=metrics)
    db.add(audit)
    record_event(db, "model.audit_completed", "platform", None, actor_user_id=user.id, details={"version": MATCH_VERSION, "result": "review_required" if violations else "checks_passed"})
    db.commit()
    return metrics
