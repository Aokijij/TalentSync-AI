import hashlib
import json

from app.domain.services.skills import skill_gap

MATCH_VERSION = "transparent-match-v3"


def requirements_for(job):
    return getattr(job, "skill_requirements", None) or [{"skill": skill, "essential": False, "weight": 1} for skill in job.skills or []]


def weighted_coverage(profile, job):
    rows = skill_gap(profile.skills, requirements_for(job))
    total = sum(row["weight"] for row in rows)
    return round(sum(row["weight"] for row in rows if row["covered"]) / total * 100, 2) if total else 0


def input_version(profile, job, text_method="lexical-hashing-v1"):
    payload = [MATCH_VERSION, text_method, profile.skills, profile.embedding, getattr(profile, "preferences", {}),
               profile.profession, profile.experience, profile.education, getattr(profile, "experiences", []),
               getattr(profile, "educations", []), getattr(profile, "certifications", []), getattr(profile, "languages", []),
               getattr(profile, "evidence", []), job.skills, job.embedding, job.title, job.description, job.requirements,
               getattr(job, "skill_requirements", []), getattr(job, "languages", []), getattr(job, "required_study_fields", []),
               getattr(job, "required_education_level", None), job.salary, job.modality, job.location, job.sector]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def preference_alignment(profile, job):
    prefs = getattr(profile, "preferences", None) or {}
    checks = []
    if prefs.get("minimum_salary") is not None:
        checks.append({"label": "Salario mínimo", "matches": None if job.salary is None else job.salary >= prefs["minimum_salary"], "required": prefs.get("salary_required", False)})
    if prefs.get("modalities"):
        checks.append({"label": "Modalidad", "matches": job.modality in prefs["modalities"], "required": prefs.get("modality_required", False)})
    if prefs.get("locations") and job.modality != "remote":
        locations = {str(value).strip().casefold() for value in prefs["locations"]}
        checks.append({"label": "Ubicación", "matches": None if not job.location else job.location.strip().casefold() in locations, "required": prefs.get("location_required", False)})
    known = [row for row in checks if row["matches"] is not None]
    score = round(sum(row["matches"] for row in known) / len(known) * 100, 2) if known else None
    return {"score": score, "checks": checks, "unmet_conditions": [row["label"] for row in checks if row["required"] and row["matches"] is False], "unknown_conditions": [row["label"] for row in checks if row["matches"] is None]}


def explain(profile, job, *, context, skills, language, education, certifications, confidence, percentage, text_method="lexical-hashing-v1"):
    if education is None and certifications is None:
        components = [{"key": "skills", "label": "Habilidades", "score": skills, "weight": .6},
                      {"key": "context", "label": "Contexto profesional", "score": context, "weight": .3 if language is not None else .4}]
    else:
        factor = .9 if language is not None else 1
        components = [{"key": key, "label": label, "score": score, "weight": weight * factor}
                      for key, label, score, weight in [("skills", "Habilidades", skills, .45), ("context", "Contexto profesional", context, .25),
                          ("education", "Formación", education if education is not None else context, .20),
                          ("certifications", "Certificaciones", certifications if certifications is not None else skills, .10)]]
    if language is not None:
        components.append({"key": "languages", "label": "Idiomas", "score": language, "weight": .1})
    rows = skill_gap(profile.skills, requirements_for(job))
    evidence = getattr(profile, "evidence", None) or []
    for row in rows:
        row["evidence"] = [{"title": item["title"], "kind": item["kind"], "verified": False} for item in evidence if row["key"] in item.get("skills", [])]
    preferences = preference_alignment(profile, job)
    factor = .75 + confidence / 400 if getattr(job, "source_kind", "internal") == "external" else 1
    for component in components:
        component["points"] = round(component["score"] * component["weight"] * factor, 3)
    return {"version": MATCH_VERSION, "input_version": input_version(profile, job, text_method), "score_type": "compatibility_index",
            "notice": "Índice de afinidad con los datos registrados; no es una probabilidad de contratación.",
            "text_method": text_method, "components": components, "requirements": rows,
            "unmet_essential_skills": [row["skill"] for row in rows if row.get("essential") and not row["covered"]],
            "preferences": preferences, "candidate_interest_score": preferences["score"], "overall_score": percentage,
            "data_confidence": confidence, "ontology_version": "foundations-v1"}
