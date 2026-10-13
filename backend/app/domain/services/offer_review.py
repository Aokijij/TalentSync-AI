"""Explainable local rules. No model calls, hiring predictions or market estimates."""
import re
from collections import Counter
from datetime import datetime, timedelta
from statistics import median

REASONS = {
    "salary": ("Salario", "Revisa el rango y explica la parte fija y variable."),
    "requirements": ("Requisitos", "Distingue habilidades esenciales, deseables y que pueden aprenderse."),
    "unclear": ("Información poco clara", "Concreta responsabilidades, resultados y condiciones."),
    "modality": ("Modalidad o ubicación", "Aclara la asistencia presencial y las restricciones del trabajo remoto."),
    "process": ("Proceso de selección", "Revisa entrevistas, duración estimada y plazo de respuesta."),
    "other": ("Otro motivo", "Revisa la oferta con el equipo; este motivo no identifica una causa concreta."),
}


def details_for(job):
    return getattr(job, "quality_details", None) or {}


def local_reference(job, peers):
    details = details_for(job)
    tokens = set(re.findall(r"\w+", (job.title or "").casefold())) - {"de", "en", "y", "senior", "junior"}
    # One observation per company; only structured, recent offers with comparable conditions.
    companies = {}
    for peer in peers:
        other = details_for(peer)
        created = getattr(peer, "created_at", None)
        if (not other or not peer.salary or peer.salary <= 0
                or getattr(peer, "source_name", None) == "local-quality-demo"
                or peer.id == getattr(job, "id", None)
                or peer.company_id == getattr(job, "company_id", None)
                or getattr(peer, "source_kind", "internal") != "internal"
                or not created or created.replace(tzinfo=None) < datetime.utcnow() - timedelta(days=180)):
            continue
        if (peer.sector != job.sector or peer.modality != job.modality
                or (peer.location or "").strip().casefold() != (job.location or "").strip().casefold()
                or peer.employment_type != job.employment_type
                or any(other.get(key) != details.get(key) for key in ("contract_type", "seniority", "experience_years", "schedule"))
                or not tokens.intersection(re.findall(r"\w+", peer.title.casefold()))):
            continue
        companies.setdefault(peer.company_id, []).append(peer.salary)
    salaries = [median(values) for values in companies.values()]
    value = round(median(salaries), 2) if len(salaries) >= 5 else None
    return {"source": "local_structured_vacancies", "sample_size": len(salaries), "minimum_sample": 5,
            "currency": "COP", "median": value, "as_of": datetime.utcnow().isoformat(),
            "notice": "Referencia de salarios mínimos fijos de ofertas locales de los últimos 180 días. Una observación por empresa; no representa el mercado ni una probabilidad de contratación. Se excluyen los ejemplos de esta revisión."}


def review_offer(job, peers=()):
    d = details_for(job)
    title = (job.title or "").strip()
    description = (job.description or "").strip()
    requirements = (job.requirements or "").strip()
    text = f"{title} {description} {requirements}".casefold()
    skills = getattr(job, "skill_requirements", None) or []
    missions = d.get("missions") or []
    issues = []

    def issue(code, message, step, field, severity="advice", suggestion=None, phrase=None):
        issues.append({"code": code, "message": message, "step": step, "field": field,
                       "severity": severity, "suggestion": suggestion, "phrase": phrase})

    years = [int(value) for value in re.findall(r"(\d{1,2})\s*(?:años|years)", requirements.casefold())]
    if d.get("experience_years") is not None:
        years.append(d["experience_years"])
    initial = d.get("seniority") in {"entry", "junior"} or bool(re.search(r"\b(?:junior|entry level|sin experiencia)\b", text))
    if initial and any(value >= 5 for value in years):
        issue("level_conflict", "Un cargo inicial solicita cinco años o más. Alinea el nivel, la experiencia y las responsabilidades.", 2, "requirements", "critical")
    if re.search(r"(?:edad\s*(?:entre|máxima|minima|mínima)|solo\s+(?:hombres|mujeres)|buena\s+presencia)", text):
        issue("personal_restrictions", "Revisa restricciones personales que no describen competencias necesarias para el cargo.", 2, "requirements", "critical")
    for phrase, suggestion in [
        ("trabajo bajo presión", "Explica qué situaciones requieren priorizar tareas y qué apoyo tendrá la persona."),
        ("tolerancia a la frustración", "Describe las situaciones difíciles del cargo y cómo se acompañan."),
        ("guerrero", "Describe cambios habituales del trabajo y las decisiones que deberá tomar."),
        ("dinámico", "Sustituye el adjetivo por una acción o responsabilidad observable."),
        ("salario competitivo", "Publica el valor fijo o rango real y explica las comisiones por separado."),
    ]:
        for field, value in (("title", title), ("description", description), ("requirements", requirements)):
            if phrase in value.casefold():
                issue(f"wording_{phrase}_{field}", f'Concreta la expresión «{phrase}».', 1 if field == "description" else 2 if field == "requirements" else 0, field,
                      suggestion=suggestion, phrase=phrase)
    if len(skills) > 10:
        issue("many_requirements", "Hay más de diez habilidades. Revisa cuáles son realmente necesarias y cuáles pueden aprenderse.", 2, "skill_requirements")
    learnable = {value.strip().casefold() for value in d.get("learnable_skills", [])}
    if any(row.get("essential") and row.get("skill", "").strip().casefold() in learnable for row in skills):
        issue("learnable_conflict", "Una habilidad figura como esencial al ingreso y también como aprendible. Elige una condición coherente.", 2, "skill_requirements", "critical")
    salary = job.salary or 0
    salary_max = d.get("salary_max")
    if salary <= 0:
        issue("salary_missing", "Publica un salario fijo o rango real para que las personas puedan decidir con información.", 0, "salary")
    range_ok = salary > 0 and (salary_max is None or salary_max >= salary)
    if salary_max is not None and salary_max < salary:
        issue("salary_range", "El máximo del rango no puede ser menor que el mínimo.", 0, "salary", "critical")
    action = bool(re.search(r"\b(?:desarroll|registr|analiz|revis|gestion|coordin|atend|prepar|diseñ|implement|manten|verific|concil|organiz|control|document|program|supervis|apoy|resolv|oper|realiz|crea|constru)\w*", description.casefold()))
    context = bool(re.search(r"\b(?:equipo|resultado|entrega|cliente|reporte|informe|proyecto|proceso|venta|soporte|servicio|producto|registro|sistema)\w*", description.casefold()))
    critical = any(row["severity"] == "critical" for row in issues)
    def meaningful(value, minimum, words):
        return len(value.strip()) >= minimum and len(set(re.findall(r"\w+", value.casefold()))) >= words
    complete_missions = bool(missions) and all(meaningful(row.get("outcome", ""), 15, 4) and meaningful(row.get("measure", ""), 10, 3) and 1 <= (row.get("days") or 0) <= 365 for row in missions)
    schedule = d.get("schedule", "").strip().casefold()
    schedule_ok = meaningful(schedule, 10, 3) and bool(re.search(r"lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo|d[ií]as|seman|turnos", schedule)) and bool(re.search(r"\d|horario|diurn|nocturn|rotativ", schedule))
    response_days = getattr(job, "response_days", 0) or 0
    process_days = d.get("process_days") or 0
    if process_days and response_days > process_days:
        issue("process_conflict", "El plazo de respuesta por avance supera la duración total estimada del proceso.", 3, "response_days", "critical")
        critical = True
    checks = []

    def check(key, label, weight, passed, step, action_text, required=False):
        checks.append({"key": key, "label": label, "weight": weight, "passed": bool(passed),
                       "step": step, "action": action_text, "required": required,
                       "priority": "Obligatorio" if required else "Mejora"})

    check("title", "Cargo específico", 0, 5 <= len(title) <= 180 and len(set(re.findall(r"\w+", title))) >= 2 and not re.search(r"\b(?:urgente|gana dinero)\b", title.casefold()), 0, "Usa un nombre específico de cargo, sin reclamos publicitarios.", True)
    check("salary", "Salario fijo o rango real", 10, range_ok, 0, "Publica un salario fijo mensual positivo en COP. El rango máximo es opcional.", True)
    check("contract_type", "Contrato definido", 7, d.get("contract_type"), 0, "Selecciona el tipo de contrato, separado de la dedicación.", True)
    check("schedule", "Jornada y horario", 7, schedule_ok, 0, "Completa Jornada y horario con días y horas o turnos. Ejemplo: lunes a viernes, 8:00 a 17:00, una hora de descanso. Para turnos, explica días, rotación y franjas.", True)
    check("location", "Modalidad y ubicación", 6, job.modality in {"remote", "hybrid", "onsite"} and bool((job.location or "").strip()), 0, "Indica la ciudad o el territorio permitido para trabajar de forma remota.", True)
    check("description", "Responsabilidades concretas", 12, meaningful(description, 100, 10) and action and context, 1, "En Responsabilidades y contexto escribe qué hará, para quién y qué entregará. Ejemplo: conciliará facturas para preparar el cierre mensual con el equipo contable.", True)
    check("missions", "Resultados esperados y evaluación", 13, complete_missions, 1, "Define al menos un resultado, cómo se evaluará y en qué plazo.", True)
    check("requirements", "Experiencia y nivel explícitos", 10, meaningful(requirements, 60, 8) and d.get("seniority") and d.get("experience_years") is not None, 2, "Completa Nivel del cargo, Experiencia mínima y Conocimientos y evidencia aceptada. Se permite 0 años. Explica qué debe demostrar y si aceptas proyectos de formación.", True)
    check("skill_requirements", "Habilidades priorizadas", 10, 1 <= len(skills) <= 10 and any(row.get("essential") for row in skills), 2, "Define hasta diez habilidades y distingue esenciales de deseables.", True)
    check("process", "Entrevistas y duración estimada", 10, d.get("interview_count") is not None and process_days >= 1 and bool(getattr(job, "pipeline_stages", None)), 3, "Declara entrevistas, etapas y duración estimada del proceso.", True)
    check("response_days", "Compromiso de respuesta", 5, 1 <= response_days <= 14 and response_days <= process_days, 3, "Acuerda respuesta por avance de hasta catorce días y dentro del plazo total.", True)
    check("inclusive", "Lenguaje y requisitos coherentes", 10, not critical and not any(row["code"].startswith("wording_") for row in issues), 2, "Retira frases genéricas y resuelve las contradicciones señaladas.")
    score = sum(row["weight"] for row in checks if row["passed"])
    blockers = [row for row in checks if row["required"] and not row["passed"]]
    can_publish = not blockers and not critical
    reference = local_reference(job, peers)
    if salary and reference["median"] and salary < reference["median"] * .65:
        issue("salary_below_local_reference", "El mínimo fijo está por debajo del 65% de la referencia local. Revisa las condiciones comparadas antes de cambiarlo.", 0, "salary")
    pending = sorted((row for row in checks if not row["passed"]), key=lambda row: (not row["required"], -row["weight"]))
    return {"version": 1, "completeness": score, "score": score, "level": "A" if can_publish and score >= 90 and not any(row["code"].startswith("wording_") for row in issues) else "B" if can_publish else "Pendiente",
            "checks": checks, "issues": issues, "next_actions": pending, "blockers": blockers, "can_publish": can_publish,
            "readiness": "Lista para publicar" if can_publish else "Completa los requisitos de publicación",
            "salary_reference": reference, "blind_hiring": getattr(job, "blind_hiring", False),
            "notice": "Revisión de claridad y coherencia basada en reglas locales. La puntuación no modifica la compatibilidad ni garantiza condiciones laborales."}


def feedback_summary(rows, revision):
    current = [row for row in rows if row.revision == revision]
    counts = Counter(row.reason for row in current)
    enough = len(current) >= 5
    return {"revision": revision, "minimum_sample": 5, "sample_size": len(current), "available": enough,
            "reasons": [{"key": key, "label": label, "count": counts[key], "action": action} for key, (label, action) in REASONS.items()] if enough else [],
            "notice": "Opiniones voluntarias sobre esta versión de la oferta. Se muestran desde cinco respuestas, sin identificar candidatos; no representan a todas las personas que la vieron."}
