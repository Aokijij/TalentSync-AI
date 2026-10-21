"""Declared credentials: exact accepted categories and professions, no registry checks."""

from app.domain.services.professions import normalize


def profile_credentials(profile, field):
    return getattr(profile, field, None) or (
        getattr(profile, "preferences", None) or {}
    ).get(field, [])


def same_profession(left, right):
    def key(value):
        return (
            normalize(value)
            .replace("ingeniero ", "ingenieria ")
            .replace("ingeniera ", "ingenieria ")
            .replace("contador publico", "contaduria publica")
            .replace("contadora publica", "contaduria publica")
        )

    return bool(key(left) and key(left) == key(right))


def credential_evaluation(profile, job):
    required = (getattr(job, "quality_details", None) or {}).get(
        "credential_requirements"
    ) or {}
    groups = []
    for key, field, label in [
        ("driving_categories", "driving_licenses", "Licencia de conducción"),
        ("professional_cards", "professional_cards", "Tarjeta profesional"),
    ]:
        alternatives = required.get(key) or []
        if not alternatives:
            continue
        records = profile_credentials(profile, field)
        relevant = [
            record
            for record in records
            if any(
                record.get("category") == wanted
                if key == "driving_categories"
                else same_profession(record.get("profession", ""), wanted)
                for wanted in alternatives
            )
        ]
        state = "recorded" if relevant else "missing"
        message = {
            "recorded": "La persona registró una de las alternativas solicitadas. Su autenticidad se revisa durante la contratación.",
            "missing": "No hay un registro de las alternativas solicitadas.",
        }[state]
        groups.append(
            {
                "key": key,
                "label": label,
                "accepted": alternatives,
                "status": state,
                "reason": message,
            }
        )
    state = (
        "not_required"
        if not groups
        else "recorded"
        if all(row["status"] == "recorded" for row in groups)
        else "not_met"
    )
    return {
        "status": state,
        "groups": groups,
        "notice": "Se comparan los documentos registrados, por separado de la afinidad profesional. TalentSync no verifica su autenticidad.",
    }
