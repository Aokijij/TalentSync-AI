from types import SimpleNamespace

import pytest

from app.domain.services.colombian_locations import canonical_commuting_city
from app.domain.services.work_preferences import location_fit


@pytest.mark.parametrize("alias,official,department", [
    ("Cartagena", "Cartagena De Indias", "Bolívar"),
    ("cucuta", "San José De Cúcuta", "Norte de Santander"),
    ("bogota dc", "Bogotá", "Bogotá D.C."),
    ("Cali", "Santiago De Cali", "Valle del Cauca"),
])
def test_common_city_names_validate_and_do_not_exclude_local_candidates(alias, official, department):
    assert canonical_commuting_city(alias) == official
    assert canonical_commuting_city(f"{alias}, {department}") == f"{official}, {department}"
    profile = SimpleNamespace(location=alias, department=department, preferences={"mobility": {"willing_to_relocate": False}})
    job = SimpleNamespace(modality="onsite", location=official, department=department)
    assert location_fit(profile, job)["status"] == "local"


@pytest.mark.parametrize("value", ["Ciudad inventada", "Medellín, Santander", "Cúcuta, Antioquia"])
def test_city_catalog_rejects_invented_cities_and_wrong_departments(value):
    with pytest.raises(ValueError, match="ciudad válida"):
        canonical_commuting_city(value)
