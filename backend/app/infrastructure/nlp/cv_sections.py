"""Complementary CV sections, including table labels and combined headings."""
import re

from app.domain.services.languages import language_level, language_name

HEADINGS = {
    "combined": r"certificaci[oó]n(?:es)?\s+(?:e|y)\s+idiomas",
    "summary": r"perfil\s+profesional|resumen(?:\s+profesional)?|professional\s+(?:summary|profile)|career\s+(?:profile|objective)|sobre\s+m[ií]|acerca\s+de\s+m[ií]|personal\s+profile|summary|perfil",
    "projects": r"proyectos(?:\s+(?:acad[eé]micos|personales|destacados|profesionales))?|(?:academic\s+|personal\s+|selected\s+)?projects",
    "certificates": r"certificaciones(?:\s+y\s+cursos)?|certificaci[oó]n|certificados|cursos(?:\s+y\s+(?:certificaciones|diplomados))?|formaci[oó]n\s+(?:complementaria|continua)|certifications?|certificates|training(?:\s+and\s+certifications)?",
    "languages": r"idiomas|lenguas|languages?",
    "education": r"formaci[oó]n(?:\s+acad[eé]mica)?|educaci[oó]n|estudios(?:\s+realizados)?|academic\s+background|education",
    "experience": r"experiencia(?:\s+(?:laboral|profesional))?|(?:work|professional|employment)\s+(?:experience|history)|employment",
    "skills": r"competencias(?:\s+t[eé]cnicas)?|habilidades(?:\s+t[eé]cnicas)?|conocimientos|technical\s+skills|skills|tecnolog[ií]as",
    "other": r"referencias(?:\s+personales|\s+laborales)?|references|contacto|contact|datos\s+personales",
}
HEADER = re.compile(r"^\s*(?:#{1,6}\s*)?(?:" + "|".join(f"(?P<{key}>{pattern})" for key, pattern in HEADINGS.items()) + r")(?=\s|:|\||$)[ \t:|]*", re.I)
LANGUAGE = r"espa[nñ]ol|ingl[eé]s|english|spanish|franc[eé]s|french|portugu[eê]s|portuguese|alem[aá]n|german|italiano|italian|mandar[ií]n|chino|japon[eé]s|japanese"


def sections(text):
    result, current = {}, None
    for line in text.splitlines():
        if line.strip() in {"PYPDF FALLBACK", "COORDINATE EXPERIENCE LAYOUT"}:
            current = None
            continue
        match = HEADER.match(line)
        if match:
            current = match.lastgroup
            line = line[match.end():]
        if current and line.strip():
            result.setdefault(current, []).append(line.strip())
    return {key: "\n".join(lines) for key, lines in result.items()}


def languages(text):
    found = {}
    pattern = re.compile(rf"\b({LANGUAGE})\b\s*[:|\-–—]?\s*(?:nivel\s*[:\-]?\s*)?(A1|A2|B1|B2|C1|C2|NATIVE|nativ[oa])\b", re.I)
    for match in pattern.finditer(text):
        name, level = language_name(match[1]), language_level(match[2])
        found.setdefault(name, {"name": name, "level": level})
    return list(found.values())


def certifications(block):
    rows = []
    for line in block.splitlines():
        line = re.sub(r"^[•▪●*\-]+\s*", "", line).strip()
        if len(line) < 5 or re.match(rf"^(?:{LANGUAGE})\b", line, re.I):
            continue
        parts = [part.strip() for part in re.split(r"\s*[|·]\s*|\s+[—–]\s+", line) if part.strip()]
        if not parts:
            continue
        year = re.search(r"\b(?:19|20)\d{2}\b", line)
        name = re.sub(r"\s*[-–—,]?\s*(?:en\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)?\s*(?:de\s+)?(?:19|20)\d{2}\s*$", "", parts[0], flags=re.I).strip()
        issuer = next((part for part in parts[1:] if not re.search(r"\b(?:19|20)\d{2}\b", part) and not re.match(rf"(?:{LANGUAGE})\b", part, re.I)), "No especificado")
        if len(name) >= 4:
            rows.append({"name": name[:180], "issuer": issuer[:180], "year": year[0] if year else "", "kind": "certificate" if re.search(r"certifi|certified|\bSFC\b", line, re.I) else "course"})
    return rows[:40]


def projects(block):
    rows, current = [], None
    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            continue
        label = re.match(r"^(.{2,120}?)\s*[|·–—]\s*((?:proyecto|project).*)$", line, re.I)
        named = re.match(r"^(?:proyecto|project)\s*:\s*(.{2,120})$", line, re.I)
        heading = not re.match(r"^[•▪●*\-]", line) and len(line) <= 100 and line.isupper() and not line.endswith(".")
        if label or named or heading or current is None:
            title = label[1] if label else named[1] if named else line
            current = {"title": title[:160], "description": label[2] if label else "", "url": None}
            rows.append(current)
        else:
            current["description"] = (current["description"] + "\n" + re.sub(r"^[•▪●*\-]+\s*", "", line)).strip()[:2000]
        link = re.search(r"(?:https?://|www\.)[^\s<>]+|\b[a-z0-9][a-z0-9.-]+\.(?:app|com|dev|co|io)(?:/[^\s<>]*)?", line, re.I)
        if link:
            url = link[0].rstrip(".,;)")
            current["url"] = url if url.startswith(("https://", "http://")) else "https://" + url
    return [row for row in rows if len(row["title"]) >= 2 and row["description"]][:20]


def extract_sections(text):
    sources = re.split(r"\n\s*(?:PYPDF FALLBACK|COORDINATE EXPERIENCE LAYOUT)\s*\n", text)
    variants = [sections(source) for source in sources]
    summaries = [" ".join(block.get("summary", "").split()) for block in variants if block.get("summary")]
    # The coordinate reconstruction is a separate reading order, not a second
    # paragraph to append. Prefer the bounded section over a sidebar spilling
    # employment/education into the native text's last heading.
    summary = min(summaries, key=len) if summaries else ""
    project_sets = [projects(block.get("projects", "")) for block in variants]
    selected_projects = max(project_sets, key=lambda rows: sum(len(row["description"]) for row in rows), default=[])
    return {"summary": summary[:3000],
            "certifications": [row for block in variants for row in certifications(block.get("certificates", "") + "\n" + block.get("combined", ""))],
            "languages": languages(text), "projects": list({row["title"].casefold(): row for row in selected_projects}.values())}
