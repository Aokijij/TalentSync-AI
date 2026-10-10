"""Bounded readers of public SENA/Sapiencia pages. No private APIs or student data."""
import copy
import json
import re
import secrets
import threading
import time
import unicodedata
from collections import OrderedDict
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from app.api.schemas.learning import ResourceContent
from app.application.errors import UseCaseError

SENA = "https://betowa.sena.edu.co"
SAPIENCIA = "https://sapiencia.gov.co"
AGENT = "TalentSyncCatalog/1.0"


def fold(text):
    return "".join(char for char in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(char))


class Node:
    def __init__(self, tag="root", attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def text(self):
        return " ".join(" ".join(child.text() if isinstance(child, Node) else child for child in self.children).split())

    def all(self, tag=None):
        for child in self.children:
            if isinstance(child, Node):
                if tag is None or child.tag == tag:
                    yield child
                yield from child.all(tag)


class PublicHTML(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root, self.stack, self.count = Node(), [], 0
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.count += 1
        if self.count > 40000 or len(self.stack) > 100:
            raise ValueError("HTML limit")
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if not any(node.tag in {"script", "style", "noscript"} for node in self.stack):
            self.stack[-1].children.append(data)


def sena_url(url):
    parsed = urlsplit(url)
    ids = parse_qs(parsed.query).get("programId", [])
    if (parsed.scheme != "https" or parsed.netloc != "betowa.sena.edu.co" or parsed.fragment
            or not re.fullmatch(r"/oferta/[a-z0-9-]{3,200}", parsed.path)
            or len(ids) != 1 or not re.fullmatch(r"[0-9]{1,12}", ids[0])):
        raise ValueError("Invalid SENA course URL")
    return f"{SENA}{parsed.path}?programId={ids[0]}&modality=V"


# Only explicit words in a title suggest skills; an administrator reviews the mapping.
MAPPINGS = [
    ("instrumentos de evaluacion", "education", ["evaluación educativa"]),
    ("excel", "administration", ["excel"]), ("office", "administration", ["ofimática"]),
    ("contab", "finance", ["contabilidad"]), ("financ", "finance", ["finanzas"]),
    ("inventari", "logistics", ["inventarios"]), ("logistic", "logistics", ["logística"]),
    ("cliente", "service", ["atención al cliente"]), ("ventas", "sales", ["ventas"]),
    ("marketing", "sales", ["marketing digital"]), ("mercadeo", "sales", ["mercadeo"]),
    ("document", "administration", ["gestión documental"]), ("administrat", "administration", ["gestión administrativa"]),
    ("salud", "care", ["promoción de la salud"]), ("alimento", "care", ["seguridad alimentaria"]),
    ("pedagog", "education", ["pedagogía"]), ("docen", "education", ["docencia"]),
    ("diseno", "design", ["diseño"]), ("programacion", "technology", ["programación"]),
    ("python", "technology", ["python"]), ("seguridad digital", "technology", ["ciberseguridad"]),
    ("english", "general", ["inglés"]), ("emprend", "general", ["emprendimiento"]),
]


def parse_sena_listing(html):
    root, rows, seen = PublicHTML(html).root, [], set()
    for article in root.all("article"):
        heading = next(article.all("h2"), None)
        link = next((a for a in article.all("a") if a.attrs.get("href", "").startswith("/oferta/")), None)
        if heading is None or link is None:
            continue
        try:
            url = sena_url(urljoin(SENA, link.attrs["href"]))
        except ValueError:
            continue
        if url in seen or not any(node.attrs.get("aria-label") == "Modalidad: Virtual" for node in article.all("output")):
            continue
        seen.add(url)
        hours = next((re.fullmatch(r"(\d+) horas", n.text()) for n in article.all("dd") if re.fullmatch(r"(\d+) horas", n.text())), None)
        age = next((re.search(r"Edad mínima: (\d+) años", n.attrs.get("aria-label", "")) for n in article.all() if "Edad mínima:" in n.attrs.get("aria-label", "")), None)
        title = heading.text()
        mapping = next((item for item in MAPPINGS if item[0] in fold(title)), None)
        if not hours or not mapping or not 0 < int(hours[1]) <= 1000:
            continue
        _, category, skills = mapping
        program = parse_qs(urlsplit(url).query)["programId"][0]
        content = ResourceContent(title=title[:160], provider="SENA", url=url, category=category, kind="course",
            instructions=f"Formación complementaria del SENA: {title.lower()}. Consulta el temario y los requisitos en la ficha oficial."[:2000],
            skills=skills, hours=int(hours[1]), cost="free", active=False,
            details={"languages": ["es", "en"] if "english" in fold(title) else ["es"], "prerequisites": "Revisa los requisitos específicos y completa el registro en el SENA.",
                     "access_notes": "Formación gratuita. La inscripción y asignación de cupo se realizan exclusivamente en el SENA.",
                     "certificate_cost": "conditional", "certificate_notes": "El SENA determina la aprobación y expedición del certificado. Una práctica de TalentSync no acredita haber cursado esta formación.",
                     "duration_notes": "Duración publicada por el SENA; comprueba el calendario de la ficha elegida.",
                     "enrollment": {"modality": "virtual", "minimum_age": int(age[1]) if age else None,
                                    "region": "Colombia · oferta virtual", "checked_on": date.today().isoformat(),
                                    "notes": "Programa localizado en el catálogo. Consulta cupos y fechas antes de inscribirte."}}).model_dump(mode="json")
        rows.append({"source_id": f"sena:{program}", "content": content,
                     "source": {"provider": "sena", "id": f"sena:{program}", "mode": "public_page",
                                "reference_url": url, "reviewed_at": date.today().isoformat(), "mapping": "title_rules_for_review"}})
    # An empty changed page must not silently replace a valid cache.
    if not rows and "resultados" not in fold(root.text()):
        raise ValueError("SENA page structure changed")
    return rows[:20]


def parse_sena_observation(html):
    root = PublicHTML(html).root
    title = next((n.text() for n in root.all("h1") if n.text() and fold(n.text()) != "betowa"), "")
    if not title:
        title = next((n.text() for n in root.all("h2") if "programa" not in fold(n.text()) and len(n.text()) > 12), "")
    text = fold(root.text())
    if not title or "requisitos para inscribirte" not in text:
        raise ValueError("SENA course structure changed")
    # Presence in a listing or schema.org InStock alone never proves a seat is available.
    offers = "cursos disponibles" in text and "codigo:" in text and "inscribirme" in text
    return {"title": title[:160], "status": "open" if offers else "unknown", "modality": "virtual",
            "checked_on": date.today().isoformat(), "unavailable": False,
            "notes": "La ficha muestra una opción de inscripción; el SENA confirma cupo, requisitos y fechas." if offers else "Confirma fechas y cupos en el SENA; no se pudo comprobar una opción de inscripción."}


def parse_sapiencia(html):
    root, rows = PublicHTML(html).root, []
    for node in root.all("a"):
        if "tarjeta" not in node.attrs.get("class", "").split():
            continue
        heading = next(node.all("h3"), None)
        title = heading.text() if heading else node.attrs.get("data-titulo", "")
        if not any(word in fold(title) for word in ("estud-ia", "estudia", "oracle", "medellinglish", "@medellin")):
            continue
        url = urljoin(SAPIENCIA, node.attrs.get("href", ""))
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc not in {"sapiencia.gov.co", "arrobamedellin.edu.co", "www.arrobamedellin.edu.co"}:
            continue
        state = fold(node.attrs.get("data-estado", ""))
        from hashlib import sha256
        rows.append({"id": f"sapiencia:{sha256(url.encode()).hexdigest()[:20]}", "title": title[:160], "url": url,
                     "provider": "Sapiencia", "status": "closed" if state == "cerrada" else "open" if state == "abierta" else "unknown",
                     "region": "Medellín · consulta los requisitos de residencia de cada convocatoria",
                     "summary": node.text().replace(title, "", 1).strip()[:1200],
                     "checked_on": date.today().isoformat(),
                     "notes": "Convocatoria o directorio de formación; no es un curso añadido al plan. Revisa elegibilidad, modalidad, fechas y cupos en la fuente."})
    if not rows:
        raise ValueError("Sapiencia page structure changed")
    return rows[:20]


class PublicLearningCatalog:
    def __init__(self, transport=None):
        self.transport, self.lock = transport, threading.Lock()
        self.previews = OrderedDict()
        self.robots = {}

    @staticmethod
    def _read(client, url, *, robots=False):
        with client.stream("GET", url, headers={"User-Agent": AGENT, "Accept": "text/plain" if robots else "text/html"}) as response:
            if response.status_code != 200:
                raise ValueError("Public source unavailable")
            if not robots and "text/html" not in response.headers.get("content-type", ""):
                raise ValueError("Unexpected source format")
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > (100_000 if robots else 2_000_000):
                    raise ValueError("Public source size limit")
            return body.decode("utf-8", errors="replace")

    def read(self, url):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc not in {"betowa.sena.edu.co", "sapiencia.gov.co"}:
            raise UseCaseError(status_code=422, detail="Fuente educativa no permitida")
        try:
            with httpx.Client(transport=self.transport, timeout=6, follow_redirects=False, trust_env=False) as client:
                with self.lock:
                    cached = self.robots.get(parsed.netloc)
                if not cached or cached[0] < time.monotonic():
                    policy = RobotFileParser()
                    policy.parse(self._read(client, f"https://{parsed.netloc}/robots.txt", robots=True).splitlines())
                    with self.lock:
                        self.robots[parsed.netloc] = (time.monotonic() + 3600, policy)
                else:
                    policy = cached[1]
                if not policy.can_fetch(AGENT, url):
                    raise ValueError("Source disallows automated reads")
                return self._read(client, url)
        except (httpx.HTTPError, ValueError, RecursionError):
            raise UseCaseError(status_code=503, detail="La fuente oficial no pudo consultarse. Conservamos la información anterior; intenta más tarde.") from None

    def search(self, query):
        url = f"{SENA}/oferta?{urlencode({'modality': 'V', 'search': query, 'page': 1, 'page_size': 20})}"
        try:
            rows = parse_sena_listing(self.read(url))
            tokens = [word[:6] for word in fold(query).split() if len(word) >= 3]
            return [row for row in rows if all(word in fold(row["content"]["title"]) for word in tokens)]
        except (ValueError, TypeError, KeyError, RecursionError):
            raise UseCaseError(status_code=503, detail="El formato público del SENA cambió; revisa su página oficial.") from None

    def opportunities(self):
        try:
            return parse_sapiencia(self.read(f"{SAPIENCIA}/convocatorias/"))
        except (ValueError, TypeError, KeyError, RecursionError):
            raise UseCaseError(status_code=503, detail="El formato de convocatorias cambió; revisa Sapiencia.") from None

    def observe(self, url):
        try:
            return parse_sena_observation(self.read(sena_url(url)))
        except (ValueError, TypeError, KeyError, RecursionError):
            raise UseCaseError(status_code=503, detail="No pudimos comprobar la inscripción en la ficha oficial del SENA.") from None

    def preview(self, rows, actor_id, **metadata):
        key = secrets.token_urlsafe(24)
        with self.lock:
            self.previews[key] = (time.monotonic() + 900, actor_id, copy.deepcopy(rows))
            while len(self.previews) > 32:
                self.previews.popitem(last=False)
        return {"preview_id": key, "resources": rows, "expires_in": 900, **metadata}

    def selected(self, key, ids, actor_id):
        with self.lock:
            entry = self.previews.get(key)
            if not entry or entry[0] < time.monotonic() or entry[1] != actor_id:
                raise UseCaseError(status_code=409, detail="La consulta venció; vuelve a consultar el SENA.")
            rows = [copy.deepcopy(row) for row in entry[2] if row["source_id"] in ids]
        if not ids or len(rows) != len(ids) or len(ids) != len(set(ids)):
            raise UseCaseError(status_code=422, detail="Selecciona programas distintos de esta consulta.")
        return rows


def snapshot_payload(value):
    """JSON round trip ensures snapshots never retain mutable provider-owned objects."""
    return json.loads(json.dumps(value, ensure_ascii=False))


def timestamp():
    return datetime.now(timezone.utc).isoformat()
