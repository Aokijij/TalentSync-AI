import re
from statistics import median


def assess_quality(job, comparable_jobs):
    text = f"{job.title} {job.requirements}"
    lowered = text.lower()
    issues = []
    if job.salary is None:
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
    return {"issues": issues, "salary_reference": salary_reference, "blind_hiring": job.blind_hiring,
            "notice": "Orientación basada en reglas y datos locales; requiere revisión humana."}
