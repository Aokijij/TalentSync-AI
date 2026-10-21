"""Candidate-controlled personal details; never a matching or coach input."""
IDENTIFICATION_TYPES = {
    "CC": "Cédula de ciudadanía", "CE": "Cédula de extranjería",
    "TI": "Tarjeta de identidad", "PPT": "Permiso por Protección Temporal",
    "passport": "Pasaporte", "other": "Otro documento",
}


def shared_personal_details(profile):
    visibility = getattr(profile, "personal_visibility", None) or {}
    return {key: getattr(profile, key, None) for key in ("birth_date", "identification") if visibility.get(key) is True}


def personal_detail_lines(profile):
    values = shared_personal_details(profile)
    result = []
    if values.get("birth_date"):
        year, month, day = str(values["birth_date"]).split("-")
        result.append(("Nacimiento", f"{day}/{month}/{year}"))
    document = values.get("identification") or {}
    if document.get("number"):
        result.append((IDENTIFICATION_TYPES.get(document.get("type"), "Identificación"), document["number"]))
    return result
