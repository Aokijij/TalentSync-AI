"""Add richer fictional review data only to the owned isolated SQLite database."""
import json
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from app.core.config import settings
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.infrastructure.database.models import (
    Application,
    Company,
    EventLog,
    Job,
    Profile,
    User,
)
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.nlp.text_processor import text_processor
from app.infrastructure.security.passwords import hash_password
from scripts.demo_scenarios import SCENARIOS

ROOT = Path(__file__).resolve().parents[2]


def main():
    local = ROOT / ".local"
    database = local / "talentsync.sqlite3"
    if settings.environment != "development" or settings.database_url != f"sqlite:///{database.as_posix()}":
        raise SystemExit("Solo admite la base SQLite aislada de .local/.")
    if not (local / "before-rich-demo.sqlite3").exists():
        with sqlite3.connect(database) as source, sqlite3.connect(local / "before-rich-demo.sqlite3") as backup:
            source.backup(backup)
    credentials = local / "review-accounts.json"
    saved = json.loads(credentials.read_text(encoding="utf-8")) if credentials.exists() else []
    by_email = {row["email"]: row for row in saved}
    now = datetime.utcnow()
    counts = {"new_companies": 0, "new_candidates": 0, "new_jobs": 0, "new_applications": 0}
    with SessionLocal() as db:
        def account(key, role, label):
            email = f"revision.demo_{key}@example.com"
            user = db.query(User).filter_by(email=email).first()
            if user is None:
                password = "Local-" + secrets.token_urlsafe(12) + "!"
                user = User(name=label, email=email, role=UserRole(role), password_hash=hash_password(password), email_verified=True)
                user.profile = Profile(skills=[])
                db.add(user)
                db.flush()
                by_email[email] = {"role": role, "label": label, "email": email, "password": password, "first_login_mfa_setup": role == "admin"}
                counts["new_companies" if role == "company" else "new_candidates"] += 1
            elif email not in by_email:
                raise SystemExit("Cuenta existente sin credencial privada; no se cambia su contraseña.")
            return user

        for scenario in SCENARIOS:
            owner = account(scenario["key"], "company", scenario["name"] + " · demo")
            company = db.query(Company).filter_by(nit="LOCAL-RICH-" + scenario["key"]).first()
            if company is None:
                company = Company(owner_user_id=owner.id, name=scenario["name"] + " (demostración)", nit="LOCAL-RICH-" + scenario["key"],
                    description=scenario["description"] + " Empresa y ofertas ficticias para revisión local.", sector=scenario["sector"], location=scenario["city"], size="11-200 personas",
                    mission="Mejorar el servicio con trabajo colaborativo y decisiones medibles.", values=["Colaboración", "Aprendizaje", "Transparencia"], benefits=["Formación continua", "Acompañamiento de ingreso"],
                    verification_required=True, verification_status="verified", verification_feedback="Organización de demostración; revisión local, sin validación oficial.")
                db.add(company)
                db.flush()
            jobs = []
            for index, (title, skills, salary, modality, tasks, requirements) in enumerate(scenario["positions"]):
                job = db.query(Job).filter_by(company_id=company.id, title=title).first()
                if job is None:
                    job = Job(company_id=company.id, title=title, sector=scenario["sector"], salary=salary, modality=modality,
                        location=scenario["city"], department=scenario["department"], blind_hiring=index % 2 == 1, employment_type="full_time",
                        description=f"{tasks}. Trabajarás con un equipo de 4 a 8 personas, revisarás resultados cada semana y documentarás tus entregas. Jornada de lunes a viernes, 8:00 a 17:00, con una hora de descanso. Oferta de demostración, sin contratación real.",
                        requirements=f"Buscamos {requirements}. Formación técnica, tecnológica o profesional relacionada. Evaluaremos ejemplos de trabajo y una conversación sobre decisiones del cargo. Primera respuesta dentro de siete días.",
                        skills=skills, skill_requirements=[{"skill": skill, "essential": number < 2, "weight": 3 if number < 2 else 1} for number, skill in enumerate(skills)],
                        benefits=["Plan de formación", "Horario acordado", "Acompañamiento durante el primer mes"], languages=[{"name": "inglés", "level": "B1"}] if scenario["key"] == "tecnologia" else [],
                        created_at=now - timedelta(days=index + 1), embedding=text_processor.embed(f"{title}. {tasks}. {' '.join(skills)}"))
                    db.add(job)
                    db.flush()
                    counts["new_jobs"] += 1
                jobs.append(job)
            for index, name in enumerate(scenario["names"]):
                title, skills, salary, modality, tasks, _ = scenario["positions"][index]
                user = account(f"{scenario['key']}_{index + 1}", "candidate", name + " · demo")
                profile = user.profile
                candidate_skills = list(dict.fromkeys([*skills, "comunicacion", "organizacion", *(skill for position in scenario["positions"] for skill in position[1])]))[:6]
                # Reruns never overwrite an edited profile or published evidence.
                if not profile.profession:
                    profile.profession = title
                    profile.skills = candidate_skills
                    profile.location = scenario["city"]
                    profile.department = scenario["department"]
                    profile.preferred_modality = modality
                    profile.preferred_sector = scenario["sector"]
                    profile.availability = "two_weeks"
                    profile.desired_salary = salary
                    profile.phone = "+57 300 000 0000"
                    profile.experience = f"{title} con 6 años de experiencia. {scenario['achievement']} Interés en colaborar en proyectos con objetivos y seguimiento claros."
                    profile.education = scenario["degree"]
                    profile.experiences = [{"role": title, "company": "Equipo " + scenario["name"] + " (demo)", "start_year": "2022", "end_year": "2026", "description": tasks + ". " + scenario["achievement"]},
                        {"role": "Asistente de " + scenario["sector"].lower(), "company": "Operación regional de demostración", "start_year": "2020", "end_year": "2022", "description": "Registré entregas, coordiné prioridades con el equipo y documenté mejoras de tiempos y calidad."}]
                    profile.educations = [{"degree": scenario["degree"], "institution": scenario["institution"], "start_year": "2016", "end_year": "2020"}]
                    profile.certifications = [{"name": "Actualización en " + skills[0], "issuer": "Academia de demostración", "year": "2025"}]
                    profile.languages = [{"name": "español", "level": "C2"}, {"name": "inglés", "level": "B1"}]
                    profile.embedding = text_processor.embed(f"{title}. {profile.experience}. {' '.join(profile.skills)}")
                if profile.skills == skills + ["comunicacion", "organizacion"]:
                    profile.skills = candidate_skills
                    profile.embedding = text_processor.embed(f"{title}. {profile.experience}. {' '.join(profile.skills)}")
                old_summary = f"{title} con {3 + index} años de experiencia. {scenario['achievement']} Interés en colaborar en proyectos con objetivos y seguimiento claros."
                if profile.experience == old_summary:
                    profile.experience = old_summary.replace(f"{3 + index} años", "6 años", 1)
                    profile.embedding = text_processor.embed(f"{title}. {profile.experience}. {' '.join(profile.skills)}")
                for offset in [0, 1]:
                    job = jobs[(index + offset) % len(jobs)]
                    if db.query(Application).filter_by(user_id=user.id, job_id=job.id).first():
                        continue
                    interviewing = offset == 1 and index == 1
                    application = Application(user_id=user.id, job_id=job.id, status=ApplicationStatus.TECHNICAL_INTERVIEW if interviewing else ApplicationStatus.REVIEWING,
                        pipeline_stage="technical_interview" if interviewing else "reviewing", created_at=now - timedelta(days=2), first_response_at=now - timedelta(days=1),
                        response_due_at=now + timedelta(days=5), identity_revealed_at=now - timedelta(hours=6) if interviewing and job.blind_hiring else None,
                        candidate_feedback={"message": "Revisamos tu trayectoria. Te comunicaremos el siguiente paso dentro del plazo informado.", "source": "company"})
                    db.add(application)
                    db.flush()
                    db.add(EventLog(actor_user_id=user.id, event_type="application.created", entity_type="application", entity_id=application.id, created_at=application.created_at, details={"demo": True}))
                    db.add(EventLog(actor_user_id=owner.id, event_type="application.status_changed", entity_type="application", entity_id=application.id, created_at=application.first_response_at, details={"status": application.status.value, "demo": True}))
                    counts["new_applications"] += 1

        # Normalize labels from the first local run to the supported sector catalog.
        old_sectors = {"Tecnología y software": "Tecnologia y software", "Finanzas y contabilidad": "Finanzas y banca", "Logística y transporte": "Logistica y transporte", "Educación y formación": "Educacion", "Diseño y creatividad": "Cultura y artes"}
        for company in db.query(Company).filter(Company.nit.like("LOCAL-RICH-%")):
            company.sector = old_sectors.get(company.sector, company.sector)
            for job in company.jobs:
                job.sector = old_sectors.get(job.sector, job.sector)
                job.languages = [{**row, "name": row["name"].lower()} for row in job.languages or []]
        for user in db.query(User).filter(User.email.like("revision.demo_%@example.com")):
            user.profile.preferred_sector = old_sectors.get(user.profile.preferred_sector, user.profile.preferred_sector)
            user.profile.languages = [{**row, "name": row["name"].lower()} for row in user.profile.languages or []]
        # Enrich only the original review fixtures, keeping their names, passwords and user additions.
        for email, role in [("revision.ventas@example.com", "Asesora comercial"), ("revision.finanzas@example.com", "Auxiliar contable"), ("revision.logistica@example.com", "Auxiliar de logística"), ("revision.salud@example.com", "Auxiliar administrativa en salud")]:
            user = db.query(User).filter_by(email=email).first()
            if user and not user.profile.experiences:
                profile = user.profile
                profile.experiences = [{"role": role, "company": "Servicios regionales (demostración)", "start_year": "2022", "end_year": "2026", "description": "Gestioné solicitudes, registré resultados y coordiné tareas con un equipo de cinco personas. Organicé una lista de verificación que redujo errores en un 15%."}]
                profile.educations = profile.educations or [{"degree": "Tecnología en gestión administrativa", "institution": "Instituto técnico de demostración", "start_year": "2018", "end_year": "2021"}]
                profile.languages = profile.languages or [{"name": "español", "level": "C2"}]
                profile.location = profile.location or "Bogotá"
                profile.department = profile.department or "Bogotá D.C."
                profile.availability = profile.availability or "two_weeks"
                profile.phone = profile.phone or "+57 300 000 0000"
                profile.experience = profile.experience or f"{role} con cuatro años de experiencia en atención, registros y seguimiento de resultados."
                profile.embedding = text_processor.embed(f"{profile.profession}. {profile.experience}. {' '.join(profile.skills)}")
        for company in db.query(Company).filter(Company.nit.in_(["LOCAL-REVIEW-comercio", "LOCAL-REVIEW-operaciones", "LOCAL-REVIEW-bienestar"])):
            for job in company.jobs:
                if job.description and job.description.startswith("Vacante ficticia de revisión local."):
                    job.description = f"{job.title}: atiende las actividades del área, registra información en hojas de cálculo y comunica avances al equipo. Revisa prioridades al inicio de la jornada y documenta novedades al cierre. Equipo de seis personas; horario de lunes a viernes de 8:00 a 17:00, con una hora de descanso. Oferta ficticia de demostración."
                    job.requirements = f"Formación técnica o tecnológica relacionada. Un año de experiencia en tareas del área y ejemplos de uso de {', '.join(job.skills)}. Proceso con revisión de trayectoria y entrevista; respuesta inicial en siete días."
                    job.embedding = text_processor.embed(f"{job.title}. {job.description}. {' '.join(job.skills)}")
        db.commit()
    credentials.write_text(json.dumps(list(by_email.values()), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Accesos para revisión local", "", "Datos ficticios, disponibles solo en este entorno. Se conservan las contraseñas anteriores.", "", "Empresas: MFA opcional localmente; si ya lo activaste, se sigue solicitando. Administrador: MFA obligatorio.", "", "| Rol | Perfil | Correo | Contraseña |", "| --- | --- | --- | --- |"]
    for row in sorted(by_email.values(), key=lambda row: (row["role"], row["email"])):
        lines.append(f"| {row['role']} | {row['label']} | {row['email']} | {row['password']} |")
    (local / "ACCESOS_REVISION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
