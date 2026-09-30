"""Create an idempotent, public Bancolombia workspace for product presentations."""

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
        "Analista de experiencia del cliente financiero",
        ["servicio al cliente", "comunicación", "crm", "análisis de datos", "excel"],
        "Acompañar solicitudes de clientes, analizar motivos de contacto y proponer mejoras medibles para su experiencia con servicios financieros.",
        "Experiencia atendiendo personas, redacción clara y manejo de indicadores de servicio.",
        "Finanzas y banca",
    ),
    (
        "Profesional de selección",
        ["selección", "entrevistas", "recursos humanos", "comunicación", "excel"],
        "Coordinar procesos de selección, entrevistas por competencias y comunicación con candidatos y líderes.",
        "Formación en psicología o áreas administrativas y experiencia en selección.",
        "Recursos humanos",
    ),
    (
        "Analista de operaciones financieras",
        ["operaciones", "indicadores", "excel", "riesgo operativo", "trabajo en equipo"],
        "Dar seguimiento a la operación financiera diaria, consolidar indicadores y coordinar controles con diferentes equipos.",
        "Experiencia en procesos operativos, hojas de cálculo, controles y seguimiento de planes de acción.",
        "Finanzas y banca",
    ),
    (
        "Ejecutivo de cuenta",
        ["ventas", "negociación", "crm", "servicio al cliente", "comunicación"],
        "Gestionar relaciones con clientes, detectar oportunidades y hacer seguimiento ordenado a acuerdos comerciales.",
        "Experiencia comercial consultiva, negociación y orientación a resultados.",
        "Ventas y comercio",
    ),
    (
        "Analista de información financiera",
        ["análisis de datos", "excel", "sql", "power bi", "comunicación"],
        "Convertir información financiera y operativa en tableros comprensibles para apoyar decisiones del negocio.",
        "Experiencia preparando reportes, validando datos y presentando conclusiones a diferentes públicos.",
        "Finanzas y banca",
    ),
    (
        "Coordinador de proyectos",
        ["gestión de proyectos", "planeación", "liderazgo", "comunicación", "riesgos"],
        "Planear iniciativas, coordinar responsables y comunicar avances, riesgos y decisiones de forma oportuna.",
        "Experiencia coordinando proyectos y equipos multidisciplinarios.",
        "Recursos humanos",
    ),
    (
        "Analista de riesgo crediticio",
        ["riesgo crediticio", "análisis financiero", "excel", "sql", "comunicación"],
        "Analizar solicitudes y comportamiento de portafolios para apoyar decisiones de crédito responsables.",
        "Experiencia en análisis financiero, manejo de datos y elaboración de conceptos de riesgo.",
        "Finanzas y banca",
    ),
    (
        "Especialista de ciberseguridad",
        ["ciberseguridad", "gestión de riesgos", "seguridad de la información", "linux", "comunicación"],
        "Fortalecer controles de seguridad, analizar alertas y acompañar la gestión de riesgos tecnológicos.",
        "Experiencia en seguridad de la información, análisis de incidentes y documentación de controles.",
        "Tecnologia y software",
    ),
    (
        "Desarrollador de servicios digitales",
        ["desarrollo de software", "api rest", "javascript", "sql", "git"],
        "Diseñar y mantener servicios digitales seguros que simplifiquen la experiencia de clientes y equipos internos.",
        "Experiencia desarrollando aplicaciones, integrando APIs, usando control de versiones y bases de datos.",
        "Tecnologia y software",
    ),
    (
        "Profesional de cumplimiento",
        ["cumplimiento", "sarlaft", "análisis de riesgos", "auditoría", "comunicación"],
        "Acompañar controles de cumplimiento, analizar alertas y documentar decisiones según la regulación aplicable.",
        "Experiencia en cumplimiento, gestión de riesgos, análisis de información y elaboración de informes.",
        "Finanzas y banca",
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

CANDIDATE_DETAILS = (
    ("Especialista de experiencia del cliente", "Servicios Cercanos S.A.S.", "Administración de Empresas", "Universidad de Antioquia", "Customer Experience Fundamentals", "CX Academy", "Lideró mejoras en atención que redujeron tiempos de respuesta y fortalecieron la medición de satisfacción."),
    ("Analista de selección", "Talento Humano Integral", "Psicología", "Universidad CES", "Entrevista por competencias", "LinkedIn Learning", "Gestionó procesos de selección completos, desde la definición del perfil hasta el acompañamiento de ingreso."),
    ("Analista de operaciones", "Operaciones Confiables", "Tecnología en Gestión Empresarial", "SENA", "Indicadores de gestión", "SENA", "Consolidó indicadores operativos, documentó controles y coordinó planes de mejora con equipos internos."),
    ("Ejecutivo de cuenta corporativa", "Soluciones Comerciales Andinas", "Mercadeo", "Universidad EAFIT", "Ventas consultivas", "HubSpot Academy", "Desarrolló cuentas empresariales mediante diagnóstico de necesidades, negociación y seguimiento en CRM."),
    ("Analista de inteligencia de negocio", "Datos y Decisiones S.A.S.", "Ingeniería Industrial", "Universidad Nacional de Colombia", "Microsoft Power BI Data Analyst", "Microsoft", "Construyó tableros financieros y automatizó reportes para facilitar decisiones de líderes comerciales y operativos."),
    ("Líder de proyectos", "Gestión Estratégica Colombia", "Ingeniería Administrativa", "Universidad Nacional de Colombia", "Scrum Fundamentals", "SCRUMstudy", "Coordinó iniciativas multidisciplinarias, controló riesgos y presentó avances a patrocinadores y equipos de trabajo."),
    ("Auxiliar de gestión documental", "Archivo Empresarial", "Técnica en Asistencia Administrativa", "SENA", "Gestión documental", "SENA", "Organizó expedientes, validó información y atendió solicitudes internas con precisión y oportunidad."),
    ("Asesor integral de servicio", "Contacto Positivo", "Tecnología en Gestión de Servicios", "Institución Universitaria Pascual Bravo", "Servicio al cliente", "Coursera", "Resolvió solicitudes multicanal, documentó casos y mejoró la solución en primer contacto."),
    ("Analista comercial", "Mercados Regionales", "Administración Comercial", "Universidad de Medellín", "CRM para equipos comerciales", "HubSpot Academy", "Analizó oportunidades, preparó propuestas y dio seguimiento a negociaciones usando datos comerciales."),
    ("Profesional de operaciones", "Logística Urbana", "Ingeniería de Productividad y Calidad", "Politécnico Colombiano", "Lean Operations", "Coursera", "Supervisó procesos, explicó desviaciones y coordinó acciones para cumplir indicadores de calidad y servicio."),
    ("Especialista de atracción de talento", "Personas y Cultura S.A.S.", "Psicología", "Universidad Pontificia Bolivariana", "Selección basada en datos", "LinkedIn Learning", "Diseñó estrategias de búsqueda, realizó entrevistas y acompañó decisiones de contratación con criterios claros."),
    ("Analista de datos financieros", "Analítica Aplicada", "Estadística", "Universidad de Antioquia", "SQL for Data Analysis", "DataCamp", "Preparó modelos de datos, tableros en Power BI y análisis ejecutivos para seguimiento financiero."),
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
        owner.name = "Bancolombia"

        owned_company = (
            session.query(Company)
            .filter(Company.owner_user_id == owner.id)
            .order_by(Company.id.asc())
            .first()
        )
        showcase_company = (
            session.query(Company).filter(Company.nit == SHOWCASE_NIT).first()
        )
        company = owned_company or showcase_company
        duplicate_company = (
            showcase_company
            if owned_company is not None
            and showcase_company is not None
            and showcase_company.id != owned_company.id
            else None
        )
        company_values = {
            "owner_user_id": owner.id,
            "name": "Bancolombia",
            "description": "Organización financiera colombiana que trabaja para promover el desarrollo sostenible, la inclusión financiera y experiencias digitales seguras.",
            "website": "https://www.bancolombia.com",
            "sector": "Finanzas y banca",
            "size": "Más de 1000 personas",
            "location": "Medellín, Antioquia",
            "mission": "Promover desarrollo económico sostenible y transformar positivamente la experiencia financiera de las personas.",
            "values": ["Integridad", "Cercanía", "Innovación", "Sostenibilidad"],
            "benefits": ["Trabajo híbrido", "Formación continua", "Bienestar", "Beneficios financieros"],
            "is_external": False,
            "source_name": "TalentSync",
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
                .filter(
                    Job.source_kind == "internal",
                    Job.external_id == external_id,
                )
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
                "status": "active",
                "benefits": company.benefits,
                "pipeline_stages": PIPELINE,
                "languages": [],
                "application_questions": [
                    {
                        "id": "relevant_experience",
                        "prompt": "¿Cuánta experiencia tienes en funciones relacionadas con este cargo?",
                        "type": "choice",
                        "required": True,
                        "options": ["Menos de un año", "Entre 1 y 3 años", "Más de 3 años"],
                        "option_scores": {
                            "Menos de un año": -1,
                            "Entre 1 y 3 años": 2,
                            "Más de 3 años": 4,
                        },
                    },
                    {
                        "id": "motivation",
                        "prompt": "Cuéntanos por qué te interesa trabajar en el sector financiero.",
                        "type": "open",
                        "required": False,
                        "options": [],
                        "keywords": ["servicio", "innovación", "aprendizaje"],
                        "positive_adjustment": 2,
                        "negative_adjustment": 0,
                    },
                ],
                "skills": skills,
                "embedding": analysis.embedding,
                "source_kind": "internal",
                "source_name": "TalentSync",
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

        if duplicate_company is not None:
            session.flush()
            remaining_jobs = (
                session.query(Job)
                .filter(Job.company_id == duplicate_company.id)
                .count()
            )
            if remaining_jobs == 0:
                session.delete(duplicate_company)

        candidates: list[User] = []
        for index, (candidate_name, profession, skills, years) in enumerate(CANDIDATES):
            role, previous_company, degree, institution, certification, issuer, achievement = CANDIDATE_DETAILS[index]
            candidate_email = f"showcase.candidate.{index + 1:02d}@example.invalid"
            candidate = session.query(User).filter(User.email == candidate_email).first()
            experience = (
                f"{years} años de experiencia en {profession.lower()}. {achievement} "
                f"Manejo de {', '.join(skills)}."
            )
            profile_text = f"{profession} {' '.join(skills)} {experience} {degree}"
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
            profile.education = f"{degree} — {institution}"
            profile.location = "Medellín"
            profile.department = "Antioquia"
            profile.availability = "Inmediata"
            profile.preferred_modality = "hybrid"
            profile.preferred_sector = JOBS[index % len(JOBS)][4]
            profile.desired_salary = 3_200_000 + years * 180_000
            profile.phone = f"+57 300 55{index + 10:04d}"
            profile.experiences = [
                {
                    "role": role,
                    "company": previous_company,
                    "start_year": str(now.year - years),
                    "end_year": "Presente",
                    "description": achievement,
                }
            ]
            profile.educations = [
                {
                    "degree": degree,
                    "institution": institution,
                    "start_year": str(now.year - years - 4),
                    "end_year": str(now.year - years),
                }
            ]
            profile.certifications = [
                {"name": certification, "issuer": issuer, "year": str(now.year - 1)}
            ]
            profile.languages = [
                {"name": "inglés", "level": "B2" if index % 3 == 0 else "B1"},
                {"name": "español", "level": "NATIVE"},
            ]
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
            application.screening_answers = [
                {
                    "question_id": "relevant_experience",
                    "question": "¿Cuánta experiencia tienes en funciones relacionadas con este cargo?",
                    "type": "choice",
                    "answer": "Entre 1 y 3 años" if index % 2 else "Más de 3 años",
                    "reviewer_adjustment": 0,
                },
                {
                    "question_id": "motivation",
                    "question": "Cuéntanos por qué te interesa trabajar en el sector financiero.",
                    "type": "open",
                    "answer": "Me interesa aportar desde el servicio, aprender y participar en iniciativas de innovación.",
                    "reviewer_adjustment": 0,
                },
            ]
            application.screening_adjustment = 4 if index % 2 == 0 else 2
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
