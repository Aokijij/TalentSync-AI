"""Populate a sizeable, idempotent internal marketplace for product showcases.

The records are deliberately fictional brands, so the production catalog does not
attribute invented offers to real companies. They use the same tables and flows as
companies that register through the application.
"""

import json
import secrets
from datetime import datetime, timedelta

from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import Company, Job, Profile, User
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.nlp.text_processor import text_processor
from app.infrastructure.security.passwords import hash_password

SOURCE_NAME = "TalentSync Marketplace"
PIPELINE = [
    {"id": "submitted", "title": "Recibidas"},
    {"id": "reviewing", "title": "En revisión"},
    {"id": "interview", "title": "Entrevista"},
    {"id": "hired", "title": "Contratados"},
    {"id": "rejected", "title": "No seleccionados"},
]

COMPANIES = (
    ("Andina Digital", "Tecnologia y software", "Medellín", "Antioquia"),
    ("Nexo Salud Integral", "Salud y bienestar", "Bogotá", "Bogotá D.C."),
    ("Horizonte Logístico", "Logistica y transporte", "Barranquilla", "Atlántico"),
    ("Prisma Financiero", "Finanzas y banca", "Bogotá", "Bogotá D.C."),
    ("Verde Urbano", "Construccion e ingenieria", "Medellín", "Antioquia"),
    ("Aula Abierta Colombia", "Educacion", "Cali", "Valle del Cauca"),
    ("Brújula Comercial", "Ventas y comercio", "Bucaramanga", "Santander"),
    ("Origen Alimentos", "Manufactura", "Manizales", "Caldas"),
    ("Ruta Hotelera", "Turismo y hoteleria", "Cartagena", "Bolívar"),
    ("Integra Talento", "Recursos humanos", "Medellín", "Antioquia"),
    ("Atlas Ingeniería", "Construccion e ingenieria", "Bogotá", "Bogotá D.C."),
    ("Boreal Energía", "Manufactura", "Barranquilla", "Atlántico"),
    ("Vértice Manufactura", "Manufactura", "Pereira", "Risaralda"),
    ("Pulso Creativo", "Marketing y publicidad", "Bogotá", "Bogotá D.C."),
    ("Conecta Servicios", "Ventas y comercio", "Cali", "Valle del Cauca"),
    ("Nova Agroindustria", "Manufactura", "Rionegro", "Antioquia"),
    ("Casa Urbana", "Retail y consumo masivo", "Bogotá", "Bogotá D.C."),
    ("Equilibrio Bienestar", "Salud y bienestar", "Medellín", "Antioquia"),
    ("Cumbre Consultoría", "Recursos humanos", "Bogotá", "Bogotá D.C."),
    ("Costa Azul Turismo", "Turismo y hoteleria", "Santa Marta", "Magdalena"),
)

ROLES = (
    (
        "Analista de operaciones",
        ["operaciones", "excel", "indicadores", "mejora continua", "trabajo en equipo"],
        "coordinar la operación diaria, consolidar indicadores y proponer mejoras medibles",
    ),
    (
        "Ejecutivo de cuenta",
        ["ventas", "negociación", "crm", "servicio al cliente", "comunicación"],
        "acompañar clientes, identificar oportunidades y hacer seguimiento a compromisos comerciales",
    ),
    (
        "Analista de información",
        ["análisis de datos", "excel", "sql", "power bi", "comunicación"],
        "transformar datos del negocio en reportes claros para apoyar decisiones oportunas",
    ),
    (
        "Coordinador de proyectos",
        ["gestión de proyectos", "planeación", "liderazgo", "riesgos", "comunicación"],
        "planear iniciativas, coordinar responsables y anticipar riesgos de ejecución",
    ),
    (
        "Especialista de experiencia",
        ["servicio al cliente", "comunicación", "resolución de problemas", "crm", "calidad"],
        "analizar necesidades de usuarios y diseñar soluciones sencillas para mejorar su experiencia",
    ),
    (
        "Profesional de talento humano",
        ["recursos humanos", "selección", "entrevistas", "bienestar", "comunicación"],
        "acompañar procesos de selección, desarrollo y bienestar de los equipos",
    ),
    (
        "Líder de calidad",
        ["aseguramiento de calidad", "auditoría", "indicadores", "mejora continua", "liderazgo"],
        "asegurar el cumplimiento de estándares y liderar planes de mejora sostenibles",
    ),
    (
        "Auxiliar administrativo",
        ["organización", "excel", "gestión documental", "servicio al cliente", "trabajo en equipo"],
        "apoyar la gestión documental, el seguimiento de solicitudes y la organización del área",
    ),
)


def seed_marketplace() -> dict[str, int]:
    now = datetime.utcnow()
    companies_created = jobs_created = jobs_updated = 0
    with SessionLocal() as session:
        for company_index, (name, sector, city, department) in enumerate(COMPANIES, 1):
            email = f"marketplace.company.{company_index:02d}@example.invalid"
            owner = session.query(User).filter(User.email == email).first()
            if owner is None:
                owner = User(
                    name=f"Equipo de {name}",
                    email=email,
                    password_hash=hash_password(secrets.token_urlsafe(32)),
                    role=UserRole.COMPANY,
                    profile=Profile(),
                )
                session.add(owner)
                session.flush()

            nit = f"TS-MARKET-{company_index:03d}"
            company = session.query(Company).filter(Company.nit == nit).first()
            company_values = {
                "owner_user_id": owner.id,
                "name": name,
                "description": (
                    f"Organización colombiana del sector {sector.lower()} enfocada en "
                    "servicios confiables, crecimiento sostenible y experiencias claras para sus clientes."
                ),
                "website": None,
                "sector": sector,
                "size": "51-200 personas" if company_index % 2 else "201-500 personas",
                "location": f"{city}, {department}",
                "mission": (
                    "Crear valor para clientes y colaboradores mediante equipos diversos, "
                    "decisiones responsables y mejora continua."
                ),
                "values": ["Integridad", "Servicio", "Colaboración", "Aprendizaje"],
                "benefits": [
                    "Formación continua",
                    "Horario flexible",
                    "Bienestar",
                    "Trabajo híbrido",
                ],
                "is_external": False,
                "source_name": SOURCE_NAME,
            }
            if company is None:
                company = Company(nit=nit, **company_values)
                session.add(company)
                session.flush()
                companies_created += 1
            else:
                for key, value in company_values.items():
                    setattr(company, key, value)

            for role_index, (title, skills, responsibility) in enumerate(ROLES, 1):
                external_id = f"market-{company_index:02d}-{role_index:02d}"
                job = (
                    session.query(Job)
                    .filter(Job.source_name == SOURCE_NAME, Job.external_id == external_id)
                    .first()
                )
                description = (
                    f"En {name} buscamos una persona para {responsibility}. "
                    f"Trabajará con diferentes áreas del sector {sector.lower()}, dará seguimiento "
                    "a resultados y participará en iniciativas que mejoran la experiencia de clientes y equipos."
                )
                requirements = (
                    "Formación técnica, tecnológica o profesional relacionada con el cargo. "
                    f"Experiencia aplicando {', '.join(skills[:3])}; capacidad para comunicar avances, "
                    "organizar prioridades y trabajar con personas de distintas áreas."
                )
                analysis = text_processor.analyze_job(
                    f"{title} {description} {requirements} {' '.join(skills)}"
                )
                questions = []
                if role_index in {1, 3, 4}:
                    questions = [
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
                            "prompt": "Cuéntanos qué te interesa de esta oportunidad.",
                            "type": "open",
                            "required": False,
                            "options": [],
                            "keywords": skills[:3],
                            "positive_adjustment": 2,
                            "negative_adjustment": 0,
                        },
                    ]
                values = {
                    "company_id": company.id,
                    "title": title,
                    "description": description,
                    "requirements": requirements,
                    "salary": float(2_600_000 + role_index * 420_000 + company_index * 25_000),
                    "location": city,
                    "department": department,
                    "modality": ("hybrid", "onsite", "remote")[
                        (company_index + role_index) % 3
                    ],
                    "employment_type": "full_time",
                    "sector": sector,
                    "status": "active",
                    "benefits": company_values["benefits"],
                    "pipeline_stages": PIPELINE,
                    "languages": (
                        [{"name": "inglés", "level": "B1"}]
                        if role_index in {3, 4}
                        else []
                    ),
                    "application_questions": questions,
                    "skills": list(dict.fromkeys([*skills, *analysis.skills]))[:20],
                    "embedding": analysis.embedding,
                    "source_kind": "internal",
                    "source_name": SOURCE_NAME,
                    "external_id": external_id,
                    "external_url": None,
                    "expires_at": now + timedelta(days=75),
                    "last_seen_at": now,
                }
                if job is None:
                    job = Job(
                        **values,
                        created_at=now - timedelta(days=(company_index + role_index) % 35),
                    )
                    session.add(job)
                    jobs_created += 1
                else:
                    for key, value in values.items():
                        setattr(job, key, value)
                    jobs_updated += 1
        session.commit()
    return {
        "companies": len(COMPANIES),
        "companies_created": companies_created,
        "jobs": len(COMPANIES) * len(ROLES),
        "jobs_created": jobs_created,
        "jobs_updated": jobs_updated,
    }


if __name__ == "__main__":
    print(json.dumps(seed_marketplace(), ensure_ascii=False))
