"""Bounded professional facts and checks for a reviewable local AI proposal."""
import re

from app.domain.services.experience_dates import recent_experiences
from app.domain.services.profile_status import is_ongoing
from app.domain.services.skill_context import fold


def summary_facts(profile):
    def text(value, limit):
        return str(value or "").strip()[:limit]
    skills = [text(value, 100) for value in (getattr(profile, "skills", None) or [])[:12]]
    experiences = [{"cargo": text(row.get("role"), 150), "funciones": text(row.get("description"), 450), "actual": is_ongoing(row)}
                   for row in recent_experiences(getattr(profile, "experiences", None) or [])[:4]]
    studies = sorted(getattr(profile, "educations", None) or [], key=lambda row: (is_ongoing(row), str(row.get("end_year") or ""), str(row.get("start_year") or "")), reverse=True)
    education = [{"titulo": text(row.get("degree"), 200), "en_curso": is_ongoing(row)} for row in studies[:2]]
    return {"profesion": text(getattr(profile, "profession", ""), 200), "habilidades": skills,
            "experiencias": experiences, "formacion": education, "formacion_anterior": text(getattr(profile, "education", ""), 300),
            "resumen_actual": text(getattr(profile, "experience", ""), 900)}


def fact_text(facts):
    values = [facts["profesion"], *facts["habilidades"], facts["formacion_anterior"], facts["resumen_actual"]]
    values.extend(value for row in facts["experiencias"] for key, value in row.items() if key != "actual")
    values.extend(row["titulo"] for row in facts["formacion"])
    return " ".join(filter(None, values))


def validate_summary(generated, facts, *, extract_skills):
    value = generated.get("summary") if isinstance(generated, dict) else None
    text = re.sub(r"\s+", " ", value).strip() if isinstance(value, str) else ""
    text = re.sub(r"\bEjecu[oó]\b", "Ejecuté", text, flags=re.I)
    if not 60 <= len(text) <= 1600 or re.search(r"<[^>]+>|\[[^]]+\]", text):
        raise ValueError("No se obtuvo un resumen completo. Tu texto se conserva; puedes volver a generar la propuesta")
    source, target = fold(fact_text(facts)), fold(text)
    if not set(re.findall(r"\b(?:no|nunca|sin)\b", target)) <= set(re.findall(r"\b(?:no|nunca|sin)\b", source)):
        raise ValueError("La propuesta cambió el sentido de tu experiencia. Tu texto se conserva; vuelve a generarla")
    if not set(re.findall(r"\d+(?:[.,]\d+)?", target)) <= set(re.findall(r"\d+(?:[.,]\d+)?", source)) or "%" in target and "%" not in source:
        raise ValueError("La propuesta añadió cifras que no aparecen en tu perfil. Genera otra versión o escribe tu resumen")
    claims = ("expert", "especiali", "lider", "dirig", "aument", "reduj", "optimiz", "certific", "maestr", "doctor", "bilingue")
    if any(claim in target and claim not in source for claim in claims):
        raise ValueError("La propuesta añadió una cualificación o un logro sin respaldo. Tu resumen se conserva")
    if not set(extract_skills(text)) <= set(extract_skills(fact_text(facts))):
        raise ValueError("La propuesta añadió habilidades que no aparecen en tu información. Vuelve a generarla y revisa el texto")
    anchors = {word for word in re.findall(r"\b[a-z]{4,}\b", source)} - {"experiencia", "profesional", "trabajo", "formacion", "habilidades", "equipo", "para", "como", "desde", "entre"}
    if anchors and not any(word in target for word in anchors):
        raise ValueError("La propuesta no refleja los datos de tu perfil. Inténtalo de nuevo")
    return text
