"""Explainable local rules. No model calls, hiring predictions or market estimates."""
import re
from collections import Counter
from datetime import datetime, timedelta
from statistics import median

from app.domain.services.job_requirements import minimum_experience_months
from app.domain.services.offer_rating import RATING_SCALE, offer_rating
from app.domain.services.skills import skill_key

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
                or any(other.get(key) != details.get(key) for key in ("contract_type", "seniority", "schedule"))
                or minimum_experience_months(other) != minimum_experience_months(details)
                or not tokens.intersection(re.findall(r"\w+", peer.title.casefold()))):
            continue
        companies.setdefault(peer.company_id, []).append(peer.salary)
    salaries = [median(values) for values in companies.values()]
    value = round(median(salaries), 2) if len(salaries) >= 5 else None
    return {"source": "local_structured_vacancies", "sample_size": len(salaries), "minimum_sample": 5,
            "currency": "COP", "median": value, "as_of": datetime.utcnow().isoformat(),
            "notice": "Referencia de salarios mínimos fijos de ofertas locales de los últimos 180 días. Una observación por empresa; no representa el mercado ni una probabilidad de contratación. Se excluyen los ejemplos de esta revisión."}


def review_offer(job, peers=()):
    from app.domain.services.colombian_locations import canonical_commuting_city

    d = details_for(job)
    title = (job.title or "").strip()
    description = (job.description or "").strip()
    requirements = (job.requirements or "").strip()
    text = f"{title} {description} {requirements}".casefold()
    skills = getattr(job, "skill_requirements", None) or []
    skill_count = len({skill_key(row.get("skill", "")) for row in skills if row.get("skill", "").strip()})
    missions = d.get("missions") or []
    issues = []

    def issue(code, message, step, field, severity="advice", suggestion=None, phrase=None):
        issues.append({"code": code, "message": message, "step": step, "field": field,
                       "severity": severity, "suggestion": suggestion, "phrase": phrase})

    years = [int(value) for value in re.findall(r"(\d{1,2})\s*(?:años|years)", requirements.casefold())]
    required_months = minimum_experience_months(d)
    if required_months is not None:
        years.append(required_months / 12)
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
    critical = any(row["severity"] == "critical" for row in issues)
    def meaningful(value, minimum, words):
        return len(value.strip()) >= minimum and len(set(re.findall(r"\w+", value.casefold()))) >= words
    complete_missions = bool(missions) and all(meaningful(row.get("outcome", ""), 15, 4) and meaningful(row.get("measure", ""), 10, 3) and 1 <= (row.get("days") or 0) <= 365 for row in missions)
    schedule = d.get("schedule", "").strip().casefold()
    schedule_ok = meaningful(schedule, 10, 3) and bool(re.search(r"lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo|d[ií]as|seman|turnos", schedule)) and bool(re.search(r"\d|horario|diurn|nocturn|rotativ", schedule))
    response_days = getattr(job, "response_days", 0) or 0
    process_days = d.get("process_days") or 0
    location_ok = job.modality == "remote" or bool((job.location or "").strip())
    scope = d.get("remote_scope") or {}
    if job.modality == "remote" and scope.get("mode") == "regions":
        location_ok = bool(scope.get("countries") or scope.get("continents"))
    if job.modality in {"onsite", "hybrid"}:
        try:
            department = getattr(job, "department", None)
            location = job.location or ""
            canonical_commuting_city(f"{location}, {department}" if department and "," not in location else location)
        except ValueError:
            location_ok = False
    if process_days and response_days > process_days:
        issue("process_conflict", "El plazo de respuesta por avance supera la duración total estimada del proceso.", 3, "response_days", "critical")
        critical = True
    checks = []

    def check(key, label, weight, passed, step, action_text, required=False, earned=None):
        points = round(weight if passed else 0) if earned is None else round(max(0, min(weight, earned)))
        checks.append({"key": key, "label": label, "weight": weight, "points": points,
                       "remaining_points": weight - points, "passed": bool(passed),
                       "state": "complete" if passed and points == weight else "partial" if points else "missing",
                       "step": step, "action": action_text, "required": required,
                       "priority": "Obligatorio" if required and not passed else "Mejora"})

    description_ok = meaningful(description, 40, 6)
    description_points = 15 if meaningful(description, 100, 10) else 8 if description_ok else 4 if meaningful(description, 15, 3) else 0
    knowledge_ok = meaningful(requirements, 20, 3)
    requirement_points = (4 if knowledge_ok else 0) + (4 if d.get("seniority") else 0) + (4 if required_months is not None else 0)
    mission_points = 0
    if missions:
        parts = [sum((meaningful(row.get("outcome", ""), 15, 4), meaningful(row.get("measure", ""), 10, 3),
                      1 <= (row.get("days") or 0) <= 365)) if row.get("outcome", "").strip() or row.get("measure", "").strip() else 0 for row in missions]
        mission_points = 3 * sum(parts) / len(missions)
    process_points = 3 * int(d.get("interview_count") is not None) + 4 * int(process_days >= 1)
    check("title", "Cargo específico", 5, 5 <= len(title) <= 180 and bool(re.search(r"\w", title)) and not re.search(r"\b(?:urgente|gana dinero)\b", title.casefold()), 0, "Usa un nombre de cargo, sin reclamos publicitarios. Puede ser una palabra, como Analista.", True)
    check("salary", "Salario fijo o rango real", 10, range_ok, 0, "Publica un salario fijo mensual positivo en COP. El rango máximo es opcional.", True)
    check("contract_type", "Contrato definido", 8, d.get("contract_type"), 0, "Selecciona el tipo de contrato, separado de la dedicación.", True)
    check("schedule", "Jornada y horario", 8, schedule_ok, 0, "Opcional: selecciona los días y horas o describe los turnos.", earned=8 if schedule_ok else 3 if meaningful(schedule, 8, 2) else 0)
    check("location", "Modalidad y ubicación", 8, job.modality in {"remote", "hybrid", "onsite"} and location_ok, 0, "Elige una ciudad para presencial o híbrido. En remoto, selecciona países/continentes o permite trabajar desde cualquier lugar.", True)
    check("description", "Responsabilidades y contexto", 15, description_ok, 1, "Describe las funciones y su contexto. El texto ya aporta puntos aunque no añadas misiones; amplíalo con entregables y equipo para completar este criterio.", True, earned=description_points)
    check("missions", "Resultados esperados y evaluación", 9, complete_missions, 1, "Opcional: añade un resultado, su evaluación y plazo. Cada dato aporta; no necesitas misiones para puntuar las responsabilidades.", earned=mission_points)
    check("requirements", "Conocimientos, nivel y experiencia", 12, knowledge_ok and d.get("seniority") and required_months is not None, 2, "Indica conocimientos, nivel y experiencia mínima en meses o años (se acepta 0). Cada uno aporta 4 puntos.", True, earned=requirement_points)
    check("skill_requirements", "Habilidades priorizadas", 8, 3 <= skill_count <= 50, 2, "Añade al menos tres habilidades distintas. Puedes marcar todas como deseables si se aprenden en el cargo.", True, earned=min(8, skill_count * 8 / 3))
    check("process", "Entrevistas y duración estimada", 7, d.get("interview_count") is not None and process_days >= 1 and bool(getattr(job, "pipeline_stages", None)), 3, "Opcional: entrevistas aportan 3 puntos y duración estimada 4 puntos.", earned=process_points)
    check("response_days", "Compromiso de respuesta", 4, 1 <= response_days <= 30 and (not process_days or response_days <= process_days), 3, "Acuerda un plazo de respuesta entre 1 y 30 días; si defines una duración total, debe caber en ella.", True)
    check("inclusive", "Lenguaje y requisitos coherentes", 6, not critical and not any(row["code"].startswith("wording_") for row in issues), 2, "Retira frases genéricas y resuelve las contradicciones señaladas.")
    score = sum(row["points"] for row in checks)
    blockers = [row for row in checks if row["required"] and not row["passed"]]
    minimum_score = 60
    can_publish = not blockers and not critical and score >= minimum_score
    reference = local_reference(job, peers)
    if salary and reference["median"] and salary < reference["median"] * .65:
        issue("salary_below_local_reference", "El mínimo fijo está por debajo del 65% de la referencia local. Revisa las condiciones comparadas antes de cambiarlo.", 0, "salary")
    pending = sorted((row for row in checks if not row["passed"] or row["points"] < row["weight"]), key=lambda row: (not (row["required"] and not row["passed"]), -row["remaining_points"]))
    return {"version": 1, "completeness": score, "score": score, "level": "A" if can_publish and score >= 90 and not any(row["code"].startswith("wording_") for row in issues) else "B" if can_publish else "Pendiente",
            "rating": offer_rating(score), "rating_scale": RATING_SCALE,
            "checks": checks, "issues": issues, "next_actions": pending, "blockers": blockers, "can_publish": can_publish, "minimum_publish_score": minimum_score,
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
