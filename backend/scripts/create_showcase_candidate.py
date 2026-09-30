"""Create or refresh a complete candidate account with a populated pipeline."""

import argparse
import json
from datetime import datetime, timedelta

from pydantic import EmailStr, TypeAdapter

from app.application.use_cases.matching import upsert_recommendation
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.infrastructure.database.models import Application, Job, Profile, User
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.nlp.text_processor import text_processor
from app.infrastructure.security.passwords import hash_password

DEMO_SKILLS = [
    "análisis de datos",
    "sql",
    "power bi",
    "excel avanzado",
    "python",
    "api rest",
    "gestión de proyectos",
    "scrum",
    "comunicación efectiva",
    "presentaciones ejecutivas",
    "servicio al cliente",
    "gestión de riesgos",
    "trabajo en equipo",
]


def create_candidate(email: str, password: str) -> dict[str, int | str]:
    email = str(TypeAdapter(EmailStr).validate_python(email)).lower()
    if len(password.encode("utf-8")) < 8:
        raise ValueError("La contraseña necesita al menos 8 caracteres")
    now = datetime.utcnow()
    with SessionLocal() as session:
        candidate = session.query(User).filter(User.email == email).first()
        if candidate is None:
            candidate = User(
                name="Camila Restrepo Gómez",
                email=email,
                password_hash=hash_password(password),
                role=UserRole.CANDIDATE,
                profile=Profile(),
            )
            session.add(candidate)
            session.flush()
        elif candidate.role != UserRole.CANDIDATE:
            raise ValueError("El correo pertenece a una cuenta que no es candidata")
        else:
            candidate.password_hash = hash_password(password)

        candidate.name = "Camila Restrepo Gómez"
        profile = candidate.profile or Profile(user_id=candidate.id)
        candidate.profile = profile
        summary = (
            "Ingeniera de sistemas con seis años de experiencia transformando datos y necesidades "
            "del negocio en productos digitales medibles. Ha liderado tableros financieros, "
            "automatizaciones e integraciones, coordinando equipos ágiles y comunicando decisiones "
            "a áreas técnicas, comerciales y de servicio."
        )
        profile.profession = "Ingeniera de sistemas y analista de datos"
        profile.skills = DEMO_SKILLS
        profile.experience = summary
        profile.education = "Ingeniería de Sistemas — Universidad de Antioquia"
        profile.location = "Medellín"
        profile.department = "Antioquia"
        profile.availability = "Inmediata"
        profile.preferred_modality = "hybrid"
        profile.preferred_sector = "Tecnologia y software"
        profile.desired_salary = 6_500_000
        profile.phone = "+57 315 624 9081"
        profile.experiences = [
            {
                "role": "Líder de analítica digital",
                "company": "Fintech Andina S.A.S.",
                "start_year": "2023",
                "end_year": "Presente",
                "description": "Lidera cinco personas, define indicadores y construye soluciones con SQL, Python y Power BI. Redujo 35 % el tiempo de preparación de reportes ejecutivos.",
            },
            {
                "role": "Analista de datos senior",
                "company": "Servicios Financieros Integrados",
                "start_year": "2020",
                "end_year": "2023",
                "description": "Modeló información financiera, automatizó controles de calidad y presentó hallazgos de riesgo y experiencia de cliente a líderes de negocio.",
            },
            {
                "role": "Desarrolladora de soluciones",
                "company": "Laboratorio Digital Colombia",
                "start_year": "2018",
                "end_year": "2020",
                "description": "Desarrolló servicios REST, consultas SQL y pruebas funcionales dentro de equipos Scrum, documentando entregas y acompañando usuarios.",
            },
        ]
        profile.educations = [
            {
                "degree": "Ingeniería de Sistemas",
                "institution": "Universidad de Antioquia",
                "start_year": "2013",
                "end_year": "2018",
            },
            {
                "degree": "Especialización en Analítica",
                "institution": "Universidad EAFIT",
                "start_year": "2021",
                "end_year": "2022",
            },
        ]
        profile.certifications = [
            {
                "name": "Microsoft Power BI Data Analyst",
                "issuer": "Microsoft",
                "year": "2025",
            },
            {
                "name": "Professional Scrum Master I",
                "issuer": "Scrum.org",
                "year": "2024",
            },
            {"name": "SQL for Data Science", "issuer": "Coursera", "year": "2023"},
        ]
        profile.languages = [
            {"name": "español", "level": "NATIVE"},
            {"name": "inglés", "level": "B2"},
            {"name": "portugués", "level": "A2"},
        ]
        profile.cv_text = " ".join(
            [summary, profile.profession, *DEMO_SKILLS]
            + [item["description"] for item in profile.experiences]
        )
        profile.embedding = text_processor.analyze_cv(profile.cv_text).embedding
        profile.updated_at = now
        session.flush()

        jobs = (
            session.query(Job)
            .filter(Job.source_kind == "internal", Job.status == "active")
            .order_by(Job.created_at.desc())
            .all()
        )
        scored_jobs = sorted(
            jobs,
            key=lambda job: len(set(job.skills or []) & set(DEMO_SKILLS)),
            reverse=True,
        )
        stages = [
            (ApplicationStatus.TECHNICAL_INTERVIEW, "interview"),
            (ApplicationStatus.SHORTLISTED, "reviewing"),
            (ApplicationStatus.REVIEWING, "reviewing"),
            (ApplicationStatus.SUBMITTED, "submitted"),
            (ApplicationStatus.SEEN, "submitted"),
        ]
        uow = SqlAlchemyUnitOfWork(session)
        applications = 0
        for index, job in enumerate(scored_jobs[:6]):
            recommendation = upsert_recommendation(
                uow, candidate, job, nlp=text_processor, commit_result=False
            )
            application = (
                session.query(Application)
                .filter(
                    Application.user_id == candidate.id, Application.job_id == job.id
                )
                .first()
            )
            if application is None:
                application = Application(user_id=candidate.id, job_id=job.id)
                session.add(application)
            status, stage = stages[index % len(stages)]
            application.status = status
            application.pipeline_stage = stage
            application.created_at = now - timedelta(days=index + 2)
            application.screening_adjustment = 3 if index < 3 else 1
            application.screening_answers = [
                {
                    "question_id": "experience",
                    "question": "¿Qué experiencia se relaciona con el cargo?",
                    "type": "open",
                    "answer": "Seis años liderando analítica, automatización y productos digitales con resultados medibles.",
                    "reviewer_adjustment": 2,
                },
                {
                    "question_id": "motivation",
                    "question": "¿Por qué te interesa esta oportunidad?",
                    "type": "open",
                    "answer": "Quiero aplicar mi experiencia técnica y de negocio para mejorar decisiones y experiencias de clientes.",
                    "reviewer_adjustment": 1,
                },
            ]
            if index == 0:
                application.interview_at = now + timedelta(days=3, hours=2)
                application.recruiter_notes = (
                    "Perfil sólido; validar liderazgo técnico y disponibilidad."
                )
            applications += 1
            recommendation.created_at = now - timedelta(days=index + 1)

        for job in scored_jobs[6:20]:
            upsert_recommendation(
                uow, candidate, job, nlp=text_processor, commit_result=False
            )
        session.commit()
        return {
            "user_id": candidate.id,
            "email": email,
            "applications": applications,
            "recommendations": min(len(scored_jobs), 20),
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crear candidato demostrativo completo"
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    arguments = parser.parse_args()
    try:
        print(
            json.dumps(
                create_candidate(arguments.email, arguments.password),
                ensure_ascii=False,
            )
        )
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
