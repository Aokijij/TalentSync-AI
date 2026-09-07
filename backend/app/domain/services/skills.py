import unicodedata


def skill_key(skill: object) -> str:
    value = unicodedata.normalize("NFKD", str(skill).strip().lower())
    value = "".join(
        character for character in value if not unicodedata.combining(character)
    )
    aliases = {
        "node.js": "nodejs",
        "rest api": "api rest",
        "restful api": "api rest",
        "gestion sst": "seguridad y salud en el trabajo",
        "sst": "seguridad y salud en el trabajo",
    }
    return aliases.get(value, value)


def normalize_skills(skills: list[str] | None) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for skill in skills or []:
        value = str(skill).strip().lower()
        key = skill_key(value)
        if value and key not in seen:
            seen.add(key)
            normalized.append(value)
    return normalized


def skill_set(skills: list[str] | None) -> set[str]:
    return {skill_key(skill) for skill in skills or [] if str(skill).strip()}
