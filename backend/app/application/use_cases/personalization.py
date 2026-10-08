import hashlib
import json
from datetime import datetime, timedelta

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.domain.services.match_explanations import MATCH_VERSION, preference_alignment
from app.domain.services.personalization import (
    collaborative_interest,
    consented,
    synthetic_email,
    training_gate,
)

FEATURES = ["skills", "context", "education", "certifications", "languages", "preferences"]


def feature_version(nlp):
    return f"{MATCH_VERSION}:{getattr(nlp, 'match_method', 'lexical-hashing-v1')}"


def feedback(db, user, job_id, interested, nlp):
    if not consented(user):
        raise UseCaseError(status_code=403, detail="Activa la personalización en Seguridad antes de registrar intereses")
    job = db.jobs.get(job_id)
    if job is None or job.status != "active":
        raise UseCaseError(status_code=404, detail="Vacante activa no encontrada")
    # Import here to avoid a matching -> personalization -> matching cycle.
    from app.application.use_cases.matching import candidate_match
    _, context, skills, language, _, education, certifications = candidate_match(user.profile, job, nlp=nlp)
    features = [skills, context, education if education is not None else context, certifications if certifications is not None else skills,
                language if language is not None else 0, preference_alignment(user.profile, job)["score"] or 0]
    row = db.personalization.find(user.id, job_id)
    if row is None:
        row = db.personalization.new_feedback(user_id=user.id, job_id=job_id)
        db.add(row)
    row.interested = interested
    row.features = features
    row.feature_version = feature_version(nlp)
    row.updated_at = datetime.utcnow()
    record_event(db, "recommendation.feedback_saved", "job", job.id, actor_user_id=user.id, details={"result": "interested" if interested else "not_interested"})
    db.commit()
    return {"job_id": job.id, "interested": interested}


def own(db, user):
    return [{"job_id": row.job_id, "title": row.job.title, "interested": row.interested} for row in db.personalization.feedback(user.id)]


def remove(db, user, job_id):
    row = db.personalization.find(user.id, job_id)
    if row:
        db.delete(row)
        # Existing shadow artifacts may include this signal.
        db.personalization.invalidate_artifacts("invalidated_feedback_removal")
        db.commit()
    return {"removed": True}


def order(db, user, recommendations):
    if not consented(user):
        for row in recommendations:
            row.personalization = {"enabled": False}
        return recommendations
    signals = db.personalization.feedback()
    own_signals = {row.job_id: row.interested for row in db.personalization.feedback(user.id)}
    visible = [row for row in recommendations if own_signals.get(row.job_id) is not False]
    for row in visible:
        row.personalization = {"enabled": True, "interested": own_signals.get(row.job_id), **collaborative_interest(user.profile, row.job_id, signals),
            "notice": "Interés agregado de perfiles con habilidades similares; separado de la afinidad técnica."}
    # Personalization breaks ties within ten-point affinity bands. Reputation
    # remains the primary ordering tier established by the matching use case.
    tiers = {row.job_id: row.job.employer_trust["visibility_reduced"] for row in visible}
    return sorted(visible, key=lambda row: (tiers[row.job_id], -int(row.match_percentage // 10), -int(own_signals.get(row.job_id) is True),
        -(row.personalization.get("score") if row.personalization.get("score") is not None else 50), -row.match_percentage))


def training_rows(db, nlp):
    return [{"user_id": row.user_id, "job_id": row.job_id, "label": int(row.interested), "features": row.features}
            for row in db.personalization.feedback() if consented(row.user) and row.feature_version == feature_version(nlp)
            and not synthetic_email(row.user.email)]


def model_status(db, nlp):
    rows = training_rows(db, nlp)
    applications = [row for user in db.users.candidates_with_profiles() if not synthetic_email(user.email) for row in db.applications.for_user(user.id)]
    return {"version": feature_version(nlp), "text_method": getattr(nlp, "match_method", "lexical-hashing-v1"),
        "training_data": training_gate(rows), "features": FEATURES, "minimum_data": {"rows": 100, "users": 20, "jobs": 10, "each_label": 20},
        "integrations": [
            {"name": "Modelo neuronal local", "status": "Activo" if getattr(nlp, "match_method", "").startswith("local-sentence-transformer:") else "Adaptador disponible; faltan dependencia y pesos locales"},
            {"name": "Acceso social de candidatos", "status": "Adaptadores Google, GitHub y LinkedIn disponibles; requieren credenciales OAuth. LinkedIn exige origen HTTPS. Consulta el login para ver cuáles están activos."},
            {"name": "Catálogos de cursos y afiliación", "status": "Catálogo local administrable e importación JSON disponibles; patrocinios visibles sin alterar ranking. APIs, compras y acuerdos externos pendientes."},
            {"name": "Análisis de proyectos", "status": "ZIP local disponible; adaptador de repositorios públicos GitHub activable por configuración y consentimiento. No verifica autoría ni dominio técnico."},
            {"name": "SSO corporativo del administrador", "status": "Google Workspace y Microsoft Entra ID disponibles con identidades aprovisionadas y MFA; requieren credenciales y selección del proveedor."},
            {"name": "Verificación oficial de empresas", "status": "Revisión manual local; falta proveedor de registros"},
            {"name": "Videollamada por Internet", "status": "Adaptador STUN/TURN disponible; requiere servidor de retransmisión configurado"},
            {"name": "Retos con ejecución", "status": "SQL restringido en memoria disponible en Aprendizaje. Otros lenguajes requieren un ejecutor aislado adicional."},
        ],
        "observed_processes": len(applications), "processes_advanced_to_interview": sum(row.status == "technical_interview" or any(event.details.get("status") == "technical_interview" for event in db.events.for_entity("application", row.id)) for row in applications),
        "experiments": [{"id": row.id, "version": row.version, "status": row.status, "metrics": row.metrics, "created_at": row.created_at} for row in db.personalization.experiments()],
        "notice": "Entrena interés declarado, no probabilidad de contratación. Los experimentos se evalúan fuera del ranking y no deciden postulaciones."}


def train(db, nlp, trainer, *, user=None, scheduled=False):
    previous = db.personalization.experiments()
    if scheduled and previous and previous[0].created_at > datetime.utcnow() - timedelta(days=1):
        return {"status": "not_due"}
    rows = training_rows(db, nlp)
    gate = training_gate(rows)
    if scheduled and not gate["ready"]:
        return {"status": "insufficient_data"}
    dataset_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    if scheduled and previous and previous[0].version == feature_version(nlp) and previous[0].metrics.get("dataset_hash") == dataset_hash:
        return {"status": "unchanged_data"}
    result = trainer.fit(rows) if gate["ready"] else {"status": "insufficient_data", "metrics": {}, "artifact": {}}
    experiment = db.personalization.new_experiment(version=feature_version(nlp), status=result["status"],
        metrics={**result["metrics"], "data": gate, "features": FEATURES}, artifact=result["artifact"])
    db.add(experiment)
    record_event(db, "model.experiment_completed", "platform", None, actor_user_id=user.id if user else None,
                 details={"version": MATCH_VERSION, "result": result["status"]})
    db.commit()
    return {"status": experiment.status, "metrics": experiment.metrics}
