import hashlib
import json
from datetime import date

from app.domain.services.requirement_analysis import (
    relevant_experience,
    requirement_rows,
    requirement_score,
)
from app.domain.services.requirement_analysis import (
    requirements_for as requirements_for,
)
from app.domain.services.work_preferences import effective_preferences, location_fit

MATCH_VERSION = "contextual-match-v11"


def weighted_coverage(profile, job):
    return requirement_score(requirement_rows(profile, job))


def input_version(profile, job, text_method="lexical-hashing-v1"):
    payload = [MATCH_VERSION, text_method, profile.skills, profile.embedding, getattr(profile, "preferred_sector", None),
               profile.profession, profile.experience, profile.education, getattr(profile, "experiences", []),
               getattr(profile, "educations", []), getattr(profile, "certifications", []), getattr(profile, "languages", []),
               getattr(profile, "evidence", []), (getattr(profile, "preferences", None) or {}).get("skill_levels", getattr(profile, "skill_levels", {})), job.skills, job.embedding, job.title, job.description, job.requirements,
               getattr(job, "skill_requirements", []), getattr(job, "languages", []), getattr(job, "required_study_fields", []),
               getattr(job, "required_education_level", None), getattr(job, "source_kind", "internal"), job.sector,
               (getattr(job, "quality_details", None) or {}).get("experience_years"),
               (getattr(profile, "preferences", None) or {}).get("cv_skill_context", []), (getattr(profile, "preferences", None) or {}).get("writing_contexts", []), date.today().strftime("%Y-%m")]
    details = getattr(job, "quality_details", None) or {}
    if details.get("experience_months") is not None:
        payload.append({"experience_months": details["experience_months"]})
    if details.get("education_accepts_in_progress"):
        payload.append({"education_accepts_in_progress": True})
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def preference_alignment(profile, job):
    prefs = effective_preferences(profile)
    checks = []
    if prefs.get("minimum_salary") is not None:
        checks.append({"label": "Salario mínimo", "matches": None if job.salary is None else job.salary >= prefs["minimum_salary"], "required": prefs.get("salary_required", False)})
    if prefs.get("modalities"):
        checks.append({"label": "Modalidad", "matches": job.modality in prefs["modalities"], "required": prefs.get("modality_required", False)})
    if prefs.get("locations") and job.modality != "remote":
        fit = location_fit(profile, job)
        checks.append({"label": "Ubicación", "matches": True if fit["status"] in {"local", "relocation"} else False if fit["status"] == "conflict" or job.location and not prefs.get("mobility") else None, "required": prefs.get("location_required", False)})
    known = [row for row in checks if row["matches"] is not None]
    score = round(sum(row["matches"] for row in known) / len(known) * 100, 2) if known else None
    return {"score": score, "checks": checks, "unmet_conditions": [row["label"] for row in checks if row["required"] and row["matches"] is False], "unknown_conditions": [row["label"] for row in checks if row["matches"] is None]}


def explain(profile, job, *, context, skills, language, education, certifications, confidence, percentage, text_method="lexical-hashing-v1", section_scores=None, experience_details=None, requirement_details=None, retained_writing_context=False):
    if education is None and certifications is None:
        components = [{"key": "skills", "label": "Habilidades", "score": skills, "weight": .6},
                      {"key": "context", "label": "Contexto profesional", "score": context, "weight": .3 if language is not None else .4}]
    else:
        factor = .9 if language is not None else 1
        components = [{"key": key, "label": label, "score": score, "weight": weight * factor}
                      for key, label, score, weight in [("skills", "Habilidades", skills, .45), ("context", "Contexto profesional", context, .25),
                          ("education", "Formación", education if education is not None else context, .20),
                          ("certifications", "Certificaciones", certifications if certifications is not None else skills, .10)]]
        if certifications is None:
            components[0]["weight"] += components.pop()["weight"]
        if education is None:
            components[1]["weight"] += components[2]["weight"]
            components.pop(2)
    if language is not None:
        components.append({"key": "languages", "label": "Idiomas", "score": language, "weight": .1})
    rows = requirement_details if requirement_details is not None else requirement_rows(profile, job)
    preferences = preference_alignment(profile, job)
    factor = .75 + confidence / 400 if getattr(job, "source_kind", "internal") == "external" else 1
    for component in components:
        component["points"] = round(component["score"] * component["weight"] * factor, 3)
    return {"version": MATCH_VERSION, "input_version": input_version(profile, job, text_method), "score_type": "compatibility_index",
            "notice": "Índice de afinidad con los datos registrados; no es una probabilidad de contratación.",
            "text_method": text_method, "components": components, "requirements": rows, "section_scores": section_scores or [], "retained_writing_context": retained_writing_context,
            "experience_requirement": experience_details or relevant_experience(profile, job),
            "context_notice": "Se comparan cargos, funciones y conocimientos por separado. Cuando se pide experiencia mínima, los meses relacionados aportan el 20% de la señal de contexto; no son una señal adicional al total.",
            "unmet_essential_skills": [row["skill"] for row in rows if row.get("essential") and not row["covered"]],
            "preferences": preferences, "candidate_interest_score": preferences["score"], "overall_score": percentage,
            "data_confidence": confidence, "ontology_version": "foundations-v1", "requirement_method": "explicit-context-v1"}
