import unicodedata


def city_key(value):
    value = str(value or "").split(",")[0].strip().casefold()
    value = "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))
    return "bogota" if value in {"bogota d.c.", "bogota dc", "bogota d.c"} else value


def location_fit(profile, job):
    mobility = (getattr(profile, "preferences", None) or {}).get("mobility", {})
    def result(status, message, factor=1):
        return {"status": status, "message": message, "factor": factor, "invitation_allowed": status != "conflict"}
    if job.modality == "remote":
        return result("remote", "Sin asistencia presencial; confirma el territorio permitido por la oferta.")
    if job.modality not in {"onsite", "hybrid"} or not job.location or not getattr(profile, "location", None):
        return result("unknown", "Falta confirmar la ciudad o la disponibilidad para asistir.")
    same = city_key(profile.location) == city_key(job.location)
    departments = (getattr(profile, "department", None), getattr(job, "department", None))
    if same and all(departments) and city_key(departments[0]) != city_key(departments[1]):
        same = False
    def commuting_match(value):
        parts = str(value).split(",", 1)
        return city_key(parts[0]) == city_key(job.location) and (len(parts) == 1 or not departments[1] or city_key(parts[1]) == city_key(departments[1]))
    if same or any(commuting_match(value) for value in mobility.get("commuting_cities", [])):
        return result("local", "Puede asistir en la ciudad de la vacante según su perfil.")
    if mobility.get("willing_to_relocate") is True:
        return result("relocation", "Está dispuesto a cambiar de ciudad; acuerda las condiciones del traslado.")
    if mobility.get("willing_to_travel") is True:
        return result("confirm", "Puede viajar, pero esto no confirma asistencia habitual. Consulta su disponibilidad.")
    if mobility.get("willing_to_relocate") is False and mobility.get("willing_to_travel") is False:
        return result("conflict", "Otra ciudad: no acepta traslado ni viajes. Ajuste de disponibilidad: −20% relativo al índice profesional.", .8)
    return result("unknown", "Otra ciudad: falta confirmar traslado, viajes o asistencia habitual.")


def effective_preferences(profile):
    """Profile fields are authoritative; preferences only stores requirement flags."""
    flags = getattr(profile, "preferences", None) or {}
    modality = getattr(profile, "preferred_modality", None)
    location = getattr(profile, "location", None)
    return {
        "minimum_salary": getattr(profile, "desired_salary", None),
        "modalities": [modality] if modality else [],
        "locations": [location] if location else [],
        "mobility": flags.get("mobility", {}),
        **{key: bool(flags.get(key, False)) for key in (
            "salary_required", "modality_required", "location_required"
        )},
    }


def employer_preference_conflicts(profile, job):
    """Hard conditions for invitations; occasional travel is not daily attendance."""
    prefs = effective_preferences(profile)
    fit = location_fit(profile, job)
    conflicts = []
    if job.modality in {"onsite", "hybrid"} and fit["status"] not in {"local", "relocation"}:
        if prefs["mobility"].get("willing_to_relocate") is False:
            conflicts.append("No acepta traslado ni asistencia habitual en la ciudad de la vacante")
        elif prefs["location_required"]:
            conflicts.append("No se ha confirmado la ciudad imprescindible")
    if prefs["modality_required"] and prefs["modalities"] and job.modality not in prefs["modalities"]:
        conflicts.append("La modalidad no cumple su condición imprescindible")
    if prefs["salary_required"] and prefs["minimum_salary"] is not None:
        if job.salary is None or job.salary < prefs["minimum_salary"]:
            conflicts.append("El salario no cumple su mínimo imprescindible")
    return conflicts
