import json
import unicodedata
from functools import lru_cache
from pathlib import Path


def fold(value):
    return "".join(char for char in unicodedata.normalize("NFKD", str(value or "").casefold()) if not unicodedata.combining(char)).strip()


@lru_cache(maxsize=1)
def countries():
    return {row["code"]: row for row in json.loads((Path(__file__).parents[1] / "data/remote_locations.json").read_text(encoding="utf-8"))["countries"]}


@lru_cache(maxsize=1)
def country_names():
    return {fold(name): code for code, row in countries().items() for name in (code, row["name"], row["english_name"])}


def profile_country(profile):
    explicit = (getattr(profile, "preferences", None) or {}).get("country_code")
    if explicit in countries():
        return explicit
    location = str(getattr(profile, "location", None) or "")
    parts = [fold(value) for value in location.split(",")]
    aliases = {"ee. uu.": "US", "estados unidos": "US", "usa": "US", "reino unido": "GB"}
    for part in reversed(parts):
        if part in aliases:
            return aliases[part]
        if part in country_names():
            return country_names()[part]
    from app.domain.services.colombian_locations import canonical_commuting_city
    try:
        canonical_commuting_city(location)
        return "CO"
    except ValueError:
        return None


def remote_scope_fit(profile, job):
    scope = (getattr(job, "quality_details", None) or {}).get("remote_scope")
    if not scope or scope.get("mode") == "global":
        return None
    country = profile_country(profile)
    if country is None:
        return {"status": "unknown", "message": "Falta confirmar el país de residencia frente al alcance remoto de esta oferta.", "factor": 1, "invitation_allowed": True}
    allowed = country in scope.get("countries", []) or countries()[country]["continent"] in scope.get("continents", [])
    return {"status": "remote" if allowed else "conflict", "message": "El país de residencia está dentro del alcance remoto." if allowed else "El país de residencia está fuera de los países o continentes admitidos para trabajar en remoto.", "factor": 1 if allowed else 0, "invitation_allowed": allowed}
