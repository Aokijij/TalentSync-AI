"""Readable explanations from already calculated components; no inference or identity data."""
from app.domain.services.languages import language_levels


def component_reasons(details, profile, job):
    rows = details.get("requirements", [])
    fulfilled = sum(bool(row.get("covered")) for row in rows)
    skill_lines = [f"{fulfilled} de {len(rows)} habilidades cumplidas. El porcentaje es el promedio ponderado de su cumplimiento, según el peso de cada requisito."]
    skill_lines += [f"{row['skill']}: {row.get('score', 0):g}% de cumplimiento · peso {row.get('weight', 1)}. {row.get('reason', '').replace('tu perfil', 'el perfil')}" for row in rows[:4]]
    context_lines = ["Se comparan profesión, cargos, funciones y conocimientos del perfil con el trabajo solicitado."]
    context_lines += [f"{row['label']}: {row['score']:.0f}% de coincidencia." for row in details.get("section_scores", []) if row.get("has_candidate_data") and isinstance(row.get("score"), (float, int))][:4]
    experience = details.get("experience_requirement", {})
    if experience.get("required_months") is not None:
        context_lines.append(f"Experiencia relacionada: {experience.get('related_months', 0)} meses registrados frente a {experience['required_months']} solicitados. Esta comparación forma parte del contexto; no suma puntos por separado.")
    fields = getattr(job, "required_study_fields", None) or []
    secondary = getattr(job, "required_education_level", None) == "secondary"
    if secondary:
        fields = []
    education_lines = ["Se comparan las áreas de estudio aceptadas (70% del componente) y el nivel académico solicitado (30%). Los estudios en curso no acreditan un título terminado."]
    if not secondary and (getattr(job, "quality_details", None) or {}).get("education_accepts_in_progress"):
        education_lines = ["Se comparan las áreas aceptadas (70% del componente) y el nivel académico (30%). Esta vacante acepta estudios en curso del nivel y área solicitados; no exige que estén terminados."]
    if secondary:
        education_lines = ["Se compara el nivel de bachillerato terminado. No se exige una carrera específica; los estudios en curso no acreditan este requisito."]
    if fields:
        education_lines.append("Áreas aceptadas: " + ", ".join(fields[:5]) + ". Se acepta cualquiera de las alternativas, no se exigen todas.")
    requested = language_levels(getattr(job, "languages", None))
    available = language_levels(getattr(profile, "languages", None))
    language_lines = ["Se promedia el cumplimiento del nivel mínimo de cada idioma. Alcanzar o superar el mínimo da cumplimiento completo; no registrar un nivel aporta cero para ese idioma."]
    language_lines += [f"{name.capitalize()}: solicitado {level} · registrado {available.get(name, 'sin indicar')}." for name, level in requested.items()]
    return {"skills": skill_lines, "context": context_lines, "education": education_lines,
            "languages": language_lines, "certifications": ["Se comparan las certificaciones solicitadas con las registradas en el perfil. Su presencia declarada no sustituye una verificación de la empresa."]}
