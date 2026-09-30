import re
from urllib.parse import urlparse

PORTAL_DOMAINS = (
    ("linkedin.", "LinkedIn"),
    ("computrabajo.", "Computrabajo"),
    ("elempleo.", "El Empleo"),
    ("indeed.", "Indeed"),
    ("glassdoor.", "Glassdoor"),
    ("magneto365.", "Magneto"),
    ("magneto.", "Magneto"),
    ("ticjob.", "Ticjob"),
    ("talent.com", "Talent.com"),
    ("jobrapido.", "Jobrapido"),
    ("bebee.", "BeBee"),
    ("ziprecruiter.", "ZipRecruiter"),
    ("workdayjobs.", "Workday"),
    ("myworkdayjobs.", "Workday"),
    ("greenhouse.io", "Greenhouse"),
    ("lever.co", "Lever"),
)


def external_portal(url: str | None, location: str | None = None) -> str:
    """Return the user-facing destination instead of the technical aggregator."""
    hostname = urlparse(url or "").hostname or ""
    normalized_host = hostname.casefold().removeprefix("www.")
    for fragment, label in PORTAL_DOMAINS:
        if fragment in normalized_host:
            return label

    text = location or ""
    match = re.search(r"(?:a través de|via)\s+([^•,]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "sitio de la empresa"


def clean_external_location(value: str | None) -> str:
    text = " ".join(str(value or "").split())
    text = re.split(r"\s*[•|]\s*(?:a través de|via)\s+", text, flags=re.IGNORECASE)[0]
    return text.strip(" ,-|•")
