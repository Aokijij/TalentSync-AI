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

COMPANY_FOCUS = {
    "Andina Digital": "productos SaaS empresariales",
    "Nexo Salud Integral": "atención ambulatoria",
    "Horizonte Logístico": "distribución de última milla",
    "Prisma Financiero": "banca digital inclusiva",
    "Verde Urbano": "proyectos urbanos sostenibles",
    "Aula Abierta Colombia": "aprendizaje híbrido",
    "Brújula Comercial": "soluciones B2B",
    "Origen Alimentos": "producción de alimentos",
    "Ruta Hotelera": "operación hotelera premium",
    "Integra Talento": "experiencia del colaborador",
    "Atlas Ingeniería": "infraestructura institucional",
    "Boreal Energía": "operaciones energéticas",
    "Vértice Manufactura": "manufactura metalmecánica",
    "Pulso Creativo": "estrategia de marcas",
    "Conecta Servicios": "experiencia omnicanal",
    "Nova Agroindustria": "cadenas agroindustriales",
    "Casa Urbana": "comercio minorista",
    "Equilibrio Bienestar": "programas de bienestar",
    "Cumbre Consultoría": "transformación organizacional",
    "Costa Azul Turismo": "experiencias de turismo sostenible",
}

COMMON_ROLES = (
    (
        "Analista de operaciones",
        ["operaciones", "excel", "indicadores", "mejora continua", "trabajo en equipo"],
        "coordinar la operación diaria, consolidar indicadores y proponer mejoras medibles",
    ),
    (
        "Analista de datos de negocio",
        ["análisis de datos", "excel", "sql", "power bi", "comunicación"],
        "convertir datos operativos en tableros y recomendaciones comprensibles para los equipos",
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
)

SECTOR_ROLES = {
    "Tecnologia y software": (
        ("Desarrollador frontend", ["javascript", "react", "html", "css", "git"], "crear interfaces accesibles, rápidas y fáciles de mantener"),
        ("Desarrollador backend", ["python", "api rest", "sql", "docker", "git"], "construir servicios seguros e integrar datos entre productos digitales"),
        ("Analista de calidad de software", ["testing", "qa", "automatización", "api rest", "comunicación"], "diseñar pruebas y prevenir defectos antes de cada lanzamiento"),
        ("Especialista de soporte tecnológico", ["soporte técnico", "linux", "redes", "servicio al cliente", "documentación"], "resolver incidentes y documentar soluciones para usuarios internos"),
    ),
    "Salud y bienestar": (
        ("Profesional de enfermería", ["enfermería", "atención al paciente", "seguridad del paciente", "historias clínicas", "comunicación"], "brindar atención segura y acompañar el plan de cuidado de cada paciente"),
        ("Auxiliar de admisiones en salud", ["admisiones", "servicio al paciente", "facturación", "excel", "comunicación"], "orientar pacientes y gestionar autorizaciones y registros de ingreso"),
        ("Auditor de calidad clínica", ["auditoría clínica", "calidad", "normatividad en salud", "indicadores", "análisis de datos"], "evaluar procesos asistenciales y liderar acciones de mejora"),
        ("Analista de facturación médica", ["facturación en salud", "rips", "excel", "auditoría", "organización"], "validar cuentas médicas y reducir devoluciones y glosas"),
    ),
    "Logistica y transporte": (
        ("Coordinador de logística", ["logística", "distribución", "indicadores", "excel", "liderazgo"], "coordinar despachos y asegurar entregas completas y oportunas"),
        ("Analista de inventarios", ["inventarios", "excel", "erp", "auditoría", "organización"], "controlar existencias y explicar diferencias de inventario"),
        ("Planeador de rutas", ["planeación de rutas", "transporte", "geolocalización", "excel", "comunicación"], "diseñar rutas eficientes y monitorear novedades de transporte"),
        ("Supervisor de bodega", ["bodega", "inventarios", "seguridad industrial", "liderazgo", "mejora continua"], "organizar recibo, almacenamiento y despacho con estándares de seguridad"),
    ),
    "Finanzas y banca": (
        ("Analista de riesgo crediticio", ["riesgo crediticio", "análisis financiero", "excel", "sql", "comunicación"], "analizar solicitudes y sustentar decisiones de crédito responsables"),
        ("Analista financiero", ["análisis financiero", "presupuestos", "excel", "power bi", "presentaciones"], "preparar proyecciones y explicar variaciones financieras del negocio"),
        ("Profesional de cumplimiento", ["cumplimiento", "sarlaft", "gestión de riesgos", "auditoría", "comunicación"], "analizar alertas y documentar controles regulatorios"),
        ("Asesor de servicios financieros", ["servicio al cliente", "productos financieros", "ventas", "crm", "comunicación"], "orientar clientes y ofrecer soluciones financieras según sus necesidades"),
    ),
    "Construccion e ingenieria": (
        ("Ingeniero residente de obra", ["supervisión de obra", "presupuestos", "autocad", "liderazgo", "seguridad industrial"], "coordinar la ejecución de obra y controlar alcance, calidad y tiempos"),
        ("Modelador BIM", ["bim", "revit", "autocad", "planos", "trabajo en equipo"], "desarrollar modelos coordinados y detectar interferencias de diseño"),
        ("Coordinador de seguridad y salud", ["sst", "seguridad industrial", "inspecciones", "normatividad", "capacitación"], "prevenir riesgos y acompañar prácticas seguras en campo"),
        ("Analista de costos y presupuestos", ["presupuestos", "apu", "excel", "costos", "planeación"], "elaborar presupuestos y controlar desviaciones de costos de proyectos"),
    ),
    "Educacion": (
        ("Docente de educación media", ["pedagogía", "planeación de clases", "evaluación", "comunicación", "trabajo en equipo"], "diseñar experiencias de aprendizaje y acompañar el progreso de estudiantes"),
        ("Coordinador académico", ["gestión académica", "liderazgo", "currículo", "indicadores", "comunicación"], "coordinar planes académicos y fortalecer las prácticas docentes"),
        ("Orientador escolar", ["orientación escolar", "psicología educativa", "convivencia", "comunicación", "trabajo en equipo"], "acompañar el bienestar y la convivencia de la comunidad educativa"),
        ("Diseñador de aprendizaje virtual", ["diseño instruccional", "moodle", "creación de contenido", "evaluación", "tecnología educativa"], "crear cursos virtuales claros, participativos y medibles"),
    ),
    "Ventas y comercio": (
        ("Ejecutivo de cuenta", ["ventas consultivas", "negociación", "crm", "servicio al cliente", "comunicación"], "desarrollar relaciones comerciales y cumplir metas de crecimiento"),
        ("Asesor comercial", ["ventas", "servicio al cliente", "negociación", "comunicación", "orientación a resultados"], "entender necesidades y recomendar soluciones adecuadas a cada cliente"),
        ("Analista CRM", ["crm", "análisis de datos", "excel", "segmentación", "marketing"], "analizar el comportamiento de clientes y mejorar campañas comerciales"),
        ("Especialista de éxito del cliente", ["customer success", "servicio al cliente", "retención", "crm", "comunicación"], "acompañar la adopción del servicio y prevenir cancelaciones"),
    ),
    "Manufactura": (
        ("Supervisor de producción", ["producción", "liderazgo", "indicadores", "seguridad industrial", "mejora continua"], "coordinar turnos y cumplir el plan de producción con seguridad y calidad"),
        ("Técnico de mantenimiento", ["mantenimiento industrial", "electricidad", "mecánica", "diagnóstico", "seguridad industrial"], "realizar mantenimiento preventivo y resolver fallas de equipos"),
        ("Analista de calidad", ["control de calidad", "auditoría", "metrología", "indicadores", "mejora continua"], "verificar especificaciones y gestionar acciones correctivas"),
        ("Ingeniero de procesos", ["ingeniería de procesos", "lean manufacturing", "indicadores", "excel", "optimización"], "reducir desperdicios y mejorar capacidad y estabilidad de los procesos"),
    ),
    "Turismo y hoteleria": (
        ("Recepcionista de hotel", ["recepción", "servicio al cliente", "reservas", "inglés", "comunicación"], "recibir huéspedes y resolver solicitudes durante su estadía"),
        ("Agente de reservas", ["reservas", "servicio al cliente", "ventas", "inglés", "sistemas hoteleros"], "gestionar reservas y orientar viajeros sobre servicios disponibles"),
        ("Coordinador de alimentos y bebidas", ["alimentos y bebidas", "liderazgo", "costos", "servicio al cliente", "manipulación de alimentos"], "coordinar el servicio y controlar calidad, inventarios y costos"),
        ("Operador de experiencias turísticas", ["turismo", "logística", "servicio al cliente", "inglés", "comunicación"], "organizar experiencias seguras y memorables para visitantes"),
    ),
    "Recursos humanos": (
        ("Profesional de selección", ["selección", "entrevistas", "reclutamiento", "comunicación", "excel"], "gestionar procesos de selección y acompañar candidatos y líderes"),
        ("Generalista de talento humano", ["recursos humanos", "bienestar", "relaciones laborales", "comunicación", "organización"], "acompañar el ciclo de vida de colaboradores y resolver solicitudes laborales"),
        ("Analista de nómina", ["nómina", "seguridad social", "excel", "legislación laboral", "organización"], "liquidar novedades y asegurar pagos correctos y oportunos"),
        ("Analista de cultura y desarrollo", ["cultura organizacional", "capacitación", "indicadores", "comunicación", "gestión del cambio"], "diseñar iniciativas de aprendizaje, cultura y compromiso"),
    ),
    "Marketing y publicidad": (
        ("Especialista de contenidos", ["creación de contenido", "redacción", "seo", "redes sociales", "analítica digital"], "crear contenidos útiles y medir su aporte a los objetivos de marca"),
        ("Analista de medios digitales", ["publicidad digital", "google ads", "meta ads", "analítica digital", "excel"], "optimizar campañas pagadas según resultados y audiencias"),
        ("Diseñador gráfico", ["diseño gráfico", "illustrator", "photoshop", "identidad visual", "creatividad"], "desarrollar piezas visuales coherentes para campañas y productos"),
        ("Analista de investigación de mercados", ["investigación de mercados", "encuestas", "análisis de datos", "excel", "presentaciones"], "convertir hallazgos de clientes y mercado en recomendaciones accionables"),
    ),
    "Retail y consumo masivo": (
        ("Administrador de tienda", ["retail", "liderazgo", "ventas", "inventarios", "servicio al cliente"], "liderar la operación de tienda y cumplir metas de venta y experiencia"),
        ("Planeador de inventarios", ["planeación de demanda", "inventarios", "excel", "erp", "análisis de datos"], "proyectar necesidades de producto y evitar agotados y excesos"),
        ("Analista de comercio electrónico", ["ecommerce", "analítica digital", "catálogo de productos", "excel", "marketing"], "mejorar conversión, contenido y operación del canal digital"),
        ("Especialista de visual merchandising", ["visual merchandising", "diseño", "retail", "planeación", "comunicación"], "diseñar exhibiciones que faciliten la compra y representen la marca"),
    ),
}


def roles_for(sector: str):
    return (*SECTOR_ROLES.get(sector, ()), *COMMON_ROLES)


def specialized_title(title: str, focus: str) -> str:
    connector = "para" if title.startswith(("Analista", "Coordinador")) else "en"
    return f"{title} {connector} {focus}"


def application_questions(
    role_index: int, title: str, skills: list[str], responsibility: str, focus: str
) -> list[dict]:
    experience_options = [
        "Aún no tengo experiencia directa",
        "Menos de 2 años",
        "Entre 2 y 4 años",
        "Más de 4 años",
    ]
    return [
        {
            "id": f"experience_{role_index}",
            "prompt": f"¿Qué experiencia tienes como {title.lower()}?",
            "type": "choice",
            "required": True,
            "options": experience_options,
            "option_scores": {
                experience_options[0]: -3,
                experience_options[1]: 0,
                experience_options[2]: 3,
                experience_options[3]: 5,
            },
        },
        {
            "id": f"scenario_{role_index}",
            "prompt": (
                f"Describe una situación en la que lograste {responsibility} "
                f"o un resultado comparable en {focus}."
            ),
            "type": "open",
            "required": role_index % 2 == 1,
            "options": [],
            "keywords": skills[:4],
            "positive_adjustment": 2,
            "negative_adjustment": 0,
        },
    ]


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

            roles = roles_for(sector)
            for role_index, (title, skills, responsibility) in enumerate(roles, 1):
                focus = COMPANY_FOCUS[name]
                title = specialized_title(title, focus)
                external_id = f"market-{company_index:02d}-{role_index:02d}"
                job = (
                    session.query(Job)
                    .filter(Job.source_name == SOURCE_NAME, Job.external_id == external_id)
                    .first()
                )
                description = (
                    f"En {name} buscamos una persona para {responsibility}. "
                    f"Su trabajo estará conectado con {focus} y tendrá impacto directo en "
                    f"{('la calidad del servicio' if role_index % 3 == 0 else 'la eficiencia del equipo' if role_index % 3 == 1 else 'la experiencia de clientes y usuarios')}. "
                    f"Durante los primeros meses deberá {('construir una línea base de indicadores' if role_index % 2 else 'entender el proceso actual y priorizar mejoras')}, "
                    "coordinar a las personas involucradas y comunicar resultados de forma clara."
                )
                education = (
                    "Formación técnica o tecnológica relacionada con el cargo"
                    if role_index in {2, 4, 8}
                    else "Formación profesional relacionada con el cargo"
                )
                experience = (role_index % 4) + 1
                requirements = (
                    f"{education} y al menos {experience} año{'s' if experience != 1 else ''} de experiencia. "
                    f"Conocimientos necesarios: {', '.join(skills)}. "
                    f"Para este reto se necesita demostrar capacidad para {responsibility}, "
                    f"trabajar con información de {focus}, priorizar tareas y documentar decisiones. "
                    "En la postulación se solicitarán ejemplos concretos de resultados obtenidos."
                )
                analysis = text_processor.analyze_job(
                    f"{title} {description} {requirements} {' '.join(skills)}"
                )
                questions = application_questions(
                    role_index, title, skills, responsibility, focus
                )
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
                    "employment_type": "contract" if role_index == 8 else "full_time",
                    "sector": sector,
                    "status": "active",
                    "benefits": [
                        company_values["benefits"][(role_index - 1) % 4],
                        company_values["benefits"][role_index % 4],
                    ],
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
        "jobs": sum(len(roles_for(sector)) for _, sector, _, _ in COMPANIES),
        "jobs_created": jobs_created,
        "jobs_updated": jobs_updated,
    }


if __name__ == "__main__":
    print(json.dumps(seed_marketplace(), ensure_ascii=False))
