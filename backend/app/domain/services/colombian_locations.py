"""Shared DIVIPOLA snapshot; validation does not depend on a network service."""
import json
from functools import lru_cache
from pathlib import Path

from app.domain.services.work_preferences import city_key


@lru_cache(maxsize=1)
def locations():
    return json.loads((Path(__file__).parents[1] / "data" / "colombian_locations.json").read_text(encoding="utf-8"))


def canonical_commuting_city(value):
    parts = value.strip().split(",", 1)
    for department, cities in locations().items():
        if len(parts) > 1 and city_key(parts[1]) != city_key(department):
            continue
        for city in cities:
            if city_key(city) == city_key(parts[0]):
                return f"{city}, {department}" if len(parts) > 1 else city
    raise ValueError("Elige una ciudad válida de la lista de municipios de Colombia")
