"""Declared credentials: exact accepted categories, current validity, no registry verification."""

from datetime import date

from app.domain.services.professions import normalize


def profile_credentials(profile, field):
    return getattr(profile, field, None) or (
        getattr(profile, "preferences", None) or {}
    ).get(field, [])


def validity(record, *, driving=False, today=None):
    today = today or date.today()
    status = record.get("status", "unknown")
    if status in {"expired", "suspended", "in_progress"}:
        return "not_met"
    expires = record.get("expires_on")
    if expires:
        try:
            if date.fromisoformat(str(expires)) < today:
                return "not_met"
        except ValueError:
            return "review"
    return "declared" if status == "valid" and (expires or not driving) else "review"


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


def credential_evaluation(profile, job, today=None):
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
        states = [
            validity(record, driving=key == "driving_categories", today=today)
            for record in relevant
        ]
        state = (
            "declared"
            if "declared" in states
            else "review"
            if "review" in states
            else "not_met"
            if states
            else "missing"
        )
        message = {
            "declared": "Registrada como vigente por la persona; pendiente de verificación documental.",
            "review": "Hay un registro, pero falta confirmar su estado o vencimiento.",
            "not_met": "El registro está vencido, suspendido o en trámite.",
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
        else "declared"
        if all(row["status"] == "declared" for row in groups)
        else "not_met"
        if any(row["status"] in {"missing", "not_met"} for row in groups)
        else "review"
    )
    return {
        "status": state,
        "groups": groups,
        "notice": "Revisión documental separada de la afinidad profesional. Los datos son declarados; TalentSync no verifica registros oficiales ni autoriza el ejercicio profesional.",
    }
