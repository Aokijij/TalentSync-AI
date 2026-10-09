"""Add a connected functional review bundle to the owned local database only."""
import csv
import json
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.application.use_cases import (
    account_security,
    learning,
    organizations,
    personalization,
    sql_practice,
)
from app.application.use_cases.matching import upsert_recommendation
from app.core.config import settings
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.domain.services.learning_activities import activities_for
from app.domain.services.learning_catalog import ASSESSMENTS
from app.domain.services.pipeline import default_stages
from app.infrastructure.database.models import (
    Application,
    AssessmentAttempt,
    Company,
    CompanyFollower,
    CompanyInvitation,
    CompanyMember,
    EventLog,
    Job,
    LearningPlan,
    LearningResource,
    MailMessage,
    Notification,
    Profile,
    User,
)
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.nlp.text_processor import text_processor
from app.infrastructure.security.passwords import hash_password
from app.infrastructure.sql_sandbox import SQLSandbox
from scripts.functional_scenarios import BOUNDARIES, CANDIDATES, COMPANIES, JOBS, TEAM

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = "functional-review-v1"
APP = "http://127.0.0.1:5173"


class SeedUnitOfWork(SqlAlchemyUnitOfWork):
    """Use production validation, keeping the entire bundle in one transaction."""

    def commit(self):
        self.flush()


def seed(db, registry, *, nlp, now=None):
    now = now or datetime.now(UTC).replace(tzinfo=None)
    marker = db.query(EventLog).filter_by(event_type="demo.scenarios_created", entity_type=BUNDLE).first()
    if marker:
        if not registry.get("accounts") or registry.get("bundle") != BUNDLE:
            raise ValueError("Los escenarios ya existen; recupera su archivo privado de accesos. No se restablecen contraseñas.")
        for row in registry["accounts"]:
            user = db.get(User, row["id"])
            if user is None:
                raise ValueError("Falta una cuenta de la carga anterior. No se recrea ni se reinicia automáticamente.")
        return registry, False
    accounts = []
    users = {}
    companies = {}
    jobs = {}
    uow = SeedUnitOfWork(db)

    def account(key, role, name, purpose, *, verified=True):
        email = f"escenarios.{key}@example.com"
        if db.query(User).filter_by(email=email).first():
            raise ValueError(f"La cuenta {email} ya existe fuera de esta carga. No se reemplaza.")
        password = "Escenario-" + secrets.token_urlsafe(12) + "!"
        user = User(name=name + " · escenario", email=email, role=UserRole(role),
                    password_hash=hash_password(password), email_verified=verified,
                    privacy_preferences={"share_evidence": key != "privacidad", "notify_new_skills": key != "privacidad", "personalize_recommendations": key in {"senior", "junior", "transicion", "condiciones"}},
                    profile=Profile(skills=[]))
        db.add(user)
        db.flush()
        accounts.append({"key": key, "id": user.id, "role": role, "label": name,
                         "email": email, "password": password, "purpose": purpose})
        users[key] = user
        return user

    for key, name, profession, skills, purpose in CANDIDATES:
        user = account(key, "candidate", name, purpose, verified=key != "sin_correo")
        if not profession:
            continue
        senior = key not in {"junior", "transicion", "historial"}
        p = user.profile
        p.profession, p.skills = profession, skills
        p.location, p.department = "Bogotá", "Bogotá D.C."
        p.preferred_modality, p.desired_salary = "remote", 4500000 if senior else 2200000
        p.preferred_sector = "Tecnologia y software"
        p.availability = "immediate"
        p.phone = "+57 300 000 0000"
        p.experience = ("Seis años de experiencia con entregas quincenales, revisión de resultados y documentación. Diseño controles, comparo resultados con objetivos y comunico mejoras al equipo. Trayectoria ficticia para explorar la plataforma." if senior else "Un año de experiencia; proyectos de formación y colaboración en un equipo pequeño.")
        p.experiences = [{"role": profession, "company": "Proyecto ficticio Horizonte", "start_year": "2020" if senior else "2025", "end_year": "2026",
                          "description": "Construí un tablero de seguimiento, documenté controles y reduje errores de registro de 18 a 5 por mes. Experiencia simulada para revisión local."}]
        if senior:
            p.experiences.append({"role": "Asistente de proyectos", "company": "Operación ficticia Central", "start_year": "2018", "end_year": "2020",
                                  "description": "Registré entregas y soportes, organicé prioridades con el equipo y mantuve trazabilidad de cambios. Experiencia ficticia para revisar la hoja de vida."})
        p.education = "Ingeniería de sistemas" if key not in {"logistica", "creativo", "transicion"} else {"logistica": "Tecnología en logística", "creativo": "Diseño visual", "transicion": "Tecnología en gestión administrativa"}[key]
        p.educations = [{"degree": p.education, "institution": "Institución ficticia de escenarios", "start_year": "2015", "end_year": "2020"}]
        p.certifications = [{"name": "Actualización de " + skills[0] + " (simulada)", "issuer": "Academia ficticia", "year": "2025"}] if senior else []
        p.languages = [{"name": "español", "level": "C2"}, {"name": "inglés", "level": "B2" if senior else "A2"}]
        if key == "condiciones":
            p.desired_salary = 6000000
            p.preferences = {"salary_required": True, "modality_required": True, "location_required": True}
        if key == "logistica":
            p.preferred_sector, p.preferred_modality = "Logistica y transporte", "onsite"
        if key == "creativo":
            p.preferred_sector = "Cultura y artes"

    for key, name, state, purpose in COMPANIES:
        owner = account(key, "company", name, purpose, verified=key != "pendiente")
        company = Company(owner_user_id=owner.id, name=name + " (escenario ficticio)", nit="LOCAL-SCENARIO-" + key,
                          description="Organización ficticia para recorrer funciones de TalentSync. Equipo de producto y operaciones de 65 personas; sin contratación real.",
                          location="Bogotá", sector="Tecnologia y software", size="51-200 personas",
                          mission="Entregar soluciones con trazabilidad y aprendizaje continuo.", values=["Colaboración", "Transparencia"], benefits=["Formación", "Horario flexible"],
                          verification_required=True, verification_status=state,
                          verification_submission={} if state == "pending" else {"legal_name": name + " (ficticia)", "registry_reference": "SIMULACION-" + key,
                              "representative_role": "Representante del escenario", "notes": "Soporte sintético; no constituye verificación legal.", "submitted_at": (now - timedelta(days=5)).isoformat()},
                          verification_feedback={"information_required": "Completa el alcance de la actividad y la referencia de registro ficticia.", "rejected": "La referencia presentada no corresponde a la organización de este escenario.", "suspended": "Suspensión simulada para comprobar restricciones y revisión administrativa.", "verified": "Aprobación manual de demostración; sin validación legal oficial."}.get(state))
        db.add(company)
        db.flush()
        companies[key] = company

    def job(key, company, title, skills, salary=4000000, modality="remote", status="active", blind=False):
        item = Job(company_id=company.id, title=title + " · escenario", description="Desarrolla y revisa soluciones del equipo de producto. Documenta decisiones, valida resultados y coordina entregas con operaciones. Jornada de lunes a viernes, 8:00 a 17:00; acompañamiento durante el ingreso. Oferta ficticia sin contratación real.",
                   requirements="Presenta ejemplos de trabajo con " + ", ".join(skills) + ". Revisaremos responsabilidades, criterios de prueba y resultados; primera respuesta en siete días.",
                   skills=skills, skill_requirements=[{"skill": skill, "essential": index < 2, "weight": 4 if index < 2 else 2} for index, skill in enumerate(skills)],
                   salary=salary, modality=modality, status=status, blind_hiring=blind, location="Bogotá", department="Bogotá D.C.", sector="Tecnologia y software",
                   benefits=["Formación continua", "Acompañamiento inicial"], pipeline_stages=default_stages(), response_days=7,
                   created_at=now - timedelta(days=3))
        db.add(item)
        db.flush()
        jobs[key] = item
        return item

    for key, title, skills, salary, modality, state, blind in JOBS:
        job(key, companies["empresa"], title, skills, salary, modality, state, blind)
    jobs["backend"].languages = [{"name": "inglés", "level": "B2"}]
    jobs["backend"].required_education_level = "university"
    jobs["backend"].required_study_fields = ["sistemas"]
    jobs["backend"].application_questions = [
        {"id": "experiencia", "prompt": "¿Qué experiencia tienes con APIs REST?", "type": "choice", "required": True, "category": "screening", "options": ["En proyectos de formación", "En producción"], "option_scores": {"En proyectos de formación": 0, "En producción": 2}},
        {"id": "calidad", "prompt": "Explica cómo probarías una petición duplicada.", "type": "open", "required": True, "category": "work_scenario", "options": [], "option_scores": {}},
    ]
    jobs["inventarios"].sector = "Logistica y transporte"
    jobs["inventarios"].pipeline_stages = [*default_stages()[:2], {"id": "validacion", "title": "Validación operativa"}, *default_stages()[2:]]
    jobs["diseno"].sector = "Cultura y artes"
    jobs["sin_datos"].location = None
    jobs["baja_calidad"].description = "Apoyo al equipo. Oferta ficticia."
    jobs["baja_calidad"].requirements = "Con disposición para aprender."
    jobs["baja_calidad"].location = None
    jobs["baja_calidad"].benefits = []
    for index in range(6):
        job(f"riesgo_{index}", companies["riesgo"], f"Analista de seguimiento {index + 1}", ["python", "sql", "excel"], 3500000)
    for key in ["pendiente", "revision", "correcciones", "rechazada", "suspendida"]:
        job(key + "_oferta", companies[key], "Analista de operaciones", ["excel", "organizacion"], 2800000, "onsite", "paused" if key == "suspendida" else "draft")

    def application(candidate, vacancy, status="reviewing", *, stage=None, reason=None, deadline=False):
        final = status in {"hired", "accepted", "rejected"}
        row = Application(user_id=users[candidate].id, job_id=jobs[vacancy].id, status=ApplicationStatus(status),
                          pipeline_stage=stage or {"seen": "submitted", "shortlisted": "reviewing", "technical_interview": "interview", "psychometric_test": "interview", "accepted": "hired"}.get(status, status),
                          created_at=now - timedelta(days=10), first_response_at=None if deadline or status == "submitted" else now - timedelta(days=8),
                          response_due_at=None if final else now + timedelta(days=5),
                          resolution_reason=reason, released_at=now - timedelta(days=2) if reason in {"response_deadline", "candidate_withdrawn"} else None,
                          identity_revealed_at=now - timedelta(days=5) if status in {"technical_interview", "psychometric_test", "hired", "accepted"} else None,
                          interview_at=now + timedelta(days=2) if status == "technical_interview" else None,
                          candidate_feedback={} if status == "submitted" else {"source": "system" if deadline else "company", "reason_code": reason or "other", "message": "Escenario: el plazo venció sin respuesta; el cierre no evalúa tu capacidad." if deadline else "Escenario: revisamos la trayectoria y dejamos constancia del avance o cierre comunicado."},
                          recruiter_notes="Observación ficticia del reclutador: revisar el ejemplo de trabajo y sus pruebas.")
        if vacancy == "backend":
            row.screening_answers = [{"question_id": "experiencia", "question": jobs[vacancy].application_questions[0]["prompt"], "answer": "En proyectos de formación" if candidate == "junior" else "En producción", "type": "choice", "configured_adjustment": 0 if candidate == "junior" else 2, "reviewer_adjustment": 0},
                                     {"question_id": "calidad", "question": jobs[vacancy].application_questions[1]["prompt"], "answer": "Usaría la misma clave de idempotencia en dos peticiones y comprobaría un solo registro. Respuesta de demostración.", "type": "open", "configured_adjustment": 0, "reviewer_adjustment": 0}]
            row.screening_adjustment = 0 if candidate == "junior" else 2
        db.add(row)
        db.flush()
        db.add(EventLog(actor_user_id=users[candidate].id, event_type="application.transition", entity_type="application", entity_id=row.id,
                        created_at=row.created_at, details={"status": "submitted", "stage": "submitted", "job_id": row.job_id, "source": "candidate"}))
        if status != "submitted":
            db.add(EventLog(actor_user_id=companies["riesgo" if vacancy.startswith("riesgo") else "empresa"].owner_user_id,
                            event_type="application.deadline_released" if deadline else "application.withdrawn" if reason == "candidate_withdrawn" else "application.transition",
                            entity_type="application", entity_id=row.id, created_at=now - timedelta(days=2),
                            details={"status": status, "stage": row.pipeline_stage, "previous_status": "submitted", "job_id": row.job_id, "source": "system" if deadline else "candidate" if reason == "candidate_withdrawn" else "company", "reason_code": reason}))
        return row

    history = []
    for vacancy, status in zip(["backend", "datos", "frontend", "qa", "api", "soporte", "lider", "cubierta", "diseno"], ApplicationStatus, strict=True):
        history.append(application("historial", vacancy, status.value, reason="skills_gap" if status == ApplicationStatus.REJECTED else None))
    application("historial", "sin_datos", "rejected", reason="candidate_withdrawn")
    application("historial", "cerrada", "rejected", reason="position_closed")
    application("historial", "inventarios", "rejected", reason="skills_gap")
    risk_apps = [application("historial", f"riesgo_{index}", "rejected", reason="response_deadline", deadline=True) for index in range(6)]
    for candidate, vacancy, state in [
        ("senior", "backend", "technical_interview"), ("senior", "datos", "reviewing"), ("senior", "qa", "shortlisted"),
        ("senior", "api", "hired"), ("senior", "soporte", "seen"), ("senior", "lider", "reviewing"),
        ("junior", "backend", "submitted"), ("junior", "datos", "reviewing"), ("junior", "frontend", "rejected"),
        ("transicion", "datos", "reviewing"), ("transicion", "soporte", "submitted"), ("aprendizaje", "datos", "reviewing"),
        ("privacidad", "backend", "reviewing"), ("creativo", "diseno", "reviewing"),
    ]:
        application(candidate, vacancy, state, reason="skills_gap" if state == "rejected" else None)
    application("logistica", "inventarios", "reviewing", stage="validacion")
    application("condiciones", "backend", "submitted")

    from app.infrastructure.database.models import TrustIncident
    for index, state in enumerate(["open", "in_review", "confirmed", "dismissed", "appealed"]):
        incident = TrustIncident(reporter_user_id=users["historial"].id, company_id=companies["riesgo"].id, application_id=risk_apps[index].id,
                                category="ghosting", status=state, details="Simulación de un proceso sin respuesta dentro del plazo. Datos ficticios para recorrer la revisión de incidencias.",
                                shared_summary=None if state == "open" else "Incidencia simulada: se compararon las fechas del proceso y el plazo informado.",
                                appeal={"message": "Apelación ficticia: solicitamos revisar la fecha registrada y el soporte de respuesta.", "created_at": now.isoformat()} if state == "appealed" else {})
        db.add(incident)
        db.flush()
        db.add(EventLog(event_type="trust.incident_reported", entity_type="incident", entity_id=incident.id, actor_user_id=users["historial"].id, details={"company_id": incident.company_id, "reason_code": "ghosting"}))

    for key, name, role, active, purpose in TEAM:
        user = account(key, "company", name, purpose)
        if active is not None:
            db.add(CompanyMember(company_id=companies["empresa"].id, user_id=user.id, role=role, active=active, assigned_job_ids=[jobs["backend"].id]))
        else:
            organizations.invite(uow, users["empresa"], {"email": user.email, "role": role, "assigned_job_ids": [jobs["backend"].id]}, app_url=APP, mail_enabled=True)
            invitation = db.query(CompanyInvitation).filter_by(email=user.email).one()
            if key == "invitacion_vencida":
                invitation.expires_at = now - timedelta(days=1)
    # Show an accepted invitation beside pending and expired ones.
    organizations.invite(uow, users["empresa"], {"email": users["reclutador"].email, "role": "recruiter", "assigned_job_ids": [jobs["backend"].id]}, app_url=APP, mail_enabled=True)
    db.query(CompanyInvitation).filter_by(email=users["reclutador"].email).one().used_at = now - timedelta(days=1)
    account("admin", "admin", "Administración Escenarios", "Revisa todos los estados de empresas e incidencias, catálogo activo/archivado, métricas, auditoría, integraciones y laboratorio.")

    # Use the same learning validation as interactive users; no fake certificate.
    learner = users["aprendizaje"]
    for resource_id in ["project-python", "project-rest", "project-sql"]:
        learning.plans(uow, learner, resource_id, "in_progress")
    draft = db.query(LearningPlan).filter_by(user_id=learner.id, resource_id="project-rest").one()
    learning.save_journey(uow, learner, "project-rest", {"version": draft.version, "answers": {}, "activity_answers": {"sequence": [1, 3, 0, 2]}})
    published = db.query(LearningPlan).filter_by(user_id=learner.id, resource_id="project-sql").one()
    learning.save_journey(uow, learner, "project-sql", {"version": published.version, "answers": {},
        "activity_answers": {item["id"]: item["answer"] for item in activities_for("project-sql")}, "finish": True, "add_to_profile": False})
    for bank_id, passed, expired in [("sql-foundations-v1", True, False), ("python-foundations-v1", False, False), ("git-foundations-v1", True, True)]:
        started = learning.start_assessment(uow, learner, bank_id)
        bank = ASSESSMENTS[bank_id]
        answers = {item["id"]: item["answer"] if passed else (item["answer"] + 1) % len(item["choices"]) for item in bank["questions"]}
        learning.submit_assessment(uow, learner, started["id"], answers)
        attempt = db.get(AssessmentAttempt, started["id"])
        attempt.started_at = now - timedelta(days=200 if expired else 3)
        attempt.expires_at = attempt.started_at + timedelta(minutes=10)
        attempt.submitted_at = attempt.started_at + timedelta(minutes=5)
        attempt.valid_until = now - timedelta(days=20) if expired else now + timedelta(days=177) if passed else None
    started = sql_practice.start(uow, learner, "sql-paid-counts-v1")
    sql_practice.submit(uow, learner, started["id"], "SELECT c.name AS customer, COUNT(o.id) AS paid_orders FROM customers c LEFT JOIN orders o ON o.customer_id=c.id AND o.status='paid' GROUP BY c.id,c.name", SQLSandbox())

    resources = []
    for key, title, cost, active in [("gratis", "Documentación Python · demostración", "free", True), ("patrocinado", "Taller de datos · patrocinio simulado", "paid", True), ("archivado", "Ruta anterior · recurso archivado", "free", False)]:
        content = {"title": title, "provider": "Proveedor ficticio de escenarios", "skills": ["python"] if key != "patrocinado" else ["power bi"], "hours": 2,
                   "category": "technology", "kind": "documentation" if key == "gratis" else "workshop", "url": "https://example.com/formacion-demostracion", "cost": cost,
                   "instructions": "Recurso ficticio para probar edición, filtros y plan. El enlace es ilustrativo; no existe compra ni certificación real.",
                   "sponsored": key == "patrocinado", "affiliate": key == "patrocinado", "disclosure": "Patrocinio y afiliación simulados sin comisiones ni pagos." if key == "patrocinado" else ""}
        row = LearningResource(id="scenario-course-" + key, content=content, active=active)
        db.add(row)
        resources.append({"id": row.id, **content, "active": active})
    db.flush()
    full = users["plan_lleno"]
    for resource_id in ["project-python", "project-rest"]:
        learning.plans(uow, full, resource_id, "in_progress")
    db.add(LearningPlan(user_id=full.id, resource_id="scenario-course-archivado", status="in_progress", progress={}))

    for key in ["senior", "creativo", "privacidad"]:
        profile = users[key].profile
        profile.evidence = [{"id": "scenario-evidence-" + key, "kind": "portfolio" if key == "creativo" else "experience", "title": "Muestra profesional ficticia",
                             "description": "Documenté un problema, sus decisiones y resultados con ejemplos de trabajo. Evidencia sintética para revisar visualización y privacidad.",
                             "skills": profile.skills[:2], "url": None, "verified": False, "add_to_profile": False, "created_at": now.isoformat()}]
    db.flush()
    for key in ["senior", "junior", "transicion", "condiciones"]:
        for vacancy, interested in [("backend", True), ("frontend", False), ("datos", True)]:
            personalization.feedback(uow, users[key], jobs[vacancy].id, interested, nlp)
    db.add(CompanyFollower(candidate_user_id=users["senior"].id, company_id=companies["empresa"].id, min_match=60))
    for row in db.query(Application).filter(Application.user_id.in_([user.id for user in users.values()])).all():
        upsert_recommendation(uow, row.user, row.job, nlp=nlp, commit_result=False)
    for key in ["senior", "historial", "aprendizaje", "empresa", "riesgo"]:
        for index, (kind, title, action) in enumerate([
            ("application_updated", "Avance del proceso · escenario", "/postulaciones" if users[key].role == "candidate" else "/empresa/postulaciones"),
            ("company_job_match", "Oportunidad para revisar · escenario", "/vacantes" if users[key].role == "candidate" else "/empresa/vacantes"),
            ("trust_incident", "Revisión de confianza · escenario", "/confianza"),
        ]):
            db.add(Notification(user_id=users[key].id, type=kind, title=title, body="Aviso ficticio para probar categorías, lectura individual y lectura de todos los avisos.", action_url=action, is_read=index == 2))
    for key in ["sin_correo", "pendiente"]:
        account_security.request_action(uow, users[key].email, "verify", app_url=APP, mail_enabled=True)
    db.flush()
    invitations = []
    for key in ["invitado", "invitacion_vencida"]:
        mail = db.query(MailMessage).filter_by(recipient=users[key].email).one()
        link = next(part for part in mail.body.split() if part.startswith(APP))
        invitations.append({"key": key, "url": link, "expired": key == "invitacion_vencida"})
    report = {"bundle": BUNDLE, "created_at": now.isoformat(), "accounts": accounts,
              "companies": {key: row.id for key, row in companies.items()}, "jobs": {key: row.id for key, row in jobs.items()},
              "invitations": invitations, "resources": resources,
              "counts": {"users": len(accounts), "candidates": len(CANDIDATES), "companies": len(companies), "team_accounts": len(TEAM), "admins": 1,
                         "jobs": len(jobs), "incidents": 5, "resources": len(resources)}}
    report["counts"]["applications"] = db.query(Application).filter(Application.user_id.in_([user.id for user in users.values()])).count()
    db.add(EventLog(event_type="demo.scenarios_created", entity_type=BUNDLE, details=report["counts"]))
    db.flush()
    return report, True


def write_guide(folder, report):
    def url(path):
        return f"[{path}]({APP}{path})"

    lines = ["# Escenarios funcionales de TalentSync", "", f"Preparados: {report['created_at'][:10]}. Solo en la base aislada local.", "",
             "## Empieza aquí", "", "1. Abre la aplicación y cierra la sesión actual antes de cambiar de cuenta.",
             f"Cuentas nuevas: {report['counts']['users']}; empresas: {report['counts']['companies']}; vacantes: {report['counts']['jobs']}; postulaciones: {report['counts']['applications']}; incidencias: 5.", "",
             "2. Candidato: `senior` para el perfil completo; `aprendizaje` para resultados; `historial` para todos los procesos.",
             "3. Empresa: `empresa` para gestión completa; `riesgo` para incidencias; el resto para verificación y permisos.",
             "4. Administrador: `admin`; configura tu autenticador en Seguridad en el primer ingreso y conserva los códigos de recuperación.",
             "5. Los correos y contraseñas de esta guía pertenecen a cuentas nuevas. Las anteriores se conservan.", "",
             "## Accesos privados", "", "Este archivo contiene claves locales. No compartir ni incorporar a Git.", ""]
    for role, title, portal in [("candidate", "Candidato", "/login"), ("company", "Empresa y equipo", "/empresa/login"), ("admin", "Administrador", "/acceso-administracion")]:
        lines.extend([f"### {title}", "", f"Entrada: {url(portal)}", "", "| Cuenta | Correo | Contraseña | Escenario |", "| --- | --- | --- | --- |"])
        for account in report["accounts"]:
            if account["role"] == role:
                lines.append(f"| {account['key']} — {account['label']} | {account['email']} | `{account['password']}` | {account['purpose']} |")
        lines.append("")
    lines.extend(["## Recorrido del candidato", "", "| Cuenta | Vista | Qué probar y resultado esperado |", "| --- | --- | --- |",
                  f"| nuevo | {url('/bienvenida')} y {url('/perfil')} | Completar cargo, formación y condiciones; cargar tu CV ficticio, corregir extracción, cambiar estilo/color y descargar el PDF. Puedes descargar primero el CV de senior y cargarlo aquí como archivo ficticio. |",
                  f"| sin_correo | {url('/seguridad')}, {url('/desarrollo/correos')} | Solicitar confirmación y usar el enlace local. Recuperar acceso desde el login; reenviar si el enlace de 30 minutos ya venció. |",
                  f"| senior | {url('/recomendaciones')} | Abrir compatibilidad: mapa por habilidades, requisitos ponderados, formación, idiomas y evidencias. Frontend tiene más de seis ejes; puedes cambiar de grupo. |",
                  f"| junior / transicion | {url('/recomendaciones')} | Comparar brechas y bases relacionadas, formación sugerida, umbral y preferencias. Añadir un recurso y comprobar su salida del catálogo. |",
                  f"| senior | {url('/vacantes')} | Buscar, filtrar, paginar, guardar/ocultar/restaurar, desactivar/reactivar consentimiento y seguir/dejar de seguir Horizonte desde su perfil. |",
                  f"| condiciones | {url('/recomendaciones')} y {url('/perfil#preferencias')} | Salario 6.000.000, remota y Bogotá son imprescindibles. Activar el filtro: Backend cumple; Datos entra en conflicto; condiciones ausentes se mantienen visibles cuando no hay conflicto conocido. Cambiar marcas no altera el índice de habilidades. |",
                  f"| aprendizaje | {url('/aprendizaje')} | Retos y cursos separados; Mi plan con Python sin empezar, REST en borrador y SQL publicado. Mis resultados: SQL aprobado, Python no aprobado, Git caducado y SQL práctico aprobado. Los intentos están etiquetados como simulados en esta guía, no como certificados reales. |",
                  f"| aprendizaje | {url('/aprendizaje')} | Iniciar cualquier otro reto, responder, revisar, entregar y comprobar el plazo/cooldown. Continuar REST y publicar; editar la publicación sin duplicar la evidencia. SQL conserva otros tres retos para comenzar. |",
                  f"| plan_lleno | {url('/aprendizaje')} | Tres recursos activos. Intentar un cuarto produce el límite; abandonar uno permite añadir otro. El recurso archivado permanece en su plan y se puede continuar. |",
                  f"| historial | {url('/postulaciones')} | Recibida, vista, revisión, preselección, entrevista técnica, prueba, aceptada, contratada y rechazada; también retirada, cierre por plazo y vacante cerrada. Abrir seguimiento e historial. Backend tiene preguntas y respuestas. |",
                  f"| historial | {url('/confianza')} | Incidencias recibida, en revisión, confirmada, desestimada y apelada. Crear otro reporte, comprobar duplicado pendiente y ver la actualización tras una decisión administrativa. |",
                  f"| senior / historial | {url('/notificaciones')} | Avisos leídos y sin leer; categorías, abrir destino, marcar uno o todos. |",
                  f"| privacidad | {url('/seguridad')} y {url('/vacantes')} | Tres consentimientos apagados. Personalización no guarda decisiones hasta activarla; empresa no ve evidencias privadas. Notificaciones y procesos vacíos/sencillos. |",
                  f"| logistica / creativo | {url('/aprendizaje')} | Áreas no tecnológicas: logística y diseño. Elegir otras áreas para revisar ventas, servicio, salud administrativa, finanzas, educación y competencias transversales. |", "",
                  "## Recorrido de empresa", "", "| Cuenta | Vista | Qué probar y resultado esperado |", "| --- | --- | --- |",
                  f"| empresa | {url('/empresa/vacantes')} | Ofertas activas, borradores, pausada, cerrada y cubierta. Crear/editar/publicar/pausar/cerrar, preguntas abiertas y de selección, idiomas y plazos. |",
                  f"| empresa | {url('/empresa/calidad')} | Comparar Backend completo con Asistente incompleto; editar salario con miles, requisitos esenciales/deseables y pesos. |",
                  f"| empresa | {url('/empresa/postulaciones')} | Backend: Elena en entrevista con identidad visible, Tomás recibido y Lucía en revisión con identidad protegida. Mover, guardar y recargar. Inventarios usa Validación operativa personalizada. |",
                  f"| empresa | {url('/empresa/talento')} | Buscar talento, ver compatibilidad y respuestas. En selección ciega se abre ficha profesional anónima; al avanzar a entrevista se revela identidad. En Datos y Diseño la identidad ya es visible. |",
                  f"| empresa | {url('/empresa/equipo')} y {url('/empresa/perfil')} | Editar organización, logo/portada; revisar permisos, asignaciones e invitaciones pendiente/aceptada/vencida; invitar, cancelar, retirar/reactivar accesos. |",
                  f"| reclutador | {url('/empresa')} | Gestión de vacantes y postulaciones; no puede modificar propiedad ni administrar permisos. |",
                  f"| entrevistador | {url('/empresa/equipo')} | Consultar únicamente seguimiento de Backend asignado. Intentar acceder a vacantes/talento confirma restricción de permisos. |",
                  f"| revocado | {url('/empresa/equipo')} | Acceso retirado; el propietario puede reactivarlo. No es una cuenta rota. |",
                  f"| invitado / invitacion_vencida | {url('/desarrollo/correos')} | Abrir enlace de la sección siguiente. Invitado acepta una vez; el vencido muestra indisponibilidad. |",
                  f"| riesgo | {url('/confianza')} | Seis cierres por plazo, dos incidencias confirmadas/apeladas y visibilidad reducida. Apelar la confirmada; la apelada ya tiene mensaje de revisión. |",
                  f"| empresa / vacia | {url('/confianza')} | Comparar confianza con suficientes respuestas favorables frente a empresa sin observaciones. |",
                  f"| pendiente / revision / correcciones / rechazada / suspendida | {url('/empresa/equipo')} | Estados sin presentar/en revisión/correcciones/rechazo/suspensión. Las restricciones corresponden a cada estado. Confirmar el correo pendiente antes de presentar. |", "",
                  "## Invitaciones listas", ""])
    for item in report["invitations"]:
        lines.append(f"- Cuenta `{item['key']}`: [abrir invitación {'vencida' if item['expired'] else 'pendiente'}]({item['url']}). Inicia sesión con esa cuenta empresarial, no con el propietario.")
    lines.extend(["", "## Recorrido del administrador", "", "| Vista | Qué probar |", "| --- | --- |",
                  f"| {url('/admin/verificaciones')} | Buscar organizaciones por Escenario; revisar solicitudes en seis estados, filtrar, paginar, aprobar/pedir información/rechazar/suspender y comprobar el cambio entrando como esa empresa. |",
                  f"| {url('/admin/ecosistema')} | Mapa de oferta/demanda con búsqueda y paginación; directorio con empresas favorables/sin muestra/en riesgo, detalle y filtros. Revisar los cinco estados de incidencias y registrar una decisión. Ejecutar auditoría para generar métricas reales de esta base sintética. |",
                  f"| {url('/admin/aprendizaje')} | Tres recursos administrables: gratuito, patrocinado/de pago y archivado. Crear con asistente, editar, archivar/desarchivar, filtrar e importar `catalogo-ejemplo.json` de esta carpeta. El enlace de ejemplo es ilustrativo. |",
                  f"| {url('/admin/modelos')} | Funcionamiento, Integraciones y Laboratorio; muestra insuficiente honesta, evaluación local y su historial. No se mezclan datos ficticios con entrenamiento real. |",
                  f"| {url('/administracion')} y {url('/vacantes')} | Gestión de usuarios/empresas/ofertas y filtros; importación CSV/XLSX de vacantes desde archivos ficticios preparados. |",
                  f"| {url('/seguridad')} | Alta MFA, códigos de recuperación, dispositivos y revocación de sesiones. Acceso de admin únicamente en su portal. |", "",
                  "## Límites de esta demostración", ""])
    lines.extend(f"- {boundary}" for boundary in BOUNDARIES)
    lines.extend(["", "## Repetir la preparación", "", "Desde el proyecto: `backend/.venv/Scripts/python.exe -X utf8 scripts/local.py seed-scenarios`.",
                  "La carga es aditiva e idempotente. Conserva contraseñas, cambios de estado, planes y perfiles. No vuelve a crear invitaciones consumidas ni reinicia decisiones. Existe una copia de la base anterior a la carga en `.local/before-functional-scenarios.sqlite3`.", ""])
    lines.extend(["## Vacantes de referencia", "", "| Escenario | Abrir vacante |", "| --- | --- |"])
    for key, job_id in report["jobs"].items():
        lines.append(f"| {key} | {url('/vacantes/' + str(job_id))} |")
    lines.extend(["", "## Archivos de importación", "", "- `catalogo-ejemplo.json`: un recurso administrable válido, con proveedor ficticio y enlace ilustrativo.",
                  "- `vacantes-ejemplo.csv` y `vacantes-ejemplo.xlsx`: las mismas dos ofertas externas sintéticas. Importar primero CSV y después XLSX permite comprobar actualización sin duplicados.",
                  "- `vacantes-con-error.csv`: una fila válida y otra con salario no numérico, para comprobar el informe de errores por fila.", ""])
    (folder / "GUIA_ESCENARIOS.md").write_text("\n".join(lines), encoding="utf-8")
    sample = {"resources": [{key: value for key, value in report["resources"][0].items() if key != "id"}]}
    sample["resources"][0]["title"] = "Documentación para importar · ejemplo"
    (folder / "catalogo-ejemplo.json").write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")
    from openpyxl import Workbook

    from app.application.use_cases.job_imports import IMPORT_HEADERS
    start = datetime.fromisoformat(report["created_at"])
    rows = [{"fuente": "Escenarios ficticios", "id_externo": f"SCENARIO-IMPORT-{index}", "empresa": "Importación Demostración (ficticia)",
             "cargo": title, "descripcion": "Oferta externa ficticia para comprobar importación, búsqueda y datos incompletos; sin contratación real.",
             "requisitos": "Experiencia con Python y SQL y ejemplos de trabajo documentados.", "sector": "Tecnologia y software",
             "enlace_externo": f"https://example.com/oferta-demostracion-{index}", "fecha_publicacion": start.date().isoformat(),
             "fecha_vencimiento": (start + timedelta(days=90)).date().isoformat(), "salario": "5000000" if index == 1 else "",
             "departamento": "Bogotá D.C.", "ciudad": "Bogotá", "modalidad": "remoto", "tipo_contrato": "full_time", "habilidades": "python|sql",
             "beneficios": "Formación", "idiomas": "", "sitio_empresa": "https://example.com", "descripcion_empresa": "Empresa ficticia de importación."}
            for index, title in enumerate(["Analista Python · importación completa", "Analista SQL · salario por acordar"], 1)]
    for name, data in [("vacantes-ejemplo.csv", rows), ("vacantes-con-error.csv", [rows[0], {**rows[1], "salario": "salario incorrecto"}])]:
        with (folder / name).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=IMPORT_HEADERS)
            writer.writeheader()
            writer.writerows(data)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Vacantes ficticias"
    sheet.append(list(IMPORT_HEADERS))
    for row in rows:
        sheet.append([row.get(key, "") for key in IMPORT_HEADERS])
    workbook.save(folder / "vacantes-ejemplo.xlsx")


def main():
    local = ROOT / ".local"
    database = local / "talentsync.sqlite3"
    if settings.environment != "development" or settings.database_url != f"sqlite:///{database.as_posix()}":
        raise SystemExit("Solo admite la base SQLite aislada de .local/.")
    folder = local / "escenarios"
    folder.mkdir(exist_ok=True)
    backup = local / "before-functional-scenarios.sqlite3"
    if not backup.exists():
        with sqlite3.connect(database) as source, sqlite3.connect(backup) as target:
            source.backup(target)
    file = folder / "accounts.json"
    registry = json.loads(file.read_text(encoding="utf-8")) if file.exists() else {}
    with SessionLocal() as db:
        report, created = seed(db, registry, nlp=text_processor)
        # Persist keys before commit; if commit fails, the next run creates a fresh
        # atomic bundle. A post-commit interruption remains recoverable.
        temporary = folder / "accounts.pending.json"
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(file)
        db.commit()
    write_guide(folder, report)
    print(json.dumps({"created": created, **report["counts"], "guide": ".local/escenarios/GUIA_ESCENARIOS.md"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
