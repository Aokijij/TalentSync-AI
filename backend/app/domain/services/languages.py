"""Canonical language identities shared by matching and API validation."""
import unicodedata

LEVELS = {level: index for index, level in enumerate(("A1", "A2", "B1", "B2", "C1", "C2", "NATIVE"), 1)}


def language_name(value):
    name = " ".join(str(value or "").casefold().split())
    key = "".join(c for c in unicodedata.normalize("NFKD", name) if not unicodedata.combining(c))
    return {"english": "inglés", "ingles": "inglés", "espanol": "español", "spanish": "español", "frances": "francés", "french": "francés", "portugues": "portugués", "portuguese": "portugués", "aleman": "alemán", "german": "alemán"}.get(key, name)


def language_level(value):
    level = str(value or "").strip().upper()
    return "NATIVE" if level in {"NATIVO", "NATIVA", "NATIVO/A"} else level


def language_levels(items):
    available = {}
    for item in items or []:
        name, level = language_name(item.get("name")), language_level(item.get("level"))
        if name and level in LEVELS and LEVELS[level] > LEVELS.get(available.get(name), 0):
            available[name] = level
    return available
