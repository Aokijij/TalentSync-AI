"""Explainable course ordering from declared skills and work context; no profile mutation."""

import re

from app.domain.services.skills import skill_key, skill_set

STOP = set(
    "de del la el los las en y o a con para un una por al que se como tu sus su curso cursos formacion trabajo profesional introduccion fundamentos basico basica aprender informacion herramientas desarrollo".split()
)
PROJECT = r"analista de proyectos|gestion de proyectos|gerencia de proyectos|plan(?:eacion|ificacion)\w*.*proyectos?|cronograma|presupuest\w*|control de riesgos|seguimiento.*proyecto"
PROJECT_SKILLS = {
    "gestion de proyectos",
    "planificacion",
    "agile",
    "scrum",
    "kanban",
    "gestion de riesgos",
    "presupuestos",
    "indicadores de gestion",
}


def profile_context(profile):
    values = [
        getattr(profile, key, "") or ""
        for key in ("profession", "preferred_sector", "experience", "education")
    ]
    for record in getattr(profile, "experiences", None) or []:
        values.extend(str(record.get(key) or "") for key in ("role", "description"))
    values.extend(
        str(record.get("degree") or "")
        for record in getattr(profile, "educations", None) or []
    )
    for record in getattr(profile, "evidence", None) or []:
        values.extend(str(record.get(key) or "") for key in ("title", "description"))
    values.append(str(getattr(profile, "cv_text", "") or "")[:20000])
    return skill_key(" ".join(values))


def context_areas(profile, areas):
    text = profile_context(profile)
    found = set()
    if re.search(PROJECT, text):
        found.add("administration")
    for area, row in areas.items():
        # A generic reference to data in a project does not imply a software career.
        terms = [term for term in row["terms"] if term not in {"datos", "comunicacion"}]
        if any(re.search(r"\b" + re.escape(term) + r"\w*\b", text) for term in terms):
            found.add(area)
    return found


def ranked_resources(resources, profile, recommended_areas):
    context = profile_context(profile)
    known = skill_set(getattr(profile, "skills", None) or [])
    tokens = set(re.findall(r"[a-z]{4,}", context)) - STOP
    project = bool(re.search(PROJECT, context))
    rows = []
    for resource in resources:
        skills = skill_set(resource.get("skills", []))
        overlap = sorted(known & skills)
        mentioned = sorted(
            skill
            for skill in skills - known
            if re.search(r"(?<!\w)" + re.escape(skill) + r"(?!\w)", context)
        )
        project_fit = project and bool(skills & PROJECT_SKILLS)
        content = skill_key(
            " ".join(
                [
                    resource["title"],
                    *resource.get("skills", []),
                    *((resource.get("details") or {}).get("syllabus", [])),
                ]
            )
        )
        shared = sorted(tokens & (set(re.findall(r"[a-z]{4,}", content)) - STOP))
        category_fit = (
            resource.get("category") in recommended_areas
            and resource.get("category") != "general"
        )
        score = (
            min(90, 30 * len(overlap))
            + min(50, 20 * len(mentioned))
            + (45 if project_fit else 0)
            + min(20, 4 * len(shared))
            + (8 if category_fit else 0)
        )
        reasons = []
        if overlap:
            reasons.append(
                "Coincide con tus habilidades: " + ", ".join(overlap[:3]) + "."
            )
        if project_fit:
            reasons.append(
                "Relacionado con la planificación y el seguimiento de proyectos de tu experiencia."
            )
        elif mentioned:
            reasons.append(
                "Se relaciona con conocimientos mencionados en tu experiencia o CV: "
                + ", ".join(mentioned[:3])
                + "."
            )
        elif len(shared) >= 2:
            reasons.append(
                "Comparte temas con tu trayectoria: " + ", ".join(shared[:3]) + "."
            )
        if not reasons and category_fit:
            reasons.append("Formación del área profesional identificada en tu perfil.")
        if not reasons:
            reasons.append(
                "Formación complementaria para explorar; no hay una coincidencia específica confirmada."
            )
        rows.append(
            {
                **resource,
                "relevance": {
                    "score": score,
                    "reasons": reasons,
                    "kind": "skills"
                    if overlap
                    else "context"
                    if project_fit or mentioned or len(shared) >= 2
                    else "area"
                    if category_fit
                    else "complementary",
                },
            }
        )
    return sorted(
        rows, key=lambda row: (-row["relevance"]["score"], row["title"].casefold())
    )
