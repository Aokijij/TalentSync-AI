"""Deterministic career, degree and certification equivalence helpers."""

import re
import unicodedata

# Broad profession groups remain for market-sector analysis only, never academic matching.
PROFESSION_GROUPS = {
    "software": ("ingenieria de sistemas", "ingenieria informatica", "ingenieria de software", "ciencias de la computacion", "desarrollo de software", "tecnologia en sistemas", "tecnico en sistemas", "tecnico profesional en sistemas", "analisis y desarrollo de sistemas"),
    "data": ("ciencia de datos", "analitica de datos", "estadistica", "matematicas", "inteligencia de negocios", "business intelligence", "ingenieria de datos"),
    "electronics": ("ingenieria electronica", "ingenieria electrica", "telecomunicaciones", "automatizacion", "mecatronica"),
    "civil": ("ingenieria civil", "construccion", "arquitectura", "obras civiles", "gestion de la construccion"),
    "business": ("administracion de empresas", "negocios", "ingenieria administrativa", "economia", "gestion empresarial"),
    "finance": ("finanzas", "contaduria", "contabilidad", "economia", "administracion financiera", "banca"),
    "marketing": ("mercadeo", "marketing", "publicidad", "comunicacion social", "comunicacion digital"),
    "people": ("psicologia", "recursos humanos", "gestion humana", "trabajo social"),
    "industrial": ("ingenieria industrial", "logistica", "produccion", "calidad", "operaciones"),
    "health": ("medicina", "enfermeria", "salud ocupacional", "fisioterapia", "psicologia clinica"),
    "legal": ("derecho", "ciencias juridicas", "abogacia"),
    "education": ("educacion", "pedagogia", "licenciatura", "docencia"),
}
LEVEL_RANK = {"secondary": .5, "technical": 1, "technologist": 2, "university": 3, "postgraduate": 4}
EDUCATION_LEVEL_LABELS = {"secondary": "Bachillerato", "technical": "Técnico", "technologist": "Tecnólogo", "university": "Profesional universitario", "postgraduate": "Posgrado"}


def normalize(value):
    text = unicodedata.normalize("NFKD", str(value or "").lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9+#.]+", text))


def career_groups(value):
    text = normalize(value)
    return {group for group, aliases in PROFESSION_GROUPS.items() if text and any(normalize(alias) in text or text in normalize(alias) for alias in aliases)}


def fields_are_related(candidate, requested):
    from app.domain.services.academic_fields import compare_fields
    return compare_fields(candidate, requested)["status"] in {"exact", "name_variant", "related"}


def infer_education_level(value):
    text = normalize(value)
    if any(term in text for term in ("especializacion", "maestria", "master", "posgrado", "doctorado")): return "postgraduate"
    if re.search(r"\btecnolog[oa]\b|\btecnologia\s+en\b", text): return "technologist"
    if any(term in text for term in ("tecnico", "tecnica")): return "technical"
    if any(term in text for term in ("pregrado", "profesional", "universidad", "universitario", "ingenieria", "licenciatura")): return "university"
    if any(term in text for term in ("bachiller", "secundaria", "educacion media")): return "secondary"
    return None


def infer_study_fields(value):
    from app.domain.services.academic_fields import alias_index
    text = normalize(value)
    mentions = []
    for alias, row in alias_index().items():
        for match in re.finditer(rf"(?<!\w){re.escape(alias)}(?!\w)", text):
            mentions.append((match.start(), match.end(), row["label"]))
    selected = []
    for start, end, label in sorted(mentions, key=lambda item: item[1] - item[0], reverse=True):
        if not any(start < other_end and end > other_start for other_start, other_end, _ in selected):
            selected.append((start, end, label))
    return list(dict.fromkeys(label for _, _, label in sorted(selected)))[:8]


def education_match(profile, job):
    from app.domain.services.academic_matching import education_evaluation
    return education_evaluation(profile, job)["score"]


def certification_match(profile, job):
    text = normalize(" ".join(f"{item.get('name', '')} {item.get('issuer', '')}" for item in (getattr(profile, "certifications", None) or [])))
    skills = getattr(job, "skills", None) or []
    if not text or not skills: return None
    related = 0
    for skill in skills:
        normalized = normalize(skill)
        tokens = [token for token in normalized.split() if len(token) > 2]
        aliases = {
            "analisis de datos": ("data analyst", "data analytics", "power bi", "business intelligence"),
            "gestion de proyectos": ("scrum master", "project management", "pmp"),
            "ciberseguridad": ("cybersecurity", "security+", "cissp"),
            "computacion en la nube": ("azure", "aws", "cloud"),
        }
        alias_match = any(alias in text for alias in aliases.get(normalized, ()))
        if normalized in text or (tokens and all(token in text for token in tokens)) or alias_match: related += 1
    return round(min(100.0, related / max(1, min(len(skills), 4)) * 100), 2)


def required_certification_match(profile, job):
    """Only explicitly requested, identifiable credentials affect the score."""
    requirements = str(getattr(job, "requirements", "") or "")
    clauses = re.split(r"[\n;.!?]", requirements)
    requested = []
    for clause in clauses:
        value = normalize(clause)
        match = re.search(r"\b(?:certificacion(?:es)?|certificad[oa]s?|certification|certified)\b", value)
        if not match or re.search(r"\b(?:no|sin|opcional|deseable|preferible|ofrecemos|brindamos|optional|preferred)\b", value):
            continue
        suffix = value[match.end():].strip()
        stop = set("en de del la el los las con vigente vigentes valida valido requerida requerido obligatoria obligatorio actualizada actualizado es son indispensable necesaria necesario y o para contar tener contar certificacion certificaciones".split())
        terms = {term for term in suffix.split() if len(term) > 1 and term not in stop}
        if terms:
            requested.append(terms)
    if not requested:
        return None
    certificates = [set(normalize(item.get("name", "")).split()) for item in getattr(profile, "certifications", None) or []]
    return round(sum(any(terms <= certificate for certificate in certificates) for terms in requested) / len(requested) * 100, 2)
