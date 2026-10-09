def effective_preferences(profile):
    """Profile fields are authoritative; preferences only stores requirement flags."""
    flags = getattr(profile, "preferences", None) or {}
    modality = getattr(profile, "preferred_modality", None)
    location = getattr(profile, "location", None)
    return {
        "minimum_salary": getattr(profile, "desired_salary", None),
        "modalities": [modality] if modality else [],
        "locations": [location] if location else [],
        **{key: bool(flags.get(key, False)) for key in (
            "salary_required", "modality_required", "location_required"
        )},
    }
