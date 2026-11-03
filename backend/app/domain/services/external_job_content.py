"""Conservative extraction from job adverts. Missing facts remain missing."""
import calendar
import re
import unicodedata
from datetime import datetime
from html import unescape
from html.parser import HTMLParser

from app.domain.services.skills import normalize_skills

VERSION = 2
MIN_SKILLS = 3


def three_months_ago(now):
    month = now.year * 12 + now.month - 1 - 3
    year, zero_month = divmod(month, 12)
    return now.replace(year=year, month=zero_month + 1,
                       day=min(now.day, calendar.monthrange(year, zero_month + 1)[1]))


class SourceText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "iframe"}:
            self.hidden += 1
        if tag in {"p", "div", "section", "br", "h1", "h2", "h3", "h4", "ul", "ol"}:
            self.parts.append("\n")
        if tag == "li":
            self.parts.append("\n• ")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "iframe"}:
            self.hidden = max(0, self.hidden - 1)
        if tag in {"p", "div", "li", "section", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, text):
        if not self.hidden:
            self.parts.append(text)


def source_text(value):
    raw = unescape(str(value or ""))[:80_000]
    parser = SourceText()
    parser.feed(raw)
    text = "".join(parser.parts).replace("\r", "\n").replace("\xa0", " ")
    text = re.sub(r"[\t ]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"(?<=[a-záéíóúñ])\.(?=[A-ZÁÉÍÓÚÑ])", ".\n", text)
    text = re.sub(r"(?<=[a-záéíóúñ])(?=(?:Experiencia|Disponibilidad|Orientación|Control de|Trabajo en|Nivel de)\b)", "\n", text)
    text = re.sub(r"(?m)^\s*#{1,4}\s+|\*\*(?=\w)|(?<=\w)\*\*", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()[:40_000]


def distinct_external_skills(skills):
    variants = {"excel avanzado": "excel", "excel intermedio": "excel", "excel básico": "excel",
                "comunicación efectiva": "comunicación", "comunicación asertiva": "comunicación",
                "html5": "html", "css3": "css"}
    return normalize_skills([variants.get(str(skill).strip().lower(), str(skill).strip().lower()) for skill in skills or []])


def extract_external_skills(text, detected=()):
    patterns = {
        "comunicación": r"\b(?:communication|comunicacion)\b",
        "trabajo en equipo": r"\bteamwork\b|\bcross[- ]functional (?:teams|collaboration)\b|\btrabajo en equipo\b",
        "liderazgo": r"\bleadership\b|\bliderazgo\b|\blider(?:ar|ando) equipos\b",
        "contabilidad": r"\baccounting\b|\bcontabilidad\b",
        "conciliaciones bancarias": r"\bbank reconciliation|conciliacion(?:es)? bancaria",
        "cuentas por pagar": r"\baccounts payable\b|\bcuentas por pagar\b",
        "cuentas por cobrar": r"\baccounts receivable\b|\bcuentas por cobrar\b",
        "análisis financiero": r"financial analysis|analisis financiero",
        "reportes financieros": r"financial reporting|reportes financieros|estados financieros",
        "gestión de inventarios": r"inventory management|gestion de inventarios",
        "gestión de proyectos": r"project management|gestion de proyectos",
        "gestión de nómina": r"\bpayroll\b|gestion de nomina",
        "selección de personal": r"recruitment|talent acquisition|seleccion de personal",
        "seguridad y salud en el trabajo": r"occupational (?:health|safety)|seguridad y salud en el trabajo|\bsst\b",
        "control de calidad": r"quality control|control de calidad",
        "mantenimiento preventivo": r"preventive maintenance|mantenimiento preventivo",
        "atención al paciente": r"patient care|atencion al paciente",
        "administración de medicamentos": r"medication administration|administracion de medicamentos",
        "farmacovigilancia": r"\bfarmacovigilancia\b",
        "dispensación de medicamentos": r"\bdispensacion(?: de medicamentos)?\b",
        "legislación farmacéutica": r"\blegislacion farmaceutica\b",
        "preparación de alimentos": r"\bpreparacion de alimentos\b",
        "técnicas de cocina": r"\btecnicas (?:de cocina|culinarias)\b",
        "buenas prácticas de manufactura": r"\bbuenas practicas de manufactura\b",
        "gestión documental": r"document management|gestion documental",
        "negociación": r"\bnegotiation\b|\bnegociacion\b",
        "servicio al cliente": r"customer (?:service|support)|atencion al cliente|servicio al cliente",
        "ventas": r"\bsales\b|\bventas\b",
        "logística": r"\blogistics\b|\blogistica\b",
        "resolución de problemas": r"problem[- ]solving|resolucion de problemas|solucion de problemas",
        "documentación": r"\bdocumentation\b|\bdocumentacion\b",
    }
    normalized = folded(text)
    # Broad nouns in company introductions and perks are not skill evidence.
    # Prefer concrete competencies such as gestión administrativa or logística.
    ambiguous = {"bienestar", "evaluación", "administración", "operaciones", "indicadores", "producción", "distribución", "transporte"}
    detected = [skill for skill in detected if skill not in ambiguous]
    return distinct_external_skills([*detected, *(skill for skill, pattern in patterns.items() if re.search(pattern, normalized))])


def folded(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(c))


HEADINGS = (
    ("responsibilities", "Funciones y responsabilidades", r"funciones y responsabilidades|responsabilidades|(?:key |functional |your )?responsibilities(?: include(?: but are not limited to)?)?|funciones(?: del cargo| principales)?|objetivo del cargo|what you(?:'|’)?ll do|what you will do|what you(?:'|’)?ll own|what you own|your impact|your mission|que haras|tus funciones|el rol"),
    ("requirements", "Requisitos del cargo", r"requisitos(?: del cargo)?|requerimientos|requirements|qualifications|what you bring|your profile|what we look for|what we are looking for|who you are|must haves?|perfil(?: requerido)?|que necesitas|lo que buscamos|habilidades (?:requeridas|tecnicas|interpersonales)|otras habilidades|nivel (?:educativo|de educacion)|conocimientos"),
    ("preferred", "Conocimientos deseables", r"conocimientos deseables|habilidades publicadas|nice[- ]to[- ]haves?|preferred(?: knowledge and skills| qualifications| skills)?|deseables|requisitos deseables|sera un plus"),
    ("benefits", "Beneficios", r"beneficios|(?:our |company )?benefits|what we offer|lo que ofrecemos|que ofrecemos|what makes working at .+ awesome\??|why .+"),
    ("compensation", "Información salarial", r"compensation(?: and benefits)?|salario|salary|remuneracion|compensacion|pay range"),
    ("process", "Proceso de selección", r"interview process|hiring process|proceso de seleccion|proceso de contratacion|como postularte|how to apply"),
    ("conditions", "Condiciones de trabajo", r"condiciones(?: laborales)?|working conditions|work schedule|horario|jornada|working model|modalidad|ubicacion|location|where we work"),
    ("information", "Acerca de la oportunidad", r"about (?:the role|you|us|.+)|sobre (?:el cargo|nosotros|la empresa)|acerca de .+|descripcion(?: del cargo)?|the role|the opportunity|quienes somos|proposito del cargo|purpose of the role"),
)


def sections_for(text):
    # Recover common headings in old flattened imports without rewriting sentences.
    text = re.sub(r"(?im)[ \t]*sectores laborales\s*:.*$", "", text)
    markers = r"Requisitos|Requerimientos|Perfil|Conocimientos|Nivel educativo|Nivel de educación|Otras habilidades|Habilidades técnicas|Habilidades interpersonales|Responsabilidades|Funciones|Beneficios|Condiciones|Modalidad|Ubicación|Horario|Jornada|Salario|What You'll Do|What We Look For|Nice-to-Have|Interview Process|About the Role|Lo que ofrecemos"
    text = re.sub(r"(?<=[.!?:])\s+(?=(?:" + markers + r")\b)", "\n", text, flags=re.I)
    text = re.sub(r"\s+(?=(?:" + markers + r")\s*:)", "\n", text, flags=re.I)
    text = re.sub(r"(?is)\bpalabras clave\s*:\s*.*?(?=(?:\n\s*\n|[¡¿]|\b(?:responsabilidades|requisitos)\s*:))", "", text)
    sections, current = [], {"key": "information", "title": "Acerca de la oportunidad", "lines": []}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        found = None
        if not line.startswith("•"):
            for key, title, pattern in HEADINGS:
                heading = folded(line).strip("¿¡?! ")
                match = re.fullmatch(r"(?:" + pattern + r")\s*[:：]?\s*", heading) if len(line) <= 180 else None
                inline = re.match(r"^(?:" + pattern + r")\s*[:：]\s*(.+)$", heading) if 0 < line.find(":") < 100 else None
                if match or inline:
                    remainder = line.split(":", 1)[1].strip() if inline and ":" in line else ""
                    found = {"key": key, "title": title, "lines": [remainder] if remainder else []}
                    break
        if found:
            if current["lines"]:
                sections.append(current)
            current = found
        else:
            current["lines"].append(line)
    if current["lines"]:
        sections.append(current)
    return [{"key": s["key"], "title": s["title"], "text": "\n".join(s["lines"])} for s in sections][:35]


def academic_requirement(requirements):
    """Technical leadership and professional experience are not academic degrees."""
    from app.domain.services.professions import LEVEL_RANK, infer_study_fields
    clauses = requirements.splitlines()
    for line in clauses:
        line = re.split(r"(?i)\b(?:experiencia|conocimientos|matr[ií]cula|habilidades)\b", line, maxsplit=1)[0]
        t = folded(line)
        if re.search(r"no (?:university |college )?degree required|sin requisito (?:de formacion|academico)|no (?:se )?requiere (?:titulo|formacion)", t):
            return {"status": "not_required", "level": None, "fields": [], "excerpt": line[:600], "accepts_students": False}
    found = []
    for line in clauses:
        line = re.split(r"(?<=[a-záéíóúñ])(?=Experiencia|Conocimientos|Matrícula)|\.\s+(?=[A-Z])", line, maxsplit=1)[0]
        t = folded(line)
        levels = []
        for level, pattern in (("secondary", r"\bbachiller(?:ato)?\b|high school (?:diploma|degree)"),
                               ("technical", r"\btecnic[oa](?: profesional)?\b|technical (?:degree|diploma)"),
                               ("technologist", r"\btecnolog[oa]\b|tecnologia en"),
                               ("university", r"\b(?:bachelor(?:'s)?(?: degree)?|degree in|university degree|college degree|titulo universitario|profesional en|pregrado|formacion universitaria)\b"),
                               ("postgraduate", r"\b(?:master(?:'s)? degree|maestria|doctorado|ph\.?d|posgrado|especializacion en)\b")):
            if re.search(pattern, t):
                levels.append(level)
        if not levels:
            continue
        # A whole sentence about technical skills is not a technical diploma.
        if levels == ["technical"] and not re.search(r"formacion|estudio|titulo|nivel (?:de educacion|educativo|academico)|tecnic[oa] (?:profesional|en)|technical (?:degree|diploma)", t):
            continue
        optional = bool(re.search(r"deseable|preferible|preferred|nice to have|equivalent (?:work )?experience|experiencia equivalente", t))
        translations = {"computer science": "ciencias de la computación", "software engineering": "ingeniería de software", "data science": "ciencia de datos", "business administration": "administración de empresas", "human resources": "recursos humanos", "psychology": "psicología", "statistics": "estadística", "mathematics": "matemáticas", "civil engineering": "ingeniería civil", "electrical engineering": "ingeniería eléctrica", "nursing": "enfermería"}
        fields = infer_study_fields(line + " " + " ".join(value for key, value in translations.items() if key in t))
        found.append({"status": "alternative" if optional else "required", "level": min(levels, key=LEVEL_RANK.get), "fields": fields, "excerpt": line[:600], "accepts_students": bool(re.search(r"estudiant|en curso|cursando|in progress|currently studying", t))})
    if not found:
        return {"status": "unspecified", "level": None, "fields": [], "excerpt": "", "accepts_students": False}
    return next((item for item in found if item["status"] == "required"), found[0])


def clarity_reasons(content, details):
    sections = content.get("sections", [])
    functions = " ".join(s["text"] for s in sections if s["key"] == "responsibilities")
    requirements = " ".join(s["text"] for s in sections if s["key"] == "requirements")
    reasons = []
    if len(functions.strip()) < 60:
        reasons.append("responsibilities_unclear")
    if len(requirements.strip()) < 50:
        reasons.append("requirements_unclear")
    if details.get("experience_months") is None:
        reasons.append("experience_unspecified")
    if (content.get("education") or {}).get("status", "unspecified") == "unspecified":
        reasons.append("education_unspecified")
    return reasons


def extract_content(title, description, requirements="", *, published_at=None):
    description, requirements = source_text(description), source_text(requirements)
    display_description = description[len(title):].lstrip(" :.-\n") if description.casefold().startswith(title.casefold()) else description
    sections = sections_for(display_description)
    required = "\n\n".join(s["text"] for s in sections if s["key"] == "requirements")
    if requirements and not any(term in folded(requirements) for term in ("publica el detalle completo", "confirma la informacion directamente")):
        if not required:
            required = requirements
            if requirements not in description:
                sections.append({"key": "requirements", "title": "Requisitos del cargo", "text": required})
    relevant = "\n".join(s["text"] for s in sections if s["key"] in {"requirements", "responsibilities", "preferred"})
    evidence, details = {}, {}
    level_text = folded(title)
    levels = (("mid", r"\b(?:semi[- ]?senior|ssr\.?)\b"), ("lead", r"\b(?:lead|principal|head of|lider|director)\b"), ("senior", r"\b(?:senior|sr\.?)\b"),
              ("junior", r"\b(?:junior|jr\.?)\b"), ("entry", r"\b(?:intern(?:ship)?|practicante|pasante|entry level|sin experiencia)\b"),
              ("mid", r"\b(?:mid[- ]level|mid|intermedio|semi[- ]?senior|ssr\.?)\b"))
    for level, pattern in levels:
        if re.search(pattern, level_text):
            details["seniority"], evidence["seniority"] = level, title[:240]
            break
    requirement_lines = (required or relevant).splitlines()
    for line in requirement_lines:
        t = folded(line)
        numbers = {"un": "1", "uno": "1", "una": "1", "dos": "2", "tres": "3", "cuatro": "4", "cinco": "5", "seis": "6", "siete": "7", "ocho": "8", "nueve": "9", "diez": "10"}
        t = re.sub(r"\b(?:" + "|".join(numbers) + r")\b", lambda m: numbers[m[0]], t)
        if re.search(r"(?:no (?:prior )?experience required|sin experiencia|no requiere experiencia)", t):
            details["experience_months"], evidence["experience_months"] = 0, line[:240]
            break
        match = re.search(r"\b(\d{1,2})\s*(?:[-–a]|to)?\s*(?:\d{1,2})?\s*\+?\s*(anos?|years?|meses?|months?)\b", t)
        if match and re.search(r"experien|experiencia|trabaj|professional|proven", t):
            months = int(match[1]) * (12 if match[2].startswith(("ano", "year")) else 1)
            if months <= 600:
                details["experience_months"], evidence["experience_months"] = months, line[:240]
                break
    for line in description.splitlines():
        t = folded(line)
        for value, pattern in (("indefinite", r"(?:contrato (?:a termino )?indefinido|indefinite[- ]term contract)"),
                               ("fixed_term", r"contrato (?:a )?termino fijo|fixed[- ]term contract"),
                               ("services", r"contrato (?:por |de )?prestacion de servicios"),
                               ("apprenticeship", r"contrato de aprendizaje"),
                               ("project", r"contrato (?:por |de )?obra (?:o |y )?labor")):
            match = re.search(pattern, t)
            if match and "contract_type" not in details:
                details["contract_type"], evidence["contract_type"] = value, line[max(0, match.start() - 20):match.end() + 80][:240]
        if "schedule" not in details and re.search(r"horario|jornada|work schedule|lunes a viernes|monday (?:to|through) friday", t) and re.search(r"\d|turno|rotativ|flexible", t):
            start = re.search(r"horario|jornada|work schedule|lunes a viernes|monday (?:to|through) friday", t).start()
            snippet = re.split(r"[.!?]", line[start:])[0][:300]
            details["schedule"], evidence["schedule"] = snippet, snippet[:240]
    if not details.get("seniority"):
        for line in requirement_lines:
            match = re.search(r"(?:nivel|seniority|level)\s*[:：-]\s*(junior|senior|mid|intermedio|entry)", folded(line))
            if match:
                details["seniority"] = {"intermedio": "mid"}.get(match[1], match[1])
                evidence["seniority"] = line[:240]
                break
    summary = next((s["text"] for s in sections if s["key"] == "responsibilities"), sections[0]["text"] if sections else description)
    summary = " ".join(summary.replace("•", " ").split())[:650]
    academic = academic_requirement(required)
    if academic["accepts_students"]:
        details["education_accepts_in_progress"] = True
    salary_line = next((line for line in description.splitlines() if re.search(r"(?:salario|remuneracion)\s*:?\s*(?:(?:a|por) convenir|negociable|a acordar)|salary negotiable", folded(line))), "")
    content = {"version": VERSION, "sections": sections, "evidence": evidence, "summary": summary, "education": academic,
               "compensation": {"status": "negotiable" if salary_line else "unspecified", "statement": salary_line[:500]},
               "published_at": published_at.isoformat() + "Z" if published_at else None}
    reasons = clarity_reasons(content, details)
    blocking = [reason for reason in reasons if reason in {"responsibilities_unclear", "requirements_unclear"}]
    content["admission"] = {"clarity_passed": not blocking, "clarity_reasons": blocking, "information_gaps": [reason for reason in reasons if reason not in blocking], "policy": "source-facts-v3"}
    return content, details, required, (title + "\n" + (relevant or description))


def admission_reasons(published_at, skills, *, now=None):
    now = now or datetime.utcnow()
    reasons = publication_reasons(published_at, now=now)
    if len(distinct_external_skills(skills)) < MIN_SKILLS:
        reasons.append("insufficient_skills")
    return reasons


def publication_reasons(published_at, *, now):
    reasons = []
    if not published_at:
        reasons.append("publication_missing")
    elif published_at < three_months_ago(now):
        reasons.append("publication_too_old")
    elif published_at > now:
        reasons.append("publication_in_future")
    return reasons


def infer_external_sector(title, fallback):
    text = folded(title)
    rules = (
        ("Salud y bienestar", r"enfermer|medic[oa]|nurs|terapeuta|paciente|fisioter"),
        ("Farmaceutica y biotecnologia", r"farmac|biotecn|microbiolog|laboratorio clinico"),
        ("Agricultura y medio ambiente", r"agronom|agric|veterinar|ambiental"),
        ("Construccion e ingenieria", r"civil|arquitect|construccion|residente de obra"),
        ("Logistica y transporte", r"logistic|conductor|bodega|supply chain|almacen|transporte|inventario"),
        ("Manufactura", r"produccion|manufactur|mantenimiento|operario|industrial|electricista"),
        ("Turismo y hoteleria", r"hotel|turismo|cocina|mesero|recepcion|tourism"),
        ("Educacion", r"docente|profesor|teacher|pedagog|instructor"),
        ("Seguros", r"\bseguros?\b|insurance"),
        ("Seguridad y vigilancia", r"vigilante|guarda de seguridad"),
        ("Inteligencia artificial", r"\bai\b|machine learning|inteligencia artificial"),
        ("Analitica y ciencia de datos", r"data |datos|analytics|business intelligence"),
        ("Tecnologia y software", r"software|developer|desarroll|devops|\bqa\b|\bit\b|ciberseg|full.?stack|frontend|backend"),
        ("Recursos humanos", r"recruit|talent |people |human|payroll|nomina"),
        ("Legal", r"abogad|juridic|\blegal\b|compliance|cumplimiento"),
        ("Finanzas y banca", r"financ|accountant|accounting|contab|credit|fraud|tesorer|risk|kyc|cartera"),
        ("Marketing y publicidad", r"marketing|disen|graphic|creativ|programmatic|copywriter|comunicacion|publicidad"),
        ("BPO y contact center", r"customer|call center|contact center|atencion al cliente|servicio al cliente|cobranza"),
        ("Ventas y comercio", r"sales|venta|account executive|account manager|comercial|partnership|revenue"),
    )
    return next((sector for sector, pattern in rules if re.search(pattern, text)), fallback)
