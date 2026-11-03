"""Replace isolated local recruiting fixtures; never connect to a remote database.

Known company names are references for local product testing. No imported job,
salary, credential or hiring process represents an official company statement.
"""
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from secrets import token_urlsafe

from sqlalchemy import delete, inspect, or_, select

from app.domain.entities.enums import ApplicationStatus, UserRole
from app.domain.services.pipeline import default_stages
from app.infrastructure.database.models import (
    Application,
    Company,
    EventLog,
    Job,
    Notification,
    Profile,
    User,
)
from app.infrastructure.database.session import Base
from app.infrastructure.security.passwords import hash_password

COMPANIES = [
    ("Bancolombia", "Finanzas y banca", "Medellín"), ("Davivienda", "Finanzas y banca", "Bogotá"),
    ("Banco de Bogotá", "Finanzas y banca", "Bogotá"), ("Grupo Éxito", "Retail y consumo masivo", "Medellín"),
    ("Grupo Nutresa", "Alimentos y bebidas", "Medellín"), ("Alpina", "Alimentos y bebidas", "Bogotá"),
    ("Alquería", "Alimentos y bebidas", "Bogotá"), ("Colombina", "Alimentos y bebidas", "Cali"),
    ("Postobón", "Alimentos y bebidas", "Medellín"), ("Ramo", "Alimentos y bebidas", "Bogotá"),
    ("Ecopetrol", "Energia y servicios publicos", "Bogotá"), ("EPM", "Energia y servicios publicos", "Medellín"),
    ("ISA", "Energia y servicios publicos", "Medellín"), ("Celsia", "Energia y servicios publicos", "Cali"),
    ("Cementos Argos", "Construccion e ingenieria", "Medellín"), ("Corona", "Manufactura", "Bogotá"),
    ("Seguros SURA", "Seguros", "Medellín"), ("Terpel", "Energia y servicios publicos", "Bogotá"),
    ("Servientrega", "Logistica y transporte", "Bogotá"), ("Coordinadora", "Logistica y transporte", "Medellín"),
    ("Avianca", "Logistica y transporte", "Bogotá"), ("Olímpica", "Retail y consumo masivo", "Barranquilla"),
    ("Alkosto", "Retail y consumo masivo", "Bogotá"), ("Arturo Calle", "Retail y consumo masivo", "Bogotá"),
    ("Leonisa", "Manufactura", "Medellín"), ("Crystal", "Manufactura", "Medellín"),
    ("Audifarma", "Farmaceutica y biotecnologia", "Pereira"), ("Colsubsidio", "Servicios profesionales", "Bogotá"),
    ("Compensar", "Salud y bienestar", "Bogotá"), ("Amarilo", "Inmobiliario", "Bogotá"),
]
CITIES = [("Medellín", "Antioquia"), ("Bogotá", "Bogotá D.C."), ("Cali", "Valle del Cauca"),
          ("Barranquilla", "Atlántico"), ("Bucaramanga", "Santander"), ("Pereira", "Risaralda"),
          ("Manizales", "Caldas"), ("Cartagena", "Bolívar"), ("Ibagué", "Tolima"),
          ("Cúcuta", "Norte de Santander"), ("Santa Marta", "Magdalena"), ("Villavicencio", "Meta")]
# title, family, sector, skills, degree, concrete deliverable, monthly base
ROLES = [
    ("Desarrollador frontend React", "software", "Tecnologia y software", ["javascript", "typescript", "react", "html", "css", "git", "pruebas de software"], "Ingeniería de sistemas", "interfaces accesibles para consultar pedidos y gestionar solicitudes", 3200000),
    ("Analista de datos", "data", "Analitica y ciencia de datos", ["sql", "python", "power bi", "excel", "pandas", "estadistica"], "Estadística", "tableros de indicadores comerciales con fuentes conciliadas y trazabilidad", 4900000),
    ("Analista contable", "finance", "Finanzas y banca", ["contabilidad", "excel", "conciliaciones bancarias", "siigo", "facturacion electronica"], "Contaduría pública", "conciliaciones bancarias y soportes para el cierre contable mensual", 2800000),
    ("Desarrollador backend Python", "software", "Tecnologia y software", ["python", "sql", "fastapi", "git", "api rest", "docker"], "Ingeniería de sistemas", "servicios de pedidos con pruebas, documentación y control de acceso", 5300000),
    ("Auxiliar de enfermería", "health", "Salud y bienestar", ["atencion al paciente", "enfermeria", "bioseguridad", "registros clinicos"], "Técnico en enfermería", "registros de atención y acompañamiento a pacientes según protocolos", 2100000),
    ("Ingeniero civil de obra", "civil", "Construccion e ingenieria", ["autocad", "presupuestos", "gestion de proyectos", "control de obra"], "Ingeniería civil", "informes de avance de obra y control de presupuesto con contratistas", 4500000),
    ("Coordinador de logística", "logistics", "Logistica y transporte", ["logistica", "excel", "gestion de inventarios", "sap"], "Administración logística", "rutas de distribución y conciliación de inventarios con el centro de operación", 3700000),
    ("Asesor comercial", "sales", "Ventas y comercio", ["ventas", "crm", "negociacion", "servicio al cliente"], "Técnico en ventas", "seguimiento de oportunidades y propuestas comerciales para clientes regionales", 2000000),
    ("Analista de talento humano", "people", "Recursos humanos", ["seleccion de personal", "nomina", "excel", "entrevistas"], "Psicología", "procesos de selección y reportes de incorporación de colaboradores", 3300000),
    ("Especialista en marketing digital", "marketing", "Marketing y publicidad", ["marketing digital", "seo", "google analytics", "redaccion"], "Mercadeo", "campañas segmentadas y reportes de conversión por canal", 3800000),
    ("Técnico de mantenimiento industrial", "industrial", "Manufactura", ["mantenimiento", "electricidad", "seguridad industrial", "mecanica"], "Técnico electromecánico", "planes preventivos y registros de mantenimiento de equipos de producción", 2700000),
    ("Abogado de contratos", "legal", "Legal", ["derecho contractual", "redaccion", "negociacion", "investigacion juridica"], "Derecho", "revisión de contratos de proveedores y matriz de riesgos jurídicos", 4400000),
    ("Docente de formación técnica", "education", "Educacion", ["pedagogia", "evaluacion", "excel", "comunicacion"], "Licenciatura en educación", "sesiones prácticas y rúbricas para acompañar procesos de aprendizaje", 3000000),
    ("Diseñador gráfico", "design", "Marketing y publicidad", ["figma", "illustrator", "photoshop", "diseño grafico"], "Diseño gráfico", "piezas visuales y prototipos coherentes con el sistema de marca", 3100000),
    ("Agente de servicio al cliente", "service", "BPO y contact center", ["servicio al cliente", "crm", "comunicacion", "excel"], "Técnico en asistencia administrativa", "resolución de solicitudes y seguimiento de casos en canales digitales", 1800000),
    ("Ingeniero de automatización", "electronics", "Energia y servicios publicos", ["plc", "automatizacion", "electricidad", "instrumentacion"], "Ingeniería electrónica", "pruebas de instrumentación y documentación de sistemas de control", 4700000),
    ("Analista administrativo", "business", "Administracion y servicios empresariales", ["excel", "presupuestos", "gestion documental", "compras"], "Administración de empresas", "seguimiento de compras y control documental del área administrativa", 2900000),
    ("Auxiliar de farmacia", "health", "Farmaceutica y biotecnologia", ["dispensacion", "inventarios", "servicio al cliente", "bioseguridad"], "Técnico en servicios farmacéuticos", "dispensación y control de inventarios siguiendo protocolos farmacéuticos", 1900000),
]
NAMES = ["Camila", "Andrés", "Valeria", "Diego", "Mariana", "Nicolás", "Laura", "Felipe", "Daniela", "Mateo", "Sara", "Julián", "Paula", "Santiago", "Lucía", "David", "Natalia", "Tomás", "Isabel", "Sebastián", "Ana", "Juan", "Elena", "Gabriel", "Sofía", "Daniel", "Catalina", "Martín", "Diana", "Simón"]
SURNAMES = ["Restrepo", "Gómez", "Ramírez", "Torres", "Moreno", "Castro", "Vargas", "Rojas", "Herrera", "Jiménez"]
COHORTS = [(0, "junior", 0), (1, "mid", 1), (2, "junior", 1)]
INDUSTRY_ROLES = {
    "Finanzas y banca": [3, 7, 8, 9, 11, 13, 14, 16, 6],
    "Alimentos y bebidas": [10, 6, 7, 8, 9, 15, 16, 11, 3],
    "Energia y servicios publicos": [15, 10, 6, 5, 8, 11, 16, 3, 14],
    "Construccion e ingenieria": [5, 6, 10, 8, 11, 16, 7, 13, 14],
    "Inmobiliario": [5, 6, 10, 8, 11, 16, 7, 13, 14],
    "Salud y bienestar": [4, 17, 6, 8, 14, 16, 9, 3, 12],
    "Farmaceutica y biotecnologia": [17, 6, 10, 8, 14, 16, 9, 3, 11],
    "Servicios profesionales": [4, 12, 8, 11, 16, 7, 14, 6, 13],
    "Logistica y transporte": [6, 10, 7, 14, 8, 11, 16, 3, 13],
}


def replace_old_data(db):
    """Delete the requested roots and all their dependent rows in one transaction.

    All administrator identities and personal candidates remain untouched.
    Discover dependencies from metadata instead of relying on optional SQLite FK
    enforcement or maintaining an incomplete hand-written table list.
    """
    removed = {table.name: set() for table in Base.metadata.sorted_tables}
    users = db.execute(select(User)).scalars().all()
    for user in users:
        fixture = user.email.lower().endswith((".test", ".invalid", ".localhost", "example.com", "example.org", "example.net"))
        if user.role != UserRole.ADMIN and (user.role == UserRole.COMPANY or fixture):
            removed["users"].add(user.id)
    for model in (Company, Job):
        removed[model.__tablename__] = set(db.execute(select(model.id)).scalars())
    changed = True
    while changed:
        changed = False
        for table in Base.metadata.sorted_tables:
            primary = list(table.primary_key.columns)
            if len(primary) != 1:
                raise RuntimeError(f"Unexpected composite primary key: {table.name}")
            predicates = [foreign.parent.in_(removed[foreign.column.table.name]) for foreign in table.foreign_keys if removed[foreign.column.table.name]]
            if predicates:
                values = set(db.execute(select(primary[0]).where(or_(*predicates))).scalars())
                new = values - removed[table.name]
                removed[table.name].update(new)
                changed |= bool(new)
    # Audit entity IDs and notification links are intentionally not foreign keys.
    # Remove references to retired records before SQLite can reuse their IDs.
    for kind, table_name in {"user": "users", "company": "companies", "job": "jobs", "application": "applications", "profile": "profiles"}.items():
        if removed[table_name]:
            removed["event_log"].update(db.execute(select(EventLog.id).where(EventLog.entity_type == kind, EventLog.entity_id.in_(removed[table_name]))).scalars())
    admin_ids = {user.id for user in users if user.role == UserRole.ADMIN}
    for notice in db.execute(select(Notification)).scalars():
        if notice.user_id not in admin_ids and (notice.action_url or "").startswith(("/vacantes/", "/procesos/", "/postulaciones?focus=", "/empresa/postulaciones?job=", "/empresas/")):
            removed["notifications"].add(notice.id)
    for table in reversed(Base.metadata.sorted_tables):
        if removed[table.name]:
            db.execute(delete(table).where(list(table.primary_key.columns)[0].in_(removed[table.name])))
    for entity in list(db.identity_map.values()):
        state = inspect(entity)
        if state.identity and state.identity[0] in removed[state.mapper.local_table.name]:
            db.expunge(entity)
    db.expire_all()
    return {key: len(value) for key, value in removed.items() if value}


def seed(db, password):
    now = datetime.utcnow()
    password_hash = hash_password(password)
    accounts, companies, candidates, jobs = [], [], [], []
    for index, (name, sector, city) in enumerate(COMPANIES):
        owner = User(name=f"Selección {name}", email=f"empresa.{index + 1:02d}@pruebas.talentsync.example.com", role=UserRole.COMPANY, password_hash=password_hash, email_verified=True)
        db.add(owner); db.flush()
        company = Company(owner_user_id=owner.id, name=name, nit=f"LOCAL-CO-{index + 1:03d}", sector=sector, location=city, size="1001+", source_name="local-realistic",
            description=f"Perfil local de pruebas inspirado en {name}. Equipo de {sector.lower()} con operaciones en Colombia. Las vacantes, salarios y procesos recreados no son oficiales ni representan a la empresa.",
            mission="Desarrollar servicios confiables y mejorar la experiencia de clientes mediante equipos colaborativos y procesos medibles.",
            values=["Colaboración", "Servicio", "Aprendizaje continuo", "Integridad"], benefits=["Formación continua", "Acompañamiento al ingreso", "Bienestar"], verification_status="pending")
        db.add(company); db.flush(); companies.append(company)
        if index < 3:
            accounts.append({"type": "Empresa", "name": name, "email": owner.email})
        for position in range(12):
            if position < 3:
                role_index, level, city_index = COHORTS[position]
            else:
                pool = INDUSTRY_ROLES.get(sector, [6, 10, 7, 8, 9, 13, 14, 16, 3])
                role_index = pool[position - 3]
                level = ["entry", "junior", "mid", "senior"][position % 4]
                city_index = (index + position) % len(CITIES)
            title, family, job_sector, skills, degree, outcome, base = ROLES[role_index]
            city, department = CITIES[city_index]
            quality = (index + position) % 3
            salary = base + ((index * 7 + position * 3) % 15) * 85000
            detail = {"version": 1, "seniority": level, "experience_years": {"entry": 0, "junior": 1, "mid": 3, "senior": 5}[level],
                "salary_currency": "COP", "salary_period": "monthly", "salary_basis": "gross_base", "weekly_hours": 40,
                "contract_type": "indefinite", "salary_max": salary + 650000, "schedule": "Lunes a viernes, de 8:00 a 17:00, una hora de descanso",
                "missions": [{"outcome": f"Entregar {outcome} con el equipo responsable", "measure": "Revisión de entregables con criterios acordados y registro de incidencias", "days": 60, "skill": skills[0]}],
                "interview_count": 2, "process_days": 21, "learnable_skills": []}
            if quality == 1:
                detail.update(missions=[], interview_count=None, process_days=None)
            elif quality == 2:
                detail.update(missions=[], schedule="", interview_count=None, process_days=None, experience_years=None)
            job = Job(company_id=company.id, title=title, description=f"En el equipo de {name} buscamos {title.lower()} para trabajar en {outcome}. Coordinarás prioridades con el área responsable, revisarás datos y documentarás decisiones. Presentarás avances semanales y participarás en revisiones de calidad con un equipo de 4 a 8 personas. Tendrás acompañamiento durante las primeras semanas y herramientas para preparar tus entregables.",
                requirements=f"Formación relacionada con {degree.lower()}. Uso de {', '.join(skills[:4])}. Comparte ejemplos de trabajo o proyectos de formación y explica qué hiciste, las herramientas utilizadas y cómo comprobaste los resultados. Evaluamos evidencias relacionadas con las responsabilidades del cargo.",
                skills=skills, skill_requirements=[{"skill": skill, "essential": i < 2, "weight": 3 if i < 2 else 1} for i, skill in enumerate(skills)],
                salary=salary, location=city, department=department, sector=job_sector, modality="hybrid" if position < 3 else ["remote", "onsite", "hybrid"][position % 3],
                employment_type="full_time", status="active", source_name="local-realistic", external_id=f"co-{index}-role-{position}",
                benefits=["Acompañamiento al ingreso", "Formación continua"], quality_details=detail, pipeline_stages=default_stages(), response_days=7,
                blind_hiring=False, required_education_level="technical" if role_index in {4, 7, 10, 14, 17} else "university", required_study_fields=[degree],
                languages=[{"name": "Inglés", "level": "B1"}] if family in {"software", "data"} else [],
                created_at=now - timedelta(days=(index + position * 2) % 25), expires_at=now + timedelta(days=45))
            db.add(job); jobs.append((job, role_index, level, city_index))
    db.flush()
    for group, (role_index, level, city_index) in enumerate(COHORTS):
        title, family, sector, skills, degree, outcome, base = ROLES[role_index]
        for index, name in enumerate(NAMES):
            full_name = f"{NAMES[(index + group * 8) % len(NAMES)]} {SURNAMES[(index + group * 3) % len(SURNAMES)]} {SURNAMES[(index + group * 3 + 4) % len(SURNAMES)]}"
            user = User(name=full_name, email=f"candidato.{group + 1}.{index + 1:02d}@pruebas.talentsync.example.com", role=UserRole.CANDIDATE, password_hash=password_hash, email_verified=True)
            db.add(user); db.flush()
            known = skills[:-1] if index == 0 else [skill for offset, skill in enumerate(skills) if (index + offset * 7) % 30 < 18 + offset % 5]
            known = known or [skills[0]]
            city, department = CITIES[city_index]
            description = f"{title} con experiencia en {outcome}. Uso {', '.join(known[:4])} para organizar entregables, revisar información y colaborar con equipos de producto y operaciones. Documento decisiones, preparo pruebas y presento avances con indicadores concretos."
            evidence_description = f"Desarrollé {outcome}. Organicé requisitos con el equipo, preparé entregables usando {', '.join(known[:3])} y documenté los resultados. Reduje en un {12 + index % 9}% el tiempo de preparación mediante validaciones y seguimiento semanal."
            profile = Profile(user_id=user.id, profession=title, skills=known, location=city, department=department, preferred_sector=sector, preferred_modality="hybrid", availability="two_weeks", desired_salary=base - 200000 + index * 40000,
                experience=description, education=degree, resume_style=["modern", "classic", "minimal"][group], resume_color="default",
                experiences=[{"role": title, "company": "Servicios profesionales integrados", "start_date": "2023-01" if level == "junior" else "2020-02", "end_date": "2025-12", "is_current": False, "description": evidence_description},
                    {"role": f"Practicante de {degree.lower()}", "company": "Centro de proyectos académicos", "start_date": "2022-02" if level == "junior" else "2019-02", "end_date": "2022-11" if level == "junior" else "2019-12", "is_current": False, "description": f"Apoyé al equipo en la preparación de {outcome}. Revisé registros, organicé información y presenté un informe de cierre."}],
                educations=[{"degree": degree, "institution": ["Universidad de Antioquia", "Universidad Nacional de Colombia", "Universidad del Valle"][group], "level": "university", "start_year": "2017", "end_year": "2022", "is_current": False}],
                certifications=[{"name": f"Formación complementaria en {known[0]}", "issuer": "Centro de formación continua", "year": "2025", "description": "Registro de prueba; sin credencial real emitida."}],
                evidence=[{"id": f"local-project-{group}-{index}", "title": f"Proyecto de {title.lower()}", "kind": "project", "description": evidence_description, "skills": known[:3], "verified": False, "add_to_profile": False, "created_at": now.isoformat()}],
                languages=[{"name": "Español", "level": "NATIVE"}, {"name": "Inglés", "level": ["B2", "B1", "A2"][index % 3]}],
                preferences={"local_fixture": True, "mobility": {"willing_to_relocate": True, "willing_to_travel": True}, "market_participation": {"enabled": True, "confirmed_real": False, "family": family, "level": level, "updated_at": now.isoformat() + "Z"}})
            db.add(profile); candidates.append((user, role_index))
            if index == 0:
                accounts.append({"type": "Candidato", "name": full_name, "profession": title, "email": user.email})
    # Named candidates from additional professions keep recruitment varied.
    for index, role_index in enumerate(range(3, len(ROLES))):
        title, family, sector, skills, degree, outcome, base = ROLES[role_index]
        city, department = CITIES[index % len(CITIES)]
        user = User(name=f"{NAMES[index]} {SURNAMES[(index + 2) % 10]}", email=f"especialista.{index + 1:02d}@pruebas.talentsync.example.com", role=UserRole.CANDIDATE, password_hash=password_hash, email_verified=True)
        db.add(user); db.flush()
        db.add(Profile(user_id=user.id, profession=title, skills=skills, location=city, department=department, experience=f"Experiencia en {outcome}. Coordino entregables con el equipo, reviso información y documento resultados de los proyectos.",
            experiences=[{"role": title, "company": "Servicios regionales", "start_date": "2021-01", "end_date": "2025-12", "description": f"Preparé {outcome}. Revisé los resultados y presenté informes de seguimiento usando {', '.join(skills[:3])}."}],
            educations=[{"degree": degree, "institution": "SENA" if "Técnic" in degree else "Universidad Nacional de Colombia", "level": "technical" if "Técnic" in degree else "university", "start_year": "2017", "end_year": "2020", "is_current": False}],
            languages=[{"name": "Español", "level": "NATIVE"}], preferred_sector=sector, preferred_modality="onsite", availability="immediate", desired_salary=base,
            preferences={"local_fixture": True, "mobility": {"willing_to_relocate": True}}))
        candidates.append((user, role_index))
    db.flush()
    states = [(ApplicationStatus.SUBMITTED, "submitted"), (ApplicationStatus.REVIEWING, "reviewing"), (ApplicationStatus.TECHNICAL_INTERVIEW, "interview"), (ApplicationStatus.HIRED, "hired"), (ApplicationStatus.REJECTED, "rejected")]
    application_count = 0
    for index, (job, role_index, level, city_index) in enumerate(jobs):
        eligible = [user for user, role in candidates if role == role_index]
        company_index, position = divmod(index, 12)
        selected = [eligible[(company_index + offset) % len(eligible)] for offset in range(min(5, len(eligible)))]
        for offset, user in enumerate(selected):
            status, stage = states[(company_index // 6 + position + offset) % len(states)]
            created = now - timedelta(days=2 if stage == "submitted" else 5)
            application = Application(user_id=user.id, job_id=job.id, status=status, pipeline_stage=stage, created_at=created,
                first_response_at=None if stage == "submitted" else created + timedelta(hours=20),
                response_due_at=None if stage in {"hired", "rejected"} else now + timedelta(days=5),
                interview_at=now + timedelta(days=2) if stage == "interview" else None,
                recruiter_notes="Revisar los entregables del proyecto y acordar disponibilidad." if stage != "submitted" else None,
                resolution_reason="requirements" if stage == "rejected" else None)
            db.add(application); db.flush(); application_count += 1
            db.add(EventLog(actor_user_id=user.id, event_type="application.created", entity_type="application", entity_id=application.id, created_at=created, details={"job_id": job.id, "local_fixture": True}))
            if stage != "submitted":
                stages = [(ApplicationStatus.REVIEWING, "reviewing")]
                if stage in {"interview", "hired"}:
                    stages.append((ApplicationStatus.TECHNICAL_INTERVIEW, "interview"))
                if stage in {"hired", "rejected"}:
                    stages.append((status, stage))
                previous_status, previous_stage = ApplicationStatus.SUBMITTED, "submitted"
                for step, (step_status, step_stage) in enumerate(stages, 1):
                    db.add(EventLog(actor_user_id=job.company.owner_user_id, event_type="application.transition", entity_type="application", entity_id=application.id, created_at=created + timedelta(hours=20 * step),
                        details={"status": step_status.value, "previous_status": previous_status.value, "stage": step_stage, "previous_stage": previous_stage, "job_id": job.id, "source": "company", "deadline": application.response_due_at.isoformat() if application.response_due_at else None}))
                    previous_status, previous_stage = step_status, step_stage
                db.add(Notification(user_id=user.id, type="application_status", title="Tu proceso tiene una actualización", body=f"Consulta el avance de tu postulación a {job.title} en {job.company.name}.", action_url=f"/postulaciones?focus={application.id}", created_at=created + timedelta(hours=20 * len(stages))))
    db.flush()
    return {"companies": len(companies), "jobs": len(jobs), "candidates": len(candidates), "applications": application_count, "accounts": accounts}


def main():
    from app.core.config import settings
    from app.infrastructure.database.session import SessionLocal

    root = Path(__file__).resolve().parents[2]
    database = root / ".local/talentsync.sqlite3"
    if settings.environment != "development" or settings.database_url != f"sqlite:///{database.as_posix()}":
        raise SystemExit("Solo se permite la base aislada .local/talentsync.sqlite3 de desarrollo")
    folder = root / ".local/backups"; folder.mkdir(parents=True, exist_ok=True)
    backup = folder / f"before-realistic-{datetime.utcnow():%Y%m%d-%H%M%S}.sqlite3"
    with sqlite3.connect(database) as source, sqlite3.connect(backup) as target:
        source.backup(target)
    password = "TS!" + token_urlsafe(18)
    with SessionLocal() as db:
        administrators = [tuple(row) for row in db.execute(select(User.__table__).where(User.role == UserRole.ADMIN))]
        deleted = replace_old_data(db)
        result = seed(db, password)
        assert administrators == [tuple(row) for row in db.execute(select(User.__table__).where(User.role == UserRole.ADMIN))]
        assert not db.connection().exec_driver_sql("PRAGMA foreign_key_check").fetchall()
        db.commit()
    access = {**result, "password": password, "backup": str(backup), "removed": deleted}
    (root / ".local/realistic-accounts.json").write_text(json.dumps(access, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Accesos locales de TalentSync", "", "Abre http://127.0.0.1:5173. Cuentas y contenido de prueba; las empresas no han publicado estas vacantes.", "", f"Contraseña para estas seis cuentas: `{password}`", "", "| Tipo | Perfil | Correo |", "|---|---|---|"]
    lines += [f"| {row['type']} | {row['name']} · {row.get('profession', 'Selección y contratación')} | {row['email']} |" for row in result["accounts"]]
    lines += ["", "Las cuentas de administrador y los perfiles personales se conservaron. Los grupos comparables tienen 30 perfiles y las referencias salariales, 30 empresas.", "", "En cuentas de empresa, configura la verificación en dos pasos desde Seguridad cuando la plataforma lo solicite. No se ha desactivado la protección."]
    (root / ".local/ACCESOS-PRUEBAS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "accounts"}))
    print("Accesos: .local/ACCESOS-PRUEBAS.md; copia de seguridad: " + str(backup))


if __name__ == "__main__":
    main()
