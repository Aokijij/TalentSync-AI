"""Create an idempotent private company workspace for product presentations."""

import argparse
import json
import secrets
from datetime import datetime, timedelta
from getpass import getpass

from pydantic import EmailStr, TypeAdapter

from app.application.use_cases.matching import upsert_recommendation
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.infrastructure.database.models import Application, Company, Job, Profile, User
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.nlp.text_processor import text_processor
from app.infrastructure.security.passwords import hash_password

SHOWCASE_NIT = "TS-SHOWCASE-001"
PIPELINE = [
    {"id": "submitted", "title": "Recibidas"},
    {"id": "reviewing", "title": "En revisión"},
    {"id": "interview", "title": "Entrevista"},
    {"id": "hired", "title": "Contratados"},
    {"id": "rejected", "title": "No seleccionados"},
]

JOBS = (
    (
        "Analista de experiencia del cliente",
        ["servicio al cliente", "comunicación", "crm", "análisis de datos", "excel"],
        "Acompañar solicitudes de clientes, analizar motivos de contacto y proponer mejoras medibles para la experiencia.",
        "Experiencia atendiendo personas, redacción clara y manejo básico de indicadores.",
        "Ventas y comercio",
    ),
    (
        "Profesional de selección",
        ["selección", "entrevistas", "recursos humanos", "comunicación", "excel"],
        "Coordinar procesos de selección, entrevistas por competencias y comunicación con candidatos y líderes.",
        "Formación en psicología o áreas administrativas y experiencia en selección.",
        "Recursos humanos",
    ),
    (
        "Analista de operaciones",
        ["operaciones", "indicadores", "excel", "mejora continua", "trabajo en equipo"],
        "Dar seguimiento a la operación diaria, consolidar indicadores y coordinar planes de mejora con diferentes equipos.",
        "Experiencia en procesos operativos, hojas de cálculo y seguimiento de planes de acción.",
        "Logistica y transporte",
    ),
    (
        "Ejecutivo de cuenta",
        ["ventas", "negociación", "crm", "servicio al cliente", "comunicación"],
        "Gestionar relaciones con clientes, detectar oportunidades y hacer seguimiento ordenado a acuerdos comerciales.",
        "Experiencia comercial consultiva, negociación y orientación a resultados.",
        "Ventas y comercio",
    ),
    (
        "Analista de información",
        ["análisis de datos", "excel", "sql", "power bi", "comunicación"],
        "Convertir información operativa en tableros y análisis comprensibles para apoyar decisiones del negocio.",
        "Experiencia preparando reportes, validando datos y presentando conclusiones.",
        "Analitica y ciencia de datos",
    ),
    (
        "Coordinador de proyectos",
        ["gestión de proyectos", "planeación", "liderazgo", "comunicación", "riesgos"],
        "Planear iniciativas, coordinar responsables y comunicar avances, riesgos y decisiones de forma oportuna.",
        "Experiencia coordinando proyectos y equipos multidisciplinarios.",
        "Recursos humanos",
    ),
)

CANDIDATES = (
    ("Laura Campos", "Analista de experiencia", ["servicio al cliente", "comunicación", "crm", "excel", "análisis de datos"], 4),
    ("Andrés Rojas", "Profesional de talento humano", ["selección", "entrevistas", "recursos humanos", "comunicación", "excel"], 5),
    ("Mariana Vélez", "Analista de operaciones", ["operaciones", "indicadores", "excel", "mejora continua", "trabajo en equipo"], 3),
    ("Carlos Méndez", "Ejecutivo comercial", ["ventas", "negociación", "crm", "servicio al cliente", "comunicación"], 6),
    ("Diana Castillo", "Analista de datos", ["análisis de datos", "excel", "sql", "power bi", "comunicación"], 4),
    ("Felipe Duarte", "Coordinador de proyectos", ["gestión de proyectos", "planeación", "liderazgo", "comunicación", "riesgos"], 7),
    ("Sara Mejía", "Auxiliar administrativa", ["organización", "excel", "comunicación", "gestión documental"], 2),
    ("Mateo Torres", "Asesor de servicio", ["servicio al cliente", "resolución de problemas", "comunicación", "trabajo en equipo"], 3),
    ("Valentina Mora", "Analista comercial", ["ventas", "excel", "negociación", "crm", "análisis de datos"], 4),
    ("Juan Esteban Ruiz", "Profesional de operaciones", ["operaciones", "logística", "indicadores", "excel", "liderazgo"], 5),
    ("Natalia Herrera", "Especialista de selección", ["selección", "entrevistas", "bienestar", "recursos humanos", "comunicación"], 6),
    ("Santiago Peña", "Analista BI", ["power bi", "sql", "excel", "análisis de datos", "presentaciones"], 3),
)


def create_showcase(email: str, name: str, password: str | None) -> dict[str, int]:
    email = str(TypeAdapter(EmailStr).validate_python(email)).lower()
    with SessionLocal() as session:
        owner = session.query(User).filter(User.email == email).first()
        if owner is None:
            if not password or len(password.encode("utf-8")) < 8:
                raise ValueError("La cuenta nueva necesita una contraseña de al menos 8 caracteres")
            owner = User(
                name=name,
                email=email,
                password_hash=hash_password(password),
                role=UserRole.COMPANY,
            )
            owner.profile = Profile()
            session.add(owner)
            session.flush()
        elif owner.role != UserRole.COMPANY:
            raise ValueError("El correo ya pertenece a una cuenta que no es empresa")

        company = session.query(Company).filter(Company.nit == SHOWCASE_NIT).first()
        company_values = {
            "owner_user_id": owner.id,
            "name": "TalentSync Empresas",
            "description": "Equipo de servicios de talento que usa TalentSync para organizar procesos de selección claros, medibles y centrados en las personas.",
            "website": "https://talentsync-ai.pages.dev",
            "sector": "Recursos humanos",
            "size": "51-200 personas",
            "location": "Medellín, Antioquia",
            "mission": "Conectar personas y oportunidades mediante procesos de selección transparentes y decisiones sustentadas en información.",
            "values": ["Claridad", "Respeto", "Diversidad", "Aprendizaje continuo"],
            "benefits": ["Trabajo híbrido", "Formación continua", "Horario flexible", "Bienestar"],
            "is_external": False,
            "source_name": "TalentSync Showcase",
        }
        if company is None:
            company = Company(nit=SHOWCASE_NIT, **company_values)
            session.add(company)
            session.flush()
        else:
            for key, value in company_values.items():
                setattr(company, key, value)

        jobs: list[Job] = []
        now = datetime.utcnow()
        for index, (title, skills, description, requirements, sector) in enumerate(JOBS):
            external_id = f"showcase-job-{index + 1}"
            job = (
                session.query(Job)
                .filter(Job.source_name == "TalentSync Showcase", Job.external_id == external_id)
                .first()
            )
            analysis = text_processor.analyze_job(f"{title} {description} {requirements}")
            values = {
                "company_id": company.id,
                "title": title,
                "description": description,
                "requirements": requirements,
                "salary": 3_200_000 + index * 450_000,
                "location": "Medellín",
                "department": "Antioquia",
                "modality": "hybrid" if index % 2 == 0 else "remote",
                "employment_type": "full_time",
                "sector": sector,
                "status": "paused",
                "benefits": company.benefits,
                "pipeline_stages": PIPELINE,
                "languages": [],
                "application_questions": [],
                "skills": skills,
                "embedding": analysis.embedding,
                "source_kind": "internal",
                "source_name": "TalentSync Showcase",
                "external_id": external_id,
                "external_url": None,
                "created_at": now - timedelta(days=10 + index * 5),
                "expires_at": now + timedelta(days=90),
                "last_seen_at": now,
            }
            if job is None:
                job = Job(**values)
                session.add(job)
                session.flush()
            else:
                for key, value in values.items():
                    setattr(job, key, value)
            jobs.append(job)

        candidates: list[User] = []
        for index, (candidate_name, profession, skills, years) in enumerate(CANDIDATES):
            candidate_email = f"showcase.candidate.{index + 1:02d}@example.invalid"
            candidate = session.query(User).filter(User.email == candidate_email).first()
            experience = f"{years} años de experiencia en funciones relacionadas con {profession.lower()}."
            profile_text = f"{profession} {' '.join(skills)} {experience}"
            analysis = text_processor.analyze_cv(profile_text)
            if candidate is None:
                candidate = User(
                    name=candidate_name,
                    email=candidate_email,
                    password_hash=hash_password(secrets.token_urlsafe(32)),
                    role=UserRole.CANDIDATE,
                )
                candidate.profile = Profile()
                session.add(candidate)
                session.flush()
            candidate.name = candidate_name
            profile = candidate.profile
            profile.profession = profession
            profile.skills = skills
            profile.experience = experience
            profile.education = "Formación profesional o tecnológica relacionada con su área"
            profile.location = "Medellín"
            profile.department = "Antioquia"
            profile.availability = "Inmediata"
            profile.preferred_modality = "hybrid"
            profile.experiences = [
                {
                    "role": profession,
                    "company": "Organización anterior",
                    "start_year": str(now.year - years),
                    "end_year": "Presente",
                    "description": experience,
                }
            ]
            profile.educations = []
            profile.certifications = []
            profile.languages = [{"name": "inglés", "level": "B1"}]
            profile.embedding = analysis.embedding
            profile.updated_at = now
            candidates.append(candidate)

        session.flush()
        stages = [
            (ApplicationStatus.SUBMITTED, "submitted"),
            (ApplicationStatus.REVIEWING, "reviewing"),
            (ApplicationStatus.TECHNICAL_INTERVIEW, "interview"),
            (ApplicationStatus.HIRED, "hired"),
            (ApplicationStatus.REJECTED, "rejected"),
        ]
        applications = 0
        uow = SqlAlchemyUnitOfWork(session)
        for index, candidate in enumerate(candidates):
            job = jobs[index % len(jobs)]
            status, stage = stages[index % len(stages)]
            application = (
                session.query(Application)
                .filter(Application.user_id == candidate.id, Application.job_id == job.id)
                .first()
            )
            if application is None:
                application = Application(user_id=candidate.id, job_id=job.id)
                session.add(application)
                applications += 1
            application.status = status
            application.pipeline_stage = stage
            application.created_at = now - timedelta(days=index + 1)
            upsert_recommendation(
                uow,
                candidate,
                job,
                nlp=text_processor,
                commit_result=False,
            )
        session.commit()
        return {
            "company_user_id": owner.id,
            "company_id": company.id,
            "jobs": len(jobs),
            "candidates": len(candidates),
            "applications_created": applications,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Crear el espacio privado de empresa")
    parser.add_argument("--email", required=True, help="Correo de acceso de la empresa")
    parser.add_argument("--name", default="Equipo TalentSync", help="Nombre del usuario")
    arguments = parser.parse_args()
    with SessionLocal() as session:
        exists = session.query(User).filter(User.email == arguments.email.lower()).first()
    password = None
    if exists is None:
        password = getpass("Contraseña de la cuenta empresa: ")
        if password != getpass("Repite la contraseña: "):
            parser.error("Las contraseñas no coinciden")
    try:
        print(
            json.dumps(
                create_showcase(arguments.email, arguments.name, password),
                ensure_ascii=False,
            )
        )
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
