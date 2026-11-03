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
    academic = details.get("education_requirement")
    if academic is None:
        from app.domain.services.academic_matching import education_evaluation
        academic = education_evaluation(profile, job)
    education_lines = [academic["reason"]]
    for row in academic.get("comparisons", [])[:8]:
        level_labels = {"meets": "cumple el nivel", "below": "nivel inferior al solicitado", "unknown": "nivel por confirmar", "in_progress": "estudios en curso; se solicita formación terminada", "not_required": "sin nivel mínimo"}
        education_lines.append(f"{row['candidate_degree']} → {row['requested_field'] or 'nivel académico'}: {row['reason']} Nivel: {level_labels[row['level_status']]}.")
    if academic["status"] == "review":
        education_lines.append("Formación pendiente de revisión; un nombre desconocido no se trata como incompatibilidad confirmada.")
    requested = language_levels(getattr(job, "languages", None))
    available = language_levels(getattr(profile, "languages", None))
    language_lines = ["Se promedia el cumplimiento del nivel mínimo de cada idioma. Alcanzar o superar el mínimo da cumplimiento completo; no registrar un nivel aporta cero para ese idioma."]
    language_lines += [f"{name.capitalize()}: solicitado {level} · registrado {available.get(name, 'sin indicar')}." for name, level in requested.items()]
    return {"skills": skill_lines, "context": context_lines, "education": education_lines,
            "languages": language_lines, "certifications": ["Se comparan las certificaciones solicitadas con las registradas en el perfil. Su presencia declarada no sustituye una verificación de la empresa."]}
