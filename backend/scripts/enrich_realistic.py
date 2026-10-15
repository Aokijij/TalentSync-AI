"""Upgrade local fixtures in place, retaining identities and recruitment history."""
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from app.api.schemas.job import ScreeningQuestionConfig
from app.api.schemas.job_quality import QualityDetails
from app.application.use_cases.applications import _screening_result
from app.domain.entities.enums import UserRole
from app.domain.services.languages import language_levels
from app.domain.services.skills import normalize_skills
from app.infrastructure.database.models import Application, Company, Job, Profile, User
from scripts.seed_realistic import CITIES, NAMES, ROLES, SURNAMES

# Original cases for local testing; these do not describe real company projects.
BUSINESS_CASES = [
    ("Canales digitales", "apertura de productos con validación documental", "solicitudes incompletas y tiempos de aprobación"),
    ("Pagos y recaudos", "conciliación de pagos recurrentes y devoluciones", "cobros duplicados y partidas pendientes"),
    ("Banca empresarial", "seguimiento de solicitudes de crédito de pequeñas empresas", "documentos vencidos y trazabilidad de decisiones"),
    ("Comercio electrónico", "retiro de compras en tienda y sustitución de productos", "pedidos divididos entre sedes y faltantes"),
    ("Planeación comercial", "pronóstico de abastecimiento para distribuidores regionales", "diferencias entre ventas, inventario y entregas"),
    ("Cadena de frío", "seguimiento de lotes de productos refrigerados", "temperaturas fuera de rango y fechas de vencimiento"),
    ("Abastecimiento", "programación de recolecciones y entregas de materia prima", "cambios de volumen y trazabilidad del proveedor"),
    ("Distribución nacional", "alistamiento de pedidos de temporada para mayoristas", "errores de referencias y devoluciones"),
    ("Operación regional", "reposición en puntos de venta con rutas de distribución", "quiebres de inventario y entregas parciales"),
    ("Producción y calidad", "liberación de lotes y seguimiento de no conformidades", "reprocesos y registros de calidad incompletos"),
    ("Gestión de activos", "programación de inspecciones de equipos operativos", "alertas de mantenimiento y permisos pendientes"),
    ("Servicios al usuario", "atención de solicitudes de conexión y revisión de consumo", "casos repetidos y cruces de información"),
    ("Operación de redes", "seguimiento de órdenes de inspección y mantenimiento", "hallazgos sin cierre y evidencia técnica dispersa"),
    ("Servicios energéticos", "acompañamiento a clientes con proyectos de eficiencia", "mediciones inconsistentes y cambios de alcance"),
    ("Proyectos de infraestructura", "programación de despachos para obras regionales", "restricciones de acceso y cambios de programación"),
    ("Transformación industrial", "control de referencias y defectos de producción", "variación de especificaciones y desperdicio"),
    ("Gestión de siniestros", "seguimiento de reclamaciones y documentos de soporte", "expedientes duplicados y plazos de revisión"),
    ("Operación de estaciones", "conciliación de ventas y abastecimiento de sedes", "diferencias de caja y registros de recepción"),
    ("Última milla", "seguimiento de envíos con entrega fallida", "direcciones inconsistentes y novedades sin soporte"),
    ("Centros de distribución", "programación de cargues y consolidación de pedidos", "ocupación de muelles y diferencias de peso"),
    ("Experiencia de viaje", "gestión de cambios de itinerario y solicitudes de viajeros", "conexiones afectadas y comunicación tardía"),
    ("Operación de tiendas", "control de surtido y atención en puntos regionales", "rotación de productos y filas de atención"),
    ("Canales de venta", "gestión de garantías y entregas de productos", "reclamos sin seguimiento y diagnósticos pendientes"),
    ("Comercio omnicanal", "reserva de prendas y cambios entre tiendas", "tallas no disponibles y diferencias de inventario"),
    ("Planeación de colecciones", "seguimiento de pedidos por referencia y talla", "variación de demanda y retrasos de entrega"),
    ("Operación textil", "control de órdenes de fabricación y calidad de prendas", "reprocesos y cambios de ficha técnica"),
    ("Servicios farmacéuticos", "trazabilidad de dispensaciones y entregas pendientes", "lotes próximos a vencer y novedades de disponibilidad"),
    ("Servicios a afiliados", "programación de actividades y solicitudes de subsidio", "documentos pendientes y cruces de agenda"),
    ("Atención y bienestar", "orientación administrativa y asignación de citas", "inasistencias y registros duplicados"),
    ("Gestión de proyectos", "seguimiento de entregas de vivienda y garantías", "pendientes por contratista y cambios de cronograma"),
]

# Three genuine task variants per occupation, with distinct tools and evidence.
SPECIALTIES = [
    [("formularios y accesibilidad", ["accesibilidad web", "react hook form"], "Construir formularios con validación y recuperación de errores", "pruebas con teclado, lector de pantalla y entradas incompletas"), ("rendimiento de portales", ["vite", "web vitals"], "Reducir la espera al consultar listas extensas", "mediciones antes y después, paginación y pruebas de carga"), ("sistemas de diseño", ["storybook", "testing library"], "Implementar componentes reutilizables y sus estados", "pruebas de interacción, contraste y consistencia visual")],
    [("calidad de datos", ["dbt", "calidad de datos"], "Conciliar fuentes y documentar reglas de calidad", "controles de duplicados, totales y fechas de actualización"), ("inteligencia de negocios", ["dax", "power query"], "Construir indicadores con definiciones compartidas", "validación de medidas con usuarios y conciliación de fuentes"), ("automatización de reportes", ["etl", "postgresql"], "Automatizar cargas incrementales y seguimiento de fallos", "registros de ejecución, reconciliación y pruebas de recuperación")],
    [("cierre y conciliaciones", ["niif", "conciliacion bancaria"], "Conciliar cuentas y sustentar diferencias del cierre", "partidas conciliadas, soportes y revisión del contador"), ("impuestos y facturación", ["retencion en la fuente", "tributaria"], "Revisar impuestos y soportes de facturas recibidas", "validaciones de bases, tarifas y documentos electrónicos"), ("cuentas por pagar", ["sap fi", "cuentas por pagar"], "Programar obligaciones y controlar vencimientos", "conciliación de proveedores y ausencia de pagos duplicados")],
    [("integraciones y pagos", ["pytest", "idempotencia"], "Implementar integraciones con reintentos controlados", "pruebas de duplicados, tiempos de espera y recuperación"), ("seguridad de servicios", ["oauth2", "postgresql"], "Aplicar autorización por recurso y trazabilidad de cambios", "pruebas de acceso ajeno, validaciones y revisión de permisos"), ("observabilidad", ["redis", "observabilidad"], "Instrumentar servicios y diagnosticar fallos de integración", "métricas de latencia, alertas y pruebas de degradación")],
    [("atención ambulatoria", ["humanizacion", "signos vitales"], "Apoyar atención y registrar signos según protocolo y supervisión", "registros completos y verificación por enfermería profesional"), ("seguridad del paciente", ["seguridad del paciente", "control de infecciones"], "Aplicar medidas de prevención y reportar incidentes", "listas de chequeo y revisión de protocolos por el responsable"), ("acompañamiento", ["comunicacion empatica", "primeros auxilios"], "Orientar pacientes y acompañar procedimientos autorizados", "confirmación de comprensión y registro oportuno de novedades")],
    [("presupuestos", ["apu", "ms project"], "Actualizar cantidades de obra y revisar costos con contratistas", "actas de cantidades, soportes y desviación presupuestal"), ("supervisión de obra", ["revit", "bim"], "Coordinar interferencias entre planos y actividades de obra", "registro de cambios y cierre de hallazgos con responsables"), ("programación", ["programacion de obra", "sst"], "Programar frentes de trabajo con recursos y restricciones", "avance semanal frente al cronograma y permisos vigentes")],
    [("planeación de rutas", ["tms", "ruteo"], "Reorganizar rutas según capacidad y ventanas de entrega", "cumplimiento de ventanas y kilómetros por entrega"), ("centro de distribución", ["wms", "picking"], "Coordinar alistamiento y conciliación de inventario", "exactitud de pedidos y diferencias documentadas"), ("abastecimiento", ["pronosticos", "control de stock"], "Planear reposiciones con demanda y tiempos de suministro", "nivel de servicio y quiebres por referencia")],
    [("venta consultiva", ["venta consultiva", "pipeline comercial"], "Diagnosticar necesidades y preparar propuestas transparentes", "oportunidades calificadas y acuerdos de seguimiento"), ("cuentas regionales", ["gestion de cuentas", "cotizaciones"], "Coordinar cotizaciones y seguimiento de cuentas asignadas", "renovaciones y compromisos documentados en CRM"), ("canal digital", ["comercio electronico", "seguimiento comercial"], "Atender consultas y acompañar decisiones de compra", "conversión por canal y registro de objeciones")],
    [("selección", ["entrevista por competencias", "ats"], "Coordinar entrevistas con criterios documentados", "tiempos por etapa y retroalimentación trazable"), ("nómina", ["legislacion laboral", "seguridad social"], "Validar novedades y soportes para liquidación de nómina", "conciliación de aportes y revisión de novedades"), ("desarrollo", ["capacitacion", "analisis de clima"], "Organizar formación y seguimiento de compromisos del equipo", "participación, evaluación y planes de mejora acordados")],
    [("adquisición", ["google ads", "utm"], "Diseñar campañas y controlar presupuesto por segmento", "costo por adquisición y conversiones conciliadas"), ("contenidos", ["copywriting", "search console"], "Planear contenidos útiles y revisar su desempeño orgánico", "tráfico pertinente y conversión con fuentes identificadas"), ("experimentación", ["pruebas ab", "ga4"], "Comparar variantes con hipótesis y métricas previas", "resultados por cohorte y límites de la muestra")],
    [("mantenimiento preventivo", ["cmms", "lubricacion"], "Ejecutar inspecciones y registrar hallazgos en equipos", "órdenes cerradas con evidencia y validación del supervisor"), ("diagnóstico eléctrico", ["lectura de planos", "diagnostico electrico"], "Diagnosticar fallas siguiendo permisos y bloqueo de energía", "mediciones registradas y prueba funcional autorizada"), ("confiabilidad", ["analisis de fallas", "metrologia"], "Analizar fallas repetidas y proponer acciones preventivas", "recurrencia de fallas y trazabilidad de repuestos")],
    [("contratación", ["gestion contractual", "proteccion de datos"], "Revisar obligaciones, cláusulas y riesgos contractuales", "matriz de riesgos y conceptos con soporte normativo"), ("derecho comercial", ["derecho comercial", "debida diligencia"], "Verificar documentación y antecedentes de proveedores", "expediente completo y hallazgos con responsable"), ("controversias", ["litigios", "derecho procesal"], "Organizar expedientes y preparar conceptos de controversias", "plazos procesales verificados y revisión del abogado líder")],
    [("formación presencial", ["didactica", "rubricas"], "Diseñar prácticas accesibles con criterios observables", "evidencias de aprendizaje y retroalimentación individual"), ("formación virtual", ["moodle", "diseno instruccional"], "Adaptar actividades y evaluar barreras de acceso", "participación y cumplimiento de objetivos con alternativas"), ("evaluación", ["evaluacion formativa", "planeacion curricular"], "Revisar resultados y ajustar actividades de aprendizaje", "mejora entre intentos y criterios comunicados previamente")],
    [("interfaces", ["prototipado", "ux research"], "Prototipar flujos y validar comprensión con usuarios", "pruebas de tareas, hallazgos y decisiones justificadas"), ("marca", ["tipografia", "branding"], "Preparar piezas con jerarquía y coherencia de marca", "lista de revisión de legibilidad, permisos y formatos"), ("producción gráfica", ["indesign", "preprensa"], "Preparar archivos finales para impresión y canales digitales", "perfiles de color, sangrados y control de versiones")],
    [("reclamaciones", ["pqrs", "escucha activa"], "Investigar reclamaciones y acordar seguimiento", "casos resueltos con soporte y comunicación de plazos"), ("soporte digital", ["zendesk", "gestion de tickets"], "Clasificar solicitudes y escalar casos con contexto", "tiempo de respuesta y calidad del registro"), ("atención multicanal", ["atencion omnicanal", "resolucion de conflictos"], "Mantener continuidad entre canales de atención", "ausencia de duplicados y cumplimiento de compromisos")],
    [("control industrial", ["scada", "modbus"], "Verificar señales y documentar lógica de control", "pruebas de señales, alarmas y enclavamientos"), ("instrumentación", ["calibracion", "sensores"], "Validar instrumentos y registrar desviaciones", "certificados de calibración y mediciones trazables"), ("automatización", ["hmi", "redes industriales"], "Actualizar interfaces de operación con control de cambios", "pruebas funcionales y aprobación del responsable operativo")],
    [("compras", ["gestion de proveedores", "ordenes de compra"], "Comparar cotizaciones y tramitar compras con soporte", "trazabilidad de aprobaciones y entregas recibidas"), ("gestión documental", ["archivo", "control documental"], "Organizar expedientes con permisos y versiones", "recuperación de documentos y control de acceso"), ("control presupuestal", ["analisis presupuestal", "reportes de gestion"], "Consolidar gastos y explicar desviaciones del área", "conciliación de soportes y revisión del responsable")],
    [("dispensación", ["farmacovigilancia", "buenas practicas de dispensacion"], "Verificar requisitos y apoyar dispensación autorizada", "doble verificación y reporte de novedades al responsable"), ("inventario farmacéutico", ["fefo", "cadena de frio"], "Controlar lotes, vencimientos y condiciones de almacenamiento", "conteos conciliados y registros de temperatura"), ("servicios al usuario", ["trazabilidad de medicamentos", "orientacion al usuario"], "Gestionar entregas pendientes y orientar trámites", "seguimiento de pendientes sin prometer disponibilidad no confirmada")],
]
LEVEL_YEARS = {"entry": 0, "junior": 1, "mid": 3, "senior": 5, "lead": 7}
LEVEL_LABELS = {"entry": "Inicial", "junior": "Junior", "mid": "Intermedio", "senior": "Senior", "lead": "Líder"}
EXTRA_COHORTS = [(0, level, 0) for level in ("entry", "mid", "senior", "lead")] + [(4, "junior", 1), (6, "mid", 0), (7, "junior", 2)]


def questions(skills, task, metric, case):
    return [ScreeningQuestionConfig(**row).model_dump() for row in [
        {"id": "experiencia-aplicada", "prompt": f"Describe un trabajo o proyecto donde utilizaste {skills[0]} para {task.lower()}. ¿Qué hiciste y cómo verificaste el resultado?"[:300], "type": "open", "required": True},
        {"id": "criterio-de-trabajo", "prompt": f"Al trabajar en {case}, encuentras información inconsistente. ¿Cómo continuarías?"[:300], "type": "choice", "required": True,
         "options": ["Verificar la fuente, documentar la diferencia y acordar la corrección", "Modificar el resultado para que coincida sin dejar registro", "Continuar sin comprobar porque el plazo está cerca"],
         "option_scores": {"Verificar la fuente, documentar la diferencia y acordar la corrección": 2, "Modificar el resultado para que coincida sin dejar registro": -2, "Continuar sin comprobar porque el plazo está cerca": -1}},
        {"id": "evidencia-del-resultado", "prompt": f"¿Qué evidencia presentarías para revisar {metric}? Puedes describir un ejemplo de formación si aún no tienes experiencia laboral."[:300], "type": "open", "required": False},
    ]]


def upgrade(db, now=None):
    now = now or datetime.utcnow()
    jobs = list(db.scalars(select(Job).where(Job.source_name == "local-realistic").order_by(Job.id)))
    owners = {row.id: row for row in db.scalars(select(Company).where(Company.source_name == "local-realistic"))}
    changed, protected, adjusted_salary_floors = [], [], 0
    for job in jobs:
        match = re.fullmatch(r"co-(\d+)-role-(\d+)", job.external_id or "")
        if not match:
            if (job.external_id or "").endswith("-v2") and job.quality_revision == 1 and job.employment_type == "full_time" and 0 < (job.salary or 0) < 2_000_000:
                job.salary = 2_000_000
                job.quality_details = {**job.quality_details, "salary_max": max((job.quality_details or {}).get("salary_max") or 0, 2_550_000)}
                job.quality_revision += 1
                adjusted_salary_floors += 1
            continue
        if job.quality_revision:
            protected.append(job.id); continue  # Preserve offers edited through the app.
        company_index, position = map(int, match.groups())
        role_index = next(i for i, row in enumerate(ROLES) if row[0] == job.title)
        title, family, _, base_skills, degree, _, base_salary = ROLES[role_index]
        variant = SPECIALTIES[role_index][(company_index + position) % 3]
        specialty, tools, task, metric = variant
        team, case, challenge = BUSINESS_CASES[company_index]
        skills = normalize_skills([*base_skills, *tools])
        level = (job.quality_details or {}).get("seniority") or "mid"
        if position == 11:
            level = "lead"
        years = LEVEL_YEARS[level]
        autonomy = {"entry": "Contarás con revisión diaria y tareas delimitadas; aceptamos proyectos de formación.", "junior": "Tendrás acompañamiento semanal y revisión de entregables antes de su publicación.", "mid": "Gestionarás entregables completos y acordarás dependencias con otras áreas.", "senior": "Resolverás casos complejos y acompañarás la revisión técnica de otras personas.", "lead": "Coordinarás prioridades y revisiones de un equipo de cinco personas, con autoridad técnica definida."}[level]
        job.title = f"{title} · {specialty} · {LEVEL_LABELS[level]}"
        job.description = (f"Trabajarás en el equipo local de {team.lower()} de {owners[job.company_id].name}, en un caso de {case}. "
            f"El proyecto debe resolver {challenge}.\n\nResponsabilidades:\n• {task}.\n• Revisar los insumos con el área de {team.lower()} y documentar decisiones usando {skills[-2]} y {skills[-1]}.\n"
            f"• Presentar avances semanales y registrar incidencias con responsable y fecha de seguimiento.\n• Entregar documentación que permita a otra persona reproducir y revisar el trabajo.\n\n"
            f"{autonomy} El equipo trabaja con entregas quincenales y una reunión breve de coordinación. La evaluación se centra en {metric}.")
        job.requirements = (f"Formación relacionada con {degree}; se revisan títulos equivalentes y la evidencia aportada. "
            f"{'No se exige experiencia laboral previa' if years == 0 else f'Experiencia mínima de {years} años en funciones relacionadas'}, sin contar dos veces periodos simultáneos. "
            f"Esencial al ingreso: {', '.join(skills[:2])}. Deseable: {', '.join(skills[2:-1])}. "
            f"Puedes aprender {skills[-1]} durante el acompañamiento inicial. Presenta un ejemplo con entradas, decisiones, resultado y validación; no compartas información confidencial de empleadores anteriores.")
        job.skills = skills
        job.skill_requirements = [{"skill": skill, "essential": i < 2, "weight": 3 if i < 2 else 1} for i, skill in enumerate(skills)]
        detail = dict(job.quality_details or {})
        if position >= 3:
            job.salary = max(2_000_000, round((base_salary * {"entry": .55, "junior": .8, "mid": 1, "senior": 1.35, "lead": 1.7}[level] + company_index * 35000) / 10000) * 10000)
        detail.update(seniority=level, experience_years=years, salary_max=job.salary + 550000 + company_index % 4 * 100000,
            schedule="Lunes a viernes, 8:00 a 17:00, con una hora de descanso; 40 horas semanales", weekly_hours=40,
            interview_count=2 if level != "lead" else 3, process_days=14 + company_index % 4 * 7,
            learnable_skills=[skills[-1]], missions=[
                {"outcome": f"{task} para el caso de {case}"[:500], "measure": f"Revisión de {metric}; evidencia y lista de aceptación acordada"[:300], "days": 30 + company_index % 3 * 15, "skill": skills[0]},
                {"outcome": f"Documentar y entregar el flujo de {specialty} con pendientes y responsables", "measure": "Otra persona reproduce la revisión con los soportes; pendientes registrados y priorizados", "days": 90, "skill": skills[-2]},
            ])
        # Every offer has complete publication fields; wording quality still varies.
        if (company_index + position) % 3 == 1:
            job.requirements += " Buscamos un perfil dinámico."
        elif (company_index + position) % 3 == 2:
            job.requirements += " Se requiere trabajo bajo presión y tolerancia a la frustración."
        job.quality_details = QualityDetails(**detail).model_dump()
        job.response_days = [3, 5, 7, 10][company_index % 4]
        job.application_questions = questions(skills, task, metric, case)
        job.languages = [{"name": name, "level": level} for name, level in language_levels(job.languages).items()]
        job.benefits = ["Plan de acompañamiento de 30 días", "Formación relacionada con las funciones", ["Horario de ingreso flexible acordado", "Programa de bienestar", "Mentoría técnica mensual"][company_index % 3]]
        job.external_id += "-v2"
        job.quality_revision = 1
        changed.append(job.id)
    # Add distinct named peers across all five levels, without changing existing accounts.
    added = 0
    sample = db.scalar(select(User).where(User.email == "candidato.1.01@pruebas.talentsync.example.com"))
    if sample:
        for cohort, (role_index, level, city_index) in enumerate(EXTRA_COHORTS):
            title, family, sector, base_skills, degree, outcome, base_salary = ROLES[role_index]
            for index in range(24):
                email = f"comparacion.{cohort + 1}.{index + 1:02d}@pruebas.talentsync.example.com"
                if db.scalar(select(User.id).where(User.email == email)):
                    continue
                specialty, tools, task, metric = SPECIALTIES[role_index][index % 3]
                available = normalize_skills([*base_skills, *tools])
                known = [skill for offset, skill in enumerate(available) if (index + offset * 5) % 24 < 15 + offset % 5] or available[:1]
                user = User(name=f"{NAMES[(index + cohort * 3) % len(NAMES)]} {SURNAMES[(index + cohort) % 10]} {SURNAMES[(index + cohort + 3) % 10]}", email=email, role=UserRole.CANDIDATE, password_hash=sample.password_hash, email_verified=True)
                db.add(user); db.flush()
                years = max(0, LEVEL_YEARS[level])
                work = [] if not years else [{"role": f"{title} · {specialty}", "company": "Equipo de proyectos regionales", "start_date": f"{now.year - years}-01", "end_date": f"{now.year}-09", "is_current": False,
                    "description": f"{task}. Utilicé {', '.join(known[:4])}; documenté decisiones y revisé {metric}. Organicé entregas semanales y un registro de hallazgos; reduje en {10 + index % 12}% los reprocesos del caso local."}]
                city, department = CITIES[city_index]
                db.add(Profile(user_id=user.id, profession=title, skills=known, location=city, department=department,
                    experience=f"Perfil {LEVEL_LABELS[level].lower()} con práctica en {specialty}. {task}. Uso {', '.join(known)} para revisar entregables.", experiences=work,
                    education=degree, educations=[{"degree": degree, "institution": "SENA" if role_index == 4 else "Universidad de Antioquia", "level": "technical" if role_index == 4 else "university", "start_year": str(now.year - years - 5), "end_year": str(now.year - years), "is_current": False}],
                    certifications=[{"name": f"Formación complementaria en {known[0]}", "issuer": "Formación continua local", "year": "2025", "description": "Registro de prueba sin credencial oficial."}],
                    evidence=[{"id": f"comparacion-{cohort}-{index}", "kind": "project", "title": f"Proyecto de {specialty}", "description": f"{task}. Preparé ejemplos con {', '.join(known[:3])}, registré el resultado y sus limitaciones. La revisión utilizó {metric}.", "skills": known[:3], "verified": False, "add_to_profile": False}],
                    languages=[{"name": "español", "level": "NATIVE"}, {"name": "inglés", "level": ["A2", "B1", "B2", "C1"][index % 4]}], preferred_sector=sector, preferred_modality=["remote", "hybrid", "onsite"][index % 3],
                    availability="two_weeks", desired_salary=round(base_salary * (.6 + years * .12) / 10000) * 10000,
                    preferences={"local_fixture": True, "market_participation": {"enabled": True, "confirmed_real": False, "family": family, "level": level, "updated_at": now.isoformat() + "Z"}}))
                added += 1
    # Enrich only untouched fixture answers. Never edit a personal application.
    answered = 0
    for application in db.scalars(select(Application).where(Application.job_id.in_(changed))):
        if application.screening_answers or not (application.user.profile.preferences or {}).get("local_fixture"):
            continue
        job = application.job
        answers = [{"question_id": row["id"], "answer": row["options"][0] if row["type"] == "choice" else f"En un proyecto de {application.user.profile.profession} trabajé con {', '.join(application.user.profile.skills[:3])}. Documenté el resultado, comprobé los datos de entrada y presenté soportes al equipo. Puedo explicar el alcance y las limitaciones en entrevista."} for row in job.application_questions]
        application.screening_answers, application.screening_adjustment = _screening_result(job, answers)
        answered += 1
    db.flush()
    return {"upgraded_jobs": len(changed), "protected_edited_jobs": protected, "added_profiles": added, "fixture_applications_enriched": answered, "adjusted_salary_floors": adjusted_salary_floors,
            "levels": dict(Counter((job.quality_details or {}).get("seniority") for job in jobs)), "skills": len({skill for job in jobs for skill in job.skills or []})}


def main():
    from app.core.config import settings
    from app.infrastructure.database.session import SessionLocal
    root = Path(__file__).resolve().parents[2]
    target = root / ".local/talentsync.sqlite3"
    if settings.environment != "development" or settings.database_url != f"sqlite:///{target.as_posix()}":
        raise SystemExit("This upgrade requires the isolated local development database.")
    backup = root / f".local/backups/before-inplace-upgrade-{datetime.now():%Y%m%d-%H%M%S}.sqlite3"
    backup.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target) as source, sqlite3.connect(backup) as destination:
        source.backup(destination)
    with SessionLocal() as db:
        applications = [(row.id, row.user_id, row.job_id, row.status, row.pipeline_stage) for row in db.scalars(select(Application))]
        protected = [(row.id, row.password_hash, row.name, row.email) for row in db.scalars(select(User).where((User.role == UserRole.ADMIN) | User.id.in_([20, 72])))]
        personal = [(row.user_id, row.preferences, row.skills, row.experiences, row.educations, row.languages) for row in db.scalars(select(Profile).where(Profile.user_id.in_([20, 72])))]
        result = upgrade(db)
        assert applications == [(row.id, row.user_id, row.job_id, row.status, row.pipeline_stage) for row in db.scalars(select(Application))]
        assert protected == [(row.id, row.password_hash, row.name, row.email) for row in db.scalars(select(User).where((User.role == UserRole.ADMIN) | User.id.in_([20, 72])))]
        assert personal == [(row.user_id, row.preferences, row.skills, row.experiences, row.educations, row.languages) for row in db.scalars(select(Profile).where(Profile.user_id.in_([20, 72])))]
        db.commit()
    result["backup"] = str(backup)
    (root / ".local/verification/inplace-upgrade.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
