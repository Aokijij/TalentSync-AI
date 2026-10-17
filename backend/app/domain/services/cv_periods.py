"""Read explicit month/year ranges without inventing missing months."""

import re
import unicodedata

MONTHS = {
    name: number
    for number, names in enumerate(
        [
            "enero ene january jan",
            "febrero feb february",
            "marzo mar march",
            "abril abr april apr",
            "mayo may",
            "junio jun june",
            "julio jul july",
            "agosto ago august aug",
            "septiembre setiembre sep sept september",
            "octubre oct october",
            "noviembre nov november",
            "diciembre dic december dec",
        ],
        1,
    )
    for name in names.split()
}
MONTH = "|".join(sorted(MONTHS, key=len, reverse=True))
YEAR = r"(?:19|20)\d{2}"
DATE = rf"(?:(?:{MONTH})\.?\s+(?:de\s+)?{YEAR}|(?:0?[1-9]|1[0-2])[/.-]{YEAR}|{YEAR}[-/](?:0[1-9]|1[0-2])|{YEAR})"
CURRENT = r"presente|actualidad|actual|en\s+curso|vigente|present|current|now"
PERIOD = re.compile(
    rf"(?<!\w)(?P<start>{DATE})\s*(?:[-–—]|\ba\b|\bhasta\b|\bto\b)\s*(?P<end>{DATE}|{CURRENT})(?!\w)",
    re.I,
)


def _fold(value):
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value.lower())
        if not unicodedata.combining(char)
    )


def _date(value):
    year = re.search(YEAR, value).group()
    named = re.search(rf"\b({MONTH})\b", value)
    month = MONTHS[named.group()] if named else None
    if month is None:
        numeric = re.fullmatch(rf"(0?[1-9]|1[0-2])[/.-]({YEAR})", value)
        iso = re.fullmatch(rf"({YEAR})[-/](0[1-9]|1[0-2])", value)
        month = int(numeric.group(1)) if numeric else int(iso.group(2)) if iso else None
    return year, f"{year}-{month:02d}" if month else None


def read_period(value):
    match = PERIOD.search(_fold(value))
    if not match:
        return None
    start_year, start_date = _date(match["start"])
    current = re.fullmatch(CURRENT, match["end"]) is not None
    end_year, end_date = ("Presente", None) if current else _date(match["end"])
    result = {"start_year": start_year, "end_year": end_year}
    if start_date:
        result["start_date"] = start_date
    if end_date:
        result["end_date"] = end_date
    if current:
        result["is_current"] = True
    return result, match.span()


def period_fields(value):
    result = read_period(value)
    return result[0] if result else {}
