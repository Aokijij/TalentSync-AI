"""Explicit current employment and study status; legacy read models stay readable."""
from datetime import date


def is_ongoing(item):
    return item.get("is_current") is True or str(item.get("end_year", "")).casefold() in {"presente", "actualidad", "actual", "en curso"}


def single_current_employment(items):
    if sum(is_ongoing(item) for item in items or []) > 1:
        raise ValueError("Solo puedes marcar un trabajo como actual. Revisa la finalización de los anteriores.")
    return items


def validate_educations(items):
    for index, item in enumerate(items or []):
        if str(item.get("end_year") or "").casefold() in {"presente", "actualidad", "actual", "en curso"}:
            item = {**item, "is_current": True, "end_year": ""}
            items[index] = item
        if item.get("level") not in {None, "", "secondary", "technical", "technologist", "university", "postgraduate"}:
            raise ValueError("Selecciona un nivel de formación válido")
        if item.get("is_current") is not None and type(item["is_current"]) is not bool:
            raise ValueError("Indica si estudias actualmente en la institución")
        start, end = str(item.get("start_year") or ""), str(item.get("end_year") or "")
        for value in (start, end):
            if value and not (len(value) == 4 and value.isdigit() and 1900 <= int(value) <= date.today().year):
                raise ValueError("Formación: indica años válidos que no estén en el futuro")
        if item.get("is_current") and end:
            raise ValueError("Un estudio en curso no debe tener año de finalización")
        if start and end and start > end:
            raise ValueError("Formación: la finalización debe ser posterior al inicio")
    return items
