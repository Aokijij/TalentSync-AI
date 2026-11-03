"""Preparation from saved facts, without an external model or invented answers."""
import json
import re
from copy import deepcopy

from app.domain.services.career_coach import fingerprint, snapshot
from app.domain.services.personal_details import shared_personal_details
from app.domain.services.skill_context import fold
from app.domain.services.skills import skill_key


def resume_profile(profile):
    values = snapshot(profile)
    for key in ("links", "evidence", "resume_style", "resume_color", "photo_filename"):
        values[key] = getattr(profile, key, None)
    visibility = getattr(profile, "personal_visibility", None) or {}
    values.update(shared_personal_details(profile))
    values["personal_visibility"] = visibility
    values["preferences"] = {key: deepcopy((getattr(profile, "preferences", None) or {}).get(key, {})) for key in ("skill_levels", "mobility", "resume_export_options")}
    return json.loads(json.dumps(values, default=str))


def resume_options(profile):
    saved = (profile.get("preferences") or {}).get("resume_export_options") or {}
    defaults = ["contact", "summary", "experiences", "educations", "certifications", "driving_licenses", "professional_cards", "skills", "languages", "preferences", "evidence"]
    sections = list(saved.get("sections", defaults))
    if saved.get("version") != 2 and "certifications" in sections:
        sections = list(dict.fromkeys([*sections, "driving_licenses", "professional_cards"]))
    return {"sections": sections, "include_photo": saved.get("include_photo", True)}


def source_version(user):
    return fingerprint({"name": user.name, "email": user.email, "profile": resume_profile(user.profile)})


def job_snapshot(job):
    return {"id": job.id, "title": job.title, "company_name": job.company_name,
            **{key: deepcopy(getattr(job, key, None)) for key in ("description", "requirements", "skills", "skill_requirements", "location", "modality", "required_education_level", "required_study_fields", "languages")}}


def suggested_skills(profile, job):
    requested = {skill_key(skill) for skill in job.get("skills") or []}
    return sorted(profile.get("skills") or [], key=lambda skill: skill_key(skill) not in requested)


def interview_questions(profile, job, *, saved_question_ids=()):
    experiences = profile.get("experiences") or []
    requirements = sorted(job.get("skill_requirements") or [], key=lambda row: (not row.get("essential"), -int(row.get("weight") or 1)))
    all_skills = list({skill_key(skill): skill for skill in [*(row["skill"] for row in requirements), *(job.get("skills") or [])]}.values())
    # Prioritization must not hide an already answered skill still in this offer.
    skills = all_skills[:4] + [skill for skill in all_skills[4:] if "skill-" + fingerprint(skill_key(skill))[:16] in saved_question_ids]
    required = {skill_key(row["skill"]): row for row in requirements}
    # Quote bounded excerpts from the vacancy rather than inventing a scenario.
    def excerpts(text):
        clean = re.sub(r"<[^>]+>", " ", str(text or ""))
        return [re.sub(r"\s+", " ", line).strip(" •-*\t")[:320] for line in re.split(r"[\n\r]+|(?<=[.!?])\s+", clean) if len(line.strip()) >= 18][:16]
    responsibilities = excerpts(job.get("description"))
    requested = excerpts(job.get("requirements"))
    context = (responsibilities or requested or [""])[0]
    short_context = context if len(context) <= 120 else context[:120].rsplit(" ", 1)[0] + "…"
    questions = [
        {"id": "introduction", "category": "Trayectoria y cargo", "title": f"¿Qué experiencia concreta te prepara para {job['title']}?", "hint": "Relaciona tu participación con una responsabilidad de esta oferta. Puedes utilizar un trabajo, práctica o proyecto.", "context": context,
         "follow_ups": ["¿Qué parte del trabajo hiciste tú?", "¿Qué resultado o entrega puedes mostrar?"]},
        {"id": "problem", "category": "Resolución de problemas", "title": f"La oferta incluye «{short_context}». ¿Qué dificultad anticiparías y cómo la resolverías?" if short_context else f"¿Cómo abordarías una dificultad al trabajar en {job['title']}?", "context": context,
         "hint": "Parte de una dificultad real relacionada con esta responsabilidad. Si no la has afrontado, distingue tu propuesta de la experiencia que ya tienes.",
         "follow_ups": ["¿Qué comprobarías antes de actuar?", "¿Cómo detectarías un error y verificarías la solución?"]},
    ]
    own = {skill_key(skill) for skill in profile.get("skills") or []}
    for skill in skills:
        key = skill_key(skill)
        related = next((text for text in [*requested, *responsibilities] if fold(skill) in fold(text) or key in fold(text)), "")
        level = {"basic": "básico", "intermediate": "intermedio", "advanced": "avanzado", "expert": "experto"}.get(required.get(key, {}).get("level"))
        probe = {
            "sql": "¿Cómo comprobarías que la consulta no duplica filas ni omite registros relevantes?",
            "python": "¿Cómo manejarías datos inesperados y comprobarías el comportamiento con pruebas?",
            "react": "¿Cómo organizarías el estado y comprobarías la interacción de la persona usuaria?",
            "javascript": "¿Cómo manejarías una operación asíncrona que falla o tarda demasiado?",
            "excel": "¿Cómo detectarías datos incompletos y verificarías las fórmulas del reporte?",
            "api rest": "¿Cómo validarías los datos y manejarías errores o reintentos de una solicitud?",
            "gestion de inventarios": "¿Cómo detectarías una diferencia entre el registro y las existencias reales?",
            "servicio al cliente": "¿Cómo aclararías la necesidad y comprobarías que la solución fue útil?",
        }.get(key, f"¿Por qué elegirías ese uso de {skill} frente a otra alternativa?")
        questions.append({"id": "skill-" + fingerprint(skill_key(skill))[:16], "skill": skill,
            "category": "Habilidad esencial" if required.get(key, {}).get("essential") else "Aplicación de una habilidad",
            "title": f"{skill}: {probe}" if key in {"sql", "python", "react", "javascript", "excel", "api rest", "gestion de inventarios", "servicio al cliente"} else f"Para {job['title']}, ¿cómo aplicarías {skill} a las tareas de esta oferta?",
            "context": related or context, "required_level": level,
            "hint": "Describe un ejemplo real, tu decisión técnica o de trabajo y cómo verificaste el resultado. Si aún no utilizas esta habilidad, explica qué necesitas aprender.",
            "follow_ups": [probe, "¿Qué evidencia permitiría comprobar tu participación y el resultado?"],
            "in_profile": key in own})
    questions.append({"id": "collaboration", "category": "Trabajo con otras personas", "title": f"¿Cómo coordinarías una entrega del cargo {job['title']} con otras personas?", "context": (responsibilities[1:] or [context])[0], "hint": "Utiliza una experiencia real de coordinación. Explica cómo acordaron responsabilidades y resolvieron diferencias.", "follow_ups": ["¿Cómo comunicarías un bloqueo?", "¿Cómo acordarían que la entrega quedó completa?"]})
    for question in questions:
        skill = question.get("skill")
        matches = [row for row in experiences if not skill or fold(skill) in fold(str(row.get("description") or ""))]
        question["experiences"] = [{key: row.get(key) for key in ("role", "company", "description")} for row in matches[:2]]
    return questions


def preparation_revision(profile, job):
    # Private personal details do not influence questions or preparation.
    return fingerprint({"question_version": 2, "job": job, "profile": {key: profile.get(key) for key in ("profession", "skills", "experience", "experiences", "educations")}})


def answer_review(answer):
    labels = {"situation": "contexto", "task": "responsabilidad", "action": "acción", "result": "resultado"}
    missing = [label for key, label in labels.items() if not str(answer.get(key) or "").strip()]
    return {"complete": not missing, "missing": missing}
