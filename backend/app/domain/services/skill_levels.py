from app.domain.services.skills import skill_key, skill_set

SKILL_LEVELS = {"learning": .5, "basic": 1, "intermediate": 2, "advanced": 3, "expert": 4}
SKILL_LEVEL_LABELS = {"unspecified": "Sin indicar", "learning": "En aprendizaje", "basic": "Básico", "intermediate": "Intermedio", "advanced": "Avanzado", "expert": "Experto"}


def declared_skill_levels(profile):
    values = getattr(profile, "skill_levels", None)
    if values is None:
        values = (getattr(profile, "preferences", None) or {}).get("skill_levels", {})
    known = skill_set(profile.skills)
    return {skill_key(key): value for key, value in (values or {}).items() if skill_key(key) in known and value in SKILL_LEVELS}
def inferred_skill_levels(text, skills):
    """Use an explicit, adjacent proficiency statement, never years or job title."""
    import re

    from app.domain.services.skill_context import fold, skill_mentions

    names = {"aprendizaje": "learning", "learning": "learning", "principiante": "basic", "basico": "basic", "basic": "basic", "intermedio": "intermediate", "intermediate": "intermediate", "avanzado": "advanced", "advanced": "advanced", "experto": "expert", "expert": "expert"}
    alternatives = "|".join(names)
    source = str(text or "")[:30000]
    found = {}
    for row in skill_mentions(source, skills):
        if row["state"] in {"negated", "training", "unknown"}:
            continue
        before = fold(source[max(0, row["start"] - 45):row["start"]])
        after = fold(source[row["end"]:row["end"] + 45])
        right = re.match(rf"\s*[:(—–-]?\s*(?:nivel\s+)?({alternatives})(?:s|a|as)?\b", after)
        left = re.search(rf"\b({alternatives})(?:s|a|as)?\s+(?:(?:en|de|con)\s+)?$", before)
        match = right or left
        level = "learning" if row["state"] == "learning" else names[match[1]] if match else None
        if level and (row["skill"] not in found or SKILL_LEVELS[level] < SKILL_LEVELS[found[row["skill"]]["level"]]):
            found[row["skill"]] = {"level": level, "source": "cv_explicit", "excerpt": row["excerpt"]}
    return {skill_key(skill): found.get(skill_key(skill), {"level": "learning", "source": "default", "excerpt": ""}) for skill in skills}
