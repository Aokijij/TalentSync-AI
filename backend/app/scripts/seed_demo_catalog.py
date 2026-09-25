"""Create an idempotent, clearly labelled demonstration job catalog."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from app.application.use_cases.matching import upsert_recommendation
from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import Company, Job, User
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.nlp.text_processor import text_processor

DEMO_SOURCE = "TalentSync Demo"
PIPELINE = [
    {"id": "submitted", "title": "Recibidas"},
    {"id": "reviewing", "title": "En revisión"},
    {"id": "interview", "title": "Entrevista"},
    {"id": "hired", "title": "Contratados"},
    {"id": "rejected", "title": "No seleccionados"},
]

COMPANIES = (
    ("Horizonte Operativo", "Sector publico y social", "Medellín", "Antioquia", "51-200 personas"),
    ("Nexo Comercial Andino", "Ventas y comercio", "Bogotá", "Bogotá D.C.", "201-500 personas"),
    ("Ruta Clara", "Logistica y transporte", "Cali", "Valle del Cauca", "201-500 personas"),
    ("Balance Integral", "Finanzas y banca", "Medellín", "Antioquia", "51-200 personas"),
    ("Cuidado Vital", "Salud y bienestar", "Barranquilla", "Atlántico", "201-500 personas"),
    ("Aula Abierta", "Educacion", "Bogotá", "Bogotá D.C.", "51-200 personas"),
    ("Impulso Digital", "Tecnologia y software", "Medellín", "Antioquia", "51-200 personas"),
    ("Terranova Servicios", "Construccion e ingenieria", "Bucaramanga", "Santander", "201-500 personas"),
    ("Punto Humano", "Recursos humanos", "Pereira", "Risaralda", "11-50 personas"),
    ("Conecta Experiencias", "Telecomunicaciones", "Bogotá", "Bogotá D.C.", "201-500 personas"),
    ("Vía Segura", "Sector publico y social", "Cali", "Valle del Cauca", "501-1000 personas"),
    ("Energía Cercana", "Energia y servicios publicos", "Manizales", "Caldas", "201-500 personas"),
    ("Alimentos Raíz", "Alimentos y bebidas", "Medellín", "Antioquia", "501-1000 personas"),
    ("Hábitat Urbano", "Construccion e ingenieria", "Bogotá", "Bogotá D.C.", "51-200 personas"),
    ("Soluciones Prisma", "Analitica y ciencia de datos", "Cartagena", "Bolívar", "51-200 personas"),
    ("Círculo Financiero", "Finanzas y banca", "Bogotá", "Bogotá D.C.", "201-500 personas"),
    ("Movilidad Uno", "Logistica y transporte", "Barranquilla", "Atlántico", "201-500 personas"),
    ("Centro Bienestar", "Salud y bienestar", "Medellín", "Antioquia", "51-200 personas"),
    ("Red Creativa", "Marketing y publicidad", "Cali", "Valle del Cauca", "11-50 personas"),
    ("Campo Futuro", "Agricultura y medio ambiente", "Pereira", "Risaralda", "201-500 personas"),
)

ROLES = (
    ("Auxiliar administrativo/a", ["administración", "gestión documental", "excel", "organización", "comunicación"], "apoyar la operación administrativa, organizar documentos y atender solicitudes internas", "Manejo de herramientas de oficina, orden, comunicación clara y seis meses de experiencia relacionada", 1_650_000),
    ("Analista de servicio al cliente", ["servicio al cliente", "comunicación", "resolución de problemas", "crm", "trabajo en equipo"], "acompañar a los usuarios, resolver casos y convertir sus comentarios en mejoras del servicio", "Experiencia atendiendo personas, buena redacción, escucha activa y orientación a soluciones", 2_150_000),
    ("Asesor/a comercial", ["ventas", "negociación", "servicio al cliente", "crm", "comunicación"], "identificar necesidades, presentar soluciones y hacer seguimiento responsable a oportunidades comerciales", "Experiencia comercial, capacidad de negociación, disciplina de seguimiento y orientación a resultados", 2_300_000),
    ("Coordinador/a logístico", ["logística", "inventarios", "despachos", "excel", "liderazgo"], "coordinar inventarios, despachos, novedades de transporte e indicadores de cumplimiento", "Formación técnica o profesional relacionada, experiencia en operación y manejo de indicadores", 3_400_000),
    ("Auxiliar contable", ["contabilidad", "facturación", "conciliaciones", "excel", "atención al detalle"], "registrar movimientos, apoyar conciliaciones y mantener actualizados los soportes contables", "Formación contable, conocimientos de facturación y manejo cuidadoso de información", 2_050_000),
    ("Profesional de talento humano", ["recursos humanos", "selección", "bienestar", "comunicación", "excel"], "acompañar selección, vinculación, bienestar y seguimiento de indicadores de personas", "Formación en psicología o administración y experiencia en procesos de talento humano", 3_300_000),
    ("Enfermero/a asistencial", ["enfermería", "atención al paciente", "seguridad del paciente", "trabajo en equipo", "comunicación"], "brindar cuidado seguro, registrar la evolución y orientar a pacientes y familias", "Título y documentación profesional vigente, vocación de servicio y disponibilidad para turnos", 3_600_000),
    ("Docente de matemáticas", ["docencia", "matemáticas", "pedagogía", "planeación", "comunicación"], "planear experiencias de aprendizaje, acompañar estudiantes y evaluar avances de forma clara", "Licenciatura o carrera afín, fundamentos pedagógicos y capacidad para explicar conceptos", 3_000_000),
    ("Analista de datos", ["análisis de datos", "excel", "sql", "power bi", "comunicación"], "transformar datos operativos en reportes comprensibles para apoyar decisiones del equipo", "Experiencia con hojas de cálculo, consultas de datos, visualización y presentación de hallazgos", 4_200_000),
    ("Desarrollador/a full stack", ["desarrollo de software", "javascript", "react", "python", "sql"], "construir funcionalidades web, integrar servicios y mejorar la calidad de las aplicaciones", "Experiencia desarrollando aplicaciones, control de versiones, pruebas y trabajo colaborativo", 5_500_000),
    ("Diseñador/a de experiencia", ["diseño ux", "investigación de usuarios", "figma", "prototipado", "comunicación"], "comprender necesidades de usuarios y convertirlas en flujos y prototipos accesibles", "Portafolio de proyectos, dominio de prototipado y capacidad para justificar decisiones de diseño", 4_100_000),
    ("Técnico/a de mantenimiento", ["mantenimiento preventivo", "diagnóstico", "seguridad industrial", "trabajo en equipo", "documentación"], "realizar inspecciones, atender novedades y documentar acciones preventivas y correctivas", "Formación técnica, conocimiento de normas de seguridad y disponibilidad para trabajo operativo", 2_600_000),
    ("Supervisor/a de operaciones", ["operaciones", "liderazgo", "indicadores", "mejora continua", "comunicación"], "organizar turnos, acompañar al equipo y asegurar el cumplimiento de indicadores de servicio", "Experiencia coordinando equipos, manejo de indicadores y capacidad para resolver novedades", 3_800_000),
    ("Gestor/a de marketing digital", ["marketing digital", "redes sociales", "analítica", "contenido", "comunicación"], "planear contenidos, medir campañas y coordinar acciones digitales con diferentes equipos", "Experiencia en canales digitales, redacción, lectura de métricas y organización de campañas", 3_500_000),
)


def build_demo_catalog(now: datetime | None = None) -> list[dict]:
    """Return 20 companies and between 8 and 14 jobs for each one."""
    now = now or datetime.utcnow()
    catalog: list[dict] = []
    for company_index, (name, sector, city, department, size) in enumerate(COMPANIES):
        company_number = company_index + 1
        job_count = 8 + company_index % 7
        jobs = []
        for job_index in range(job_count):
            role = ROLES[(company_index * 3 + job_index) % len(ROLES)]
            title, skills, responsibility, requirements, base_salary = role
            questions = [
                {
                    "id": "availability",
                    "prompt": "¿Tu disponibilidad actual coincide con la modalidad y ubicación indicadas?",
                    "type": "choice",
                    "required": True,
                    "options": ["Sí, puedo cumplirlas", "Necesito conversar un ajuste"],
                    "option_scores": {"Sí, puedo cumplirlas": 2, "Necesito conversar un ajuste": 0},
                }
            ]
            if job_index % 3 == 0:
                questions.append(
                    {
                        "id": "motivation",
                        "prompt": "Cuéntanos brevemente qué experiencia aportarías a este cargo.",
                        "type": "open",
                        "required": False,
                        "keywords": [],
                        "positive_adjustment": 0,
                        "negative_adjustment": 0,
                    }
                )
            jobs.append(
                {
                    "external_id": f"ts-demo-{company_number:02d}-{job_index + 1:02d}",
                    "title": title,
                    "description": (
                        f"En {name} buscamos una persona para {responsibility}. "
                        "Trabajará con objetivos claros, acompañamiento del equipo y "
                        "espacios de aprendizaje. Esta es una vacante demostrativa creada "
                        "para recorrer de principio a fin las funciones de TalentSync."
                    ),
                    "requirements": requirements + ". Se valorará la disposición para aprender y colaborar.",
                    "salary": base_salary + (company_index % 5) * 250_000,
                    "location": city,
                    "department": department,
                    "modality": ("onsite", "hybrid", "remote")[(company_index + job_index) % 3],
                    "employment_type": "full_time" if job_index % 5 else "contract",
                    "sector": sector,
                    "benefits": ["Horario flexible", "Formación continua", "Día de bienestar"],
                    "pipeline_stages": PIPELINE,
                    "languages": [{"name": "inglés", "level": "B1"}] if job_index % 4 == 0 else [],
                    "application_questions": questions,
                    "skills": skills,
                    "created_at": now - timedelta(hours=(company_index * 19 + job_index * 7) % 720),
                    "expires_at": now + timedelta(days=90),
                }
            )
        catalog.append(
            {
                "nit": f"DEMO-TS-{company_number:03d}",
                "name": name,
                "description": (
                    f"{name} es una organización ficticia del catálogo demostrativo de "
                    "TalentSync. Permite explorar vacantes, compatibilidad y postulaciones "
                    "sin representar una oferta laboral real."
                ),
                "sector": sector,
                "size": size,
                "location": f"{city}, {department}",
                "mission": "Mostrar de forma segura y realista cómo funciona un proceso de selección completo.",
                "values": ["Claridad", "Aprendizaje", "Respeto", "Colaboración"],
                "benefits": ["Formación", "Flexibilidad", "Bienestar"],
                "jobs": jobs,
            }
        )
    return catalog


def seed_demo_catalog() -> dict[str, int]:
    session = SessionLocal()
    created_companies = updated_companies = created_jobs = updated_jobs = 0
    try:
        admin = session.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin is None:
            raise RuntimeError("Crea primero un usuario administrador")

        for company_data in build_demo_catalog():
            company = session.query(Company).filter(Company.nit == company_data["nit"]).first()
            company_values = {
                key: company_data[key]
                for key in ("name", "description", "sector", "size", "location", "mission", "values", "benefits")
            }
            company_values.update(
                owner_user_id=admin.id,
                is_external=False,
                source_name=DEMO_SOURCE,
                website=None,
            )
            if company is None:
                company = Company(nit=company_data["nit"], **company_values)
                session.add(company)
                session.flush()
                created_companies += 1
            else:
                for key, value in company_values.items():
                    setattr(company, key, value)
                updated_companies += 1

            for job_data in company_data["jobs"]:
                job = (
                    session.query(Job)
                    .filter(
                        Job.source_name == DEMO_SOURCE,
                        Job.external_id == job_data["external_id"],
                    )
                    .first()
                )
                analysis = text_processor.analyze_job(
                    f"{job_data['title']} {job_data['description']} {job_data['requirements']}"
                )
                values = {
                    **job_data,
                    "company_id": company.id,
                    "status": "active",
                    "skills": list(dict.fromkeys([*job_data["skills"], *analysis.skills]))[:40],
                    "embedding": analysis.embedding,
                    "source_kind": "demo",
                    "source_name": DEMO_SOURCE,
                    "external_url": None,
                    "last_seen_at": datetime.utcnow(),
                }
                if job is None:
                    session.add(Job(**values))
                    created_jobs += 1
                else:
                    for key, value in values.items():
                        setattr(job, key, value)
                    updated_jobs += 1
        session.commit()

        uow = SqlAlchemyUnitOfWork(session)
        demo_jobs = session.query(Job).filter(Job.source_kind == "demo").all()
        refreshed = 0
        for candidate in session.query(User).filter(User.role == UserRole.CANDIDATE).all():
            if candidate.profile is None:
                continue
            for job in demo_jobs:
                upsert_recommendation(uow, candidate, job, nlp=text_processor)
                refreshed += 1
        return {
            "companies_created": created_companies,
            "companies_updated": updated_companies,
            "jobs_created": created_jobs,
            "jobs_updated": updated_jobs,
            "recommendations_refreshed": refreshed,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print(json.dumps(seed_demo_catalog(), ensure_ascii=False))
