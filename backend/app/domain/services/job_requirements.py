"""Canonical experience requirement in months, preserving existing year-only offers."""


def minimum_experience_months(details):
    months = details.get("experience_months")
    if type(months) is int and 0 <= months <= 600:
        return months
    years = details.get("experience_years")
    return round(years * 12) if type(years) in {int, float} and 0 <= years <= 50 else None


def experience_label(details):
    months = minimum_experience_months(details)
    if months is None:
        return "Experiencia por definir"
    if months == 0:
        return "Sin experiencia previa"
    years, rest = divmod(months, 12)
    parts = []
    if years:
        parts.append(f"{years} {'año' if years == 1 else 'años'}")
    if rest:
        parts.append(f"{rest} {'mes' if rest == 1 else 'meses'}")
    return " y ".join(parts)
