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
                external_id = f"market-{company_index:02d}-{role_index:02d}"
                job = (
                    session.query(Job)
                    .filter(Job.source_name == SOURCE_NAME, Job.external_id == external_id)
                    .first()
                )
                description = (
                    f"En {name} buscamos una persona para {responsibility}. "
                    f"El rol trabajará con equipos del sector {sector.lower()}, organizará prioridades, "
                    "documentará avances y hará seguimiento a indicadores acordados. "
                    "Entre sus responsabilidades estará analizar situaciones del día a día, proponer "
                    "acciones de mejora, coordinar a las personas involucradas y comunicar resultados "
                    "de forma clara a líderes, clientes o usuarios internos."
                )
                requirements = (
                    "Formación técnica, tecnológica o profesional relacionada con el cargo. "
                    f"Experiencia demostrable en {', '.join(skills)}. "
                    "Se valoran la capacidad de analizar información, resolver problemas, priorizar tareas, "
                    "documentar decisiones y trabajar de manera colaborativa. La persona debe explicar "
                    "ejemplos concretos de resultados obtenidos en experiencias académicas o laborales."
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
        "jobs": sum(len(roles_for(sector)) for _, sector, _, _ in COMPANIES),
        "jobs_created": jobs_created,
        "jobs_updated": jobs_updated,
    }


if __name__ == "__main__":
    print(json.dumps(seed_marketplace(), ensure_ascii=False))
