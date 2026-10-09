import re
from statistics import median


def assess_quality(job, comparable_jobs):
    text = f"{job.title} {job.requirements}"
    lowered = text.lower()
    issues = []
    if not job.salary or job.salary <= 0:
        issues.append({"code": "salary_missing", "message": "Publica un salario para que las personas puedan decidir con información."})
    if len(getattr(job, "skill_requirements", []) or job.skills or []) > 10:
        issues.append({"code": "many_requirements", "message": "Separa las habilidades esenciales de las que pueden aprenderse; hay más de diez requisitos."})
    years = [int(value) for value in re.findall(r"(\d{1,2})\s*(?:años|years)", lowered)]
    if any(term in lowered for term in ["junior", "entry level", "sin experiencia"]) and any(value >= 5 for value in years):
        issues.append({"code": "level_conflict", "message": "El nivel inicial contradice la experiencia de cinco años o más. Revisa el alcance del cargo."})
    if re.search(r"(?:edad\s*(?:entre|máxima|minima|mínima)|solo\s+(?:hombres|mujeres)|buena\s+presencia)", lowered):
        issues.append({"code": "personal_restrictions", "message": "Revisa restricciones personales que no describen una habilidad necesaria para el trabajo."})
    tokens = set(re.findall(r"\w+", job.title.lower())) - {"senior", "junior", "developer", "desarrollador", "de", "a", "sr", "jr"}
    peers = [row.salary for row in comparable_jobs if row.id != job.id and row.salary and row.sector == job.sector and row.modality == job.modality and tokens & set(re.findall(r"\w+", row.title.lower()))]
    salary_reference = {"source": "local_active_vacancies", "sample_size": len(peers), "currency": "COP", "median": round(median(peers), 2) if len(peers) >= 5 else None,
                        "notice": "Muestra de esta base local; no representa el mercado laboral ni usa datos salariales en tiempo real."}
    if job.salary and len(peers) >= 5 and job.salary < median(peers) * .65:
        issues.append({"code": "salary_below_local_reference", "message": "El salario queda por debajo del 65% de la mediana de ofertas comparables de esta base. Revisa experiencia, jornada y alcance antes de modificarlo."})
    requirements = getattr(job, "skill_requirements", []) or []
    description = (job.description or "").strip().lower()
    requirement_text = (job.requirements or "").strip().lower()
    action = bool(re.search(r"\b(?:desarroll|constru|registr|analiz|revis|gestion|coordin|atend|prepar|diseñ|implement|manten|verific|concil|organiz|control|document|program|supervis|apoy|resolv|oper|realiz|crea)\w*", description))
    context = bool(re.search(r"\b(?:equipo|resultado|entrega|cliente|reporte|informe|proyecto|proceso|venta|soporte|servicio|producto|registro|sistema)\w*", description))
    explains_experience = bool(re.search(r"\b(?:experiencia|formaci[oó]n|conocimiento|fundamento|t[eé]cnic|tecn[oó]log|profesional|demostr|ejemplo|año|aprend|junior|senior|manejo|habilidad)\w*", requirement_text))
    weights = {"title": 10, "description": 20, "requirements": 15, "salary": 20, "location": 10, "skill_requirements": 10, "response_days": 5, "inclusive": 10}
    checks = [
        {"key": "title", "label": "Cargo concreto", "passed": 5 <= len(job.title.strip()) <= 100 and len(set(re.findall(r"\w+", job.title.lower()))) >= 2 and not re.search(r"\b(?:urgente|gana dinero|oportunidad [uú]nica)\b", job.title.lower()), "action": "Usa un nombre de cargo específico, sin listas de funciones."},
        {"key": "description", "label": "Responsabilidades claras", "passed": len(description) >= 100 and action and context, "action": "Explica qué hará la persona y para qué: acciones concretas, entregables, clientes o equipo. Ejemplo: revisará facturas y conciliará diferencias para preparar el cierre mensual."},
        {"key": "requirements", "label": "Requisitos explicados", "passed": len(requirement_text) >= 60 and explains_experience, "action": "Explica conocimientos y experiencia demostrables, distinguiendo requisitos de lo que puede aprenderse. Ejemplo: fundamentos de SQL; se aceptan proyectos de formación como evidencia."},
        {"key": "salary", "label": "Salario informado", "passed": bool(job.salary and job.salary > 0), "action": "Indica un salario mensual positivo en COP y aclara sus condiciones."},
        {"key": "location", "label": "Lugar y modalidad", "passed": job.modality in {"remote", "hybrid", "onsite"} and (job.modality == "remote" or bool(job.location)), "action": "Indica modalidad y ciudad cuando se requiere asistencia presencial."},
        {"key": "skill_requirements", "label": "Habilidades priorizadas", "passed": bool(requirements) and any(row.get("essential") for row in requirements) and len(requirements) <= 10 and all(1 <= row.get("weight", 0) <= 5 for row in requirements), "action": "Define hasta diez habilidades y marca cuáles son esenciales. Ajusta su peso de 1 a 5."},
        {"key": "response_days", "label": "Compromiso de respuesta", "passed": 1 <= (getattr(job, "response_days", 0) or 0) <= 14, "action": "Acuerda un plazo de respuesta de hasta catorce días por avance del proceso."},
        {"key": "inclusive", "label": "Requisitos coherentes e inclusivos", "passed": not any(row["code"] in {"level_conflict", "personal_restrictions"} for row in issues), "action": "Retira restricciones personales y alinea experiencia con el nivel del cargo."},
    ]
    for check in checks:
        check["weight"] = weights[check["key"]]
        check["priority"] = "Alta" if check["weight"] >= 15 or check["key"] == "inclusive" else "Media"
    completeness = sum(row["weight"] for row in checks if row["passed"])
    pending = sorted((row for row in checks if not row["passed"]), key=lambda row: (-row["weight"], row["key"]))
    return {"issues": issues, "checks": checks, "completeness": completeness,
            "next_actions": pending, "readiness": "Revisión completa" if not pending else "Información clave pendiente" if any(row["priority"] == "Alta" for row in pending) else "Detalles por mejorar",
            "salary_reference": salary_reference, "blind_hiring": job.blind_hiring,
            "notice": "Orientación basada en reglas y datos locales; requiere revisión humana."}
