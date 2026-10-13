"""Month precision when supplied; conservative compatibility with year-only CVs."""
import re
from datetime import date


def month_index(value):
    if not re.fullmatch(r"(?:19|20)\d{2}-(?:0[1-9]|1[0-2])", str(value or "")):
        return None
    year, month = map(int, value.split("-"))
    return year * 12 + month - 1


def experience_months(items, today=None):
    today = today or date.today()
    current = today.year * 12 + today.month - 1
    periods = []
    for item in items or []:
        start = month_index(item.get("start_date"))
        end = month_index(item.get("end_date"))
        ongoing = item.get("is_current") is True or str(item.get("end_year", "")).casefold() in {"presente", "actualidad", "actual"}
        if start is not None:
            end = current if ongoing else end
            if end is None:
                continue  # An empty end date does not mean currently employed.
            end = min(end, current)
        else:
            # Years remain approximate; never invent a month in the stored CV.
            a = re.fullmatch(r"(?:19|20)\d{2}", str(item.get("start_year", "")))
            b = re.fullmatch(r"(?:19|20)\d{2}", str(item.get("end_year", "")))
            if not a or not (b or ongoing):
                continue
            start = int(a.group()) * 12
            end = current if ongoing else min(int(b.group()) * 12 - 1, current)
        if end >= start:
            periods.append((start, end + 1))  # Employment months include both endpoints.
    merged = []
    for start, end in sorted(periods):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return sum(end - start for start, end in merged)


def validate_experiences(items):
    current = date.today().strftime("%Y-%m")
    for item in items or []:
        start, end = item.get("start_date"), item.get("end_date")
        for value in (start, end):
            if value and month_index(value) is None:
                raise ValueError("Experiencia: usa mes y año con formato AAAA-MM")
            if value and value > current:
                raise ValueError("Experiencia: las fechas no pueden estar en el futuro")
        if item.get("is_current") is not None and type(item["is_current"]) is not bool:
            raise ValueError("Indica si trabajas actualmente en el cargo")
        if item.get("is_current") and end:
            raise ValueError("Un cargo actual no debe tener fecha de finalización")
        if start and end and start > end:
            raise ValueError("Experiencia: la finalización debe ser posterior al inicio")
    return items
