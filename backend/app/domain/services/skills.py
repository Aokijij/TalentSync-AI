import unicodedata


def skill_key(skill: object) -> str:
    value = unicodedata.normalize("NFKD", str(skill).strip().lower())
    value = "".join(
        character for character in value if not unicodedata.combining(character)
    )
    aliases = {
        "node.js": "nodejs",
        "springboot": "spring boot",
        "microservices": "microservicios",
        "postgres": "postgresql",
        "k8s": "kubernetes",
        "js": "javascript",
        "ts": "typescript",
        "mlops": "mlops",
        "rest api": "api rest",
        "restful api": "api rest",
        "atencion al cliente": "servicio al cliente",
        "customer service": "servicio al cliente",
        "dotnet": ".net",
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


# Directional relationships describe a learning foundation, never equivalence.
SKILL_FOUNDATIONS = {
    "spring boot": {"java", "arquitectura mvc"},
    "microservicios": {"spring boot", "api rest", "docker"},
    "kubernetes": {"docker", "linux"},
    "mlops": {"machine learning", "python", "docker"},
    "angular": {"typescript", "javascript"},
    "react": {"javascript", "typescript"},
    "fastapi": {"python", "api rest"},
    "power bi": {"excel", "sql"},
    "terraform": {"aws", "azure", "linux"},
}


def skill_gap(candidate_skills, requirements):
    available = skill_set(candidate_skills)
    result = []
    for requirement in requirements:
        key = skill_key(requirement["skill"])
        foundations = sorted(available & SKILL_FOUNDATIONS.get(key, set()))
        result.append({"essential": False, "weight": 1, "level": "unspecified", **requirement, "key": key, "covered": key in available,
                       "foundations": foundations if key not in available else [],
                       "status": "declared" if key in available else "related" if foundations else "missing"})
    return result
