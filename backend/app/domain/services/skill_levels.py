from app.domain.services.skills import skill_key, skill_set

SKILL_LEVELS = {"learning": .5, "basic": 1, "intermediate": 2, "advanced": 3, "expert": 4}
SKILL_LEVEL_LABELS = {"unspecified": "Sin indicar", "learning": "En aprendizaje", "basic": "Básico", "intermediate": "Intermedio", "advanced": "Avanzado", "expert": "Experto"}


def declared_skill_levels(profile):
    values = getattr(profile, "skill_levels", None)
    if values is None:
        values = (getattr(profile, "preferences", None) or {}).get("skill_levels", {})
    known = skill_set(profile.skills)
    return {skill_key(key): value for key, value in (values or {}).items() if skill_key(key) in known and value in SKILL_LEVELS}
