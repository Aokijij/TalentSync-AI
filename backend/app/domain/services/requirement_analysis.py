"""Per-requirement support and conservative duration of related employment."""
import re
from datetime import date

from app.domain.services.experience_dates import experience_months, month_index
from app.domain.services.skill_context import fold, skill_mentions
from app.domain.services.skills import skill_gap, skill_key, skill_set

STATUS_LABELS = {"fulfilled": "Cumplido con datos declarados", "partial": "Cumplimiento parcial", "unknown": "Sin información suficiente", "not_met": "No cumple según lo registrado"}


def requirements_for(job):
    return getattr(job, "skill_requirements", None) or [{"skill": skill, "essential": False, "weight": 1} for skill in job.skills or []]


def requirement_rows(profile, job):
    rows = skill_gap(profile.skills, requirements_for(job))
    experiences = getattr(profile, "experiences", None) or []
    evidence = getattr(profile, "evidence", None) or []
    imported = (getattr(profile, "preferences", None) or {}).get("cv_skill_context", [])
    for row in rows:
        key = row["key"]
        work, signals = [], []
        for index, entry in enumerate(experiences):
            mentions = skill_mentions(f"{entry.get('role', '')}; {entry.get('description', '')}", [key])
            signals.extend(mentions)
            if any(item["state"] in {"applied", "declared"} for item in mentions):
                work.append(index)
        summary = skill_mentions(getattr(profile, "experience", ""), [key]) if not experiences else []
        signals.extend(summary)
        # Import context is useful for undeclared suggestions, but cannot
        # override the candidate's later explicit profile edits.
        if not row["covered"]:
            signals.extend(item for item in imported if skill_key(item.get("skill", "")) == key and item.get("state") in {"learning", "negated", "project"})
        supplied = [item for item in evidence if key in skill_set(item.get("skills", []))]
        contextual_evidence = [item for item in supplied if any(mention["state"] in {"applied", "declared"} for mention in skill_mentions(item.get("description", ""), [key]))]
        positive = bool(work) or any(item["state"] == "applied" for item in signals)
        negative = any(item["state"] == "negated" for item in signals)
        learning = any(item["state"] == "learning" for item in signals)
        project = any(item["state"] == "project" for item in signals)
        if positive or row["covered"] and not (negative or learning):
            status, score = "fulfilled", 100
            reason = "La habilidad aparece en funciones laborales registradas." if positive else "La habilidad está declarada en tu perfil."
        elif row["covered"] or learning or project or contextual_evidence or row["foundations"]:
            status, score = "partial", 50 if row["covered"] else 70 if contextual_evidence or project else 35 if learning else 0
            reason = "Hay información contradictoria; revisa la habilidad y su contexto." if negative else "La habilidad aparece en aprendizaje; no se presupone dominio profesional." if learning else "La habilidad aparece en un proyecto del CV; no acredita duración laboral." if project else "La descripción de una evidencia aportada menciona el uso de esta habilidad; no acredita duración laboral." if contextual_evidence else "Tienes una base relacionada; no suma cumplimiento de esta habilidad."
        elif negative:
            status, score, reason = "not_met", 0, "La información registrada indica falta de experiencia o conocimiento en esta habilidad."
        else:
            status, score, reason = "unknown", 0, "No hay información suficiente para determinar el cumplimiento."
        related = [experiences[index] for index in work]
        row.update(status=status, status_label=STATUS_LABELS[status], score=score, covered=status == "fulfilled", reason=reason,
                   related_months=experience_months(related), months_estimated=any(month_index(item.get("start_date")) is None for item in related),
                   supporting_experiences=len(work), evidence=[{"title": item["title"], "kind": item["kind"], "verified": False} for item in supplied])
    return rows


def requirement_score(rows):
    total = sum(row["weight"] for row in rows)
    return round(sum(row["weight"] * row["score"] for row in rows) / total, 2) if total else 0


ROLE_FAMILIES = {
    "software": ("desarroll", "programad", "software", "backend", "back-end", "frontend", "front-end"),
    "data": ("analista de datos", "analitica", "data analyst", "data engineer", "ingenieria de datos", "cientifico de datos"),
    "service": ("servicio al cliente", "atencion al cliente", "customer service", "contact center"),
    "sales": ("vendedor", "ventas", "comercial", "sales"),
    "finance": ("contab", "contad", "financ", "accountant"),
    "people": ("recursos humanos", "gestion humana", "reclut", "recruit", "talento humano"),
    "logistics": ("logistic", "inventario", "almacen", "bodega", "warehouse"),
    "design": ("disen", "designer", "ilustr", "graphic"),
    "education": ("docente", "profesor", "teacher", "pedagog"),
    "health": ("enfermer", "medic", "fisioter", "nurse"),
}


def relevant_experience(profile, job, today=None):
    details = getattr(job, "quality_details", None) or {}
    years = details.get("experience_years")
    source = "structured" if years is not None else None
    if years is None:
        text = fold(getattr(job, "requirements", ""))
        match = re.search(r"\b(\d{1,2})(?:\s*(?:a|[-–])\s*\d{1,2})?\s*anos?\s+(?:de\s+)?experiencia\b", text)
        if match:
            years, source = int(match[1]), "requirements_text"
    if type(years) not in {int, float} or not 0 <= years <= 50:
        years, source = None, None
    title = fold(getattr(job, "title", ""))
    families = {key for key, terms in ROLE_FAMILIES.items() if any(term in title for term in terms)}
    generic = {"analista", "asistente", "profesional", "auxiliar", "senior", "junior", "de", "del", "en", "y", "ingeniero", "ingeniera", "coordinador", "coordinadora", "especialista"}
    title_tokens = {word for word in re.findall(r"[a-z]{4,}", title) if word not in generic}
    requested = [row["skill"] for row in requirements_for(job)]
    related = []
    for entry in getattr(profile, "experiences", None) or []:
        role = fold(entry.get("role", ""))
        contextual = skill_mentions(f"{entry.get('role', '')}; {entry.get('description', '')}", requested)
        aligned = bool(title_tokens & set(re.findall(r"[a-z]{4,}", role))) or any(any(term in role for term in ROLE_FAMILIES[key]) for key in families)
        if aligned or any(item["state"] in {"applied", "declared"} for item in contextual):
            related.append(entry)
    months = experience_months(related, today=today)
    required = int(years * 12) if years is not None else None
    dated = [entry for entry in related if experience_months([entry], today=today) > 0]
    unknown_dates = len(related) - len(dated)
    status = "fulfilled" if required == 0 or required is not None and months >= required else "unknown" if required is None or not dated else "partial"
    return {"required_months": required, "related_months": months, "related_roles": len(related), "roles_without_dates": unknown_dates,
            "estimated": any(month_index(entry.get("start_date")) is None for entry in dated), "status": status,
            "score": None if required is None or required > 0 and not dated else 100 if required == 0 else round(min(100, months / required * 100), 2),
            "source": source, "as_of_month": (today or date.today()).strftime("%Y-%m"),
            "notice": "Meses en cargos relacionados; no prueban uso continuo de una herramienta. Los periodos simultáneos se cuentan una sola vez; fechas incompletas se indican como desconocidas o aproximadas."}
