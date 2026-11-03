"""Evidence of a specific advertised job, never a 200-status link checker."""
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit
from urllib.robotparser import RobotFileParser

from app.infrastructure.public_http import PublicHTTP, PublicHTTPError, public_url


@dataclass(frozen=True)
class Availability:
    state: str  # verified, closed, unknown, unavailable
    reason: str
    valid_until: datetime | None = None
    posting: dict | None = None


def ats_reference(url):
    parsed = urlsplit(public_url(url))
    parts = parsed.path.strip("/").split("/")
    host = parsed.hostname
    if host in {"boards.greenhouse.io", "job-boards.greenhouse.io"} and len(parts) == 3 and parts[1] == "jobs" and re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", parts[0]) and parts[2].isdigit():
        return "greenhouse", parts[0], parts[2]
    if host in {"jobs.lever.co", "jobs.eu.lever.co"} and len(parts) >= 2 and re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", parts[0]) and re.fullmatch(r"[a-fA-F0-9-]{32,36}", parts[1]):
        return "lever_eu" if host == "jobs.eu.lever.co" else "lever", parts[0], parts[1]
    return None


class StructuredJobs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reading, self.current, self.documents = False, [], []
        self.canonical = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "link" and attributes.get("rel", "").casefold() == "canonical":
            self.canonical = attributes.get("href")
        if tag == "script":
            self.reading = dict(attrs).get("type", "").lower() == "application/ld+json"
            self.current = []

    def handle_data(self, value):
        if self.reading:
            self.current.append(value)

    def handle_endtag(self, tag):
        if tag == "script" and self.reading:
            try:
                self.documents.append(json.loads("".join(self.current)))
            except (ValueError, RecursionError):
                pass
            self.reading = False


def postings(value, depth=0):
    if depth > 12:
        return
    if isinstance(value, list):
        for row in value:
            yield from postings(row, depth + 1)
    elif isinstance(value, dict):
        types = value.get("@type", [])
        if types == "JobPosting" or isinstance(types, list) and "JobPosting" in types:
            yield value
        yield from postings(value.get("@graph", []), depth + 1)


def _identity(url):
    parsed = urlsplit(public_url(url))
    # Query IDs matter; only discard known tracking parameters.
    query = tuple(sorted((k, tuple(v)) for k, v in parse_qs(parsed.query).items() if not k.startswith("utm_") and k not in {"source", "ref", "gh_src"}))
    return parsed.hostname, parsed.path.rstrip("/"), query


class JobAvailability:
    def __init__(self, http=None):
        self.http = http or PublicHTTP(max_bytes=3_000_000)

    def check(self, url, *, now=None):
        now = now or datetime.utcnow()
        try:
            url = public_url(url)
            reference = ats_reference(url)
            if reference:
                provider, board, job_id = reference
                endpoint = (f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}" if provider == "greenhouse" else
                            f"https://api{'.eu' if provider == 'lever_eu' else ''}.lever.co/v0/postings/{board}/{job_id}?mode=json")
                response = self.http.get(endpoint)
                expected, actual = urlsplit(endpoint), urlsplit(response.url)
                if (actual.hostname, actual.path.rstrip("/")) != (expected.hostname, expected.path.rstrip("/")):
                    return Availability("unknown", "redirected")
                if response.status in {404, 410}:
                    return Availability("closed", "source_removed")
                if response.status != 200:
                    return Availability("unavailable", "source_unavailable")
                value = json.loads(response.body)
                if not isinstance(value, dict) or str(value.get("id")) != job_id:
                    return Availability("unknown", "unconfirmed")
                if not value.get("title" if provider == "greenhouse" else "text"):
                    return Availability("unknown", "unconfirmed")
                return Availability("verified", "source_api", posting=value)
            parsed = urlsplit(url)
            if parsed.hostname in {"www.getonbrd.com", "getonbrd.com"} and re.fullmatch(r"/jobs/[a-zA-Z0-9_-]+", parsed.path):
                slug = parsed.path.rsplit("/", 1)[-1]
                response = self.http.get("https://www.getonbrd.com/api/v0/jobs/" + slug)
                if response.status in {404, 410}:
                    return Availability("closed", "source_removed")
                if response.status != 200:
                    return Availability("unavailable", "source_unavailable")
                posting = json.loads(response.body).get("data") or {}
                if posting.get("id") != slug or not (posting.get("attributes") or {}).get("title"):
                    return Availability("unknown", "unconfirmed")
                return Availability("verified", "source_api", posting=posting)
            robots = self.http.get(f"https://{parsed.netloc}/robots.txt")
            if robots.status == 200:
                rules = RobotFileParser()
                rules.parse(robots.body.decode("utf-8", errors="replace").splitlines())
                if not rules.can_fetch("TalentSyncCatalog", url):
                    return Availability("unknown", "robots_disallowed")
            elif robots.status not in {404, 410}:
                return Availability("unavailable", "source_unavailable")
            response = self.http.get(url)
            if response.status in {404, 410}:
                return Availability("closed", "source_removed")
            if response.status != 200:
                return Availability("unavailable", "source_unavailable")
            if "text/html" not in response.content_type:
                return Availability("unknown", "unconfirmed")
            # A redirect to a homepage/search page is not evidence about this job.
            if _identity(response.url) != _identity(url):
                return Availability("unknown", "redirected")
            parser = StructuredJobs()
            parser.feed(response.body.decode("utf-8", errors="replace"))
            documents = list(postings(parser.documents))
            # These original portals omit JobPosting.url. Only accept their exact
            # job-detail route, matching canonical URL, one posting and employer.
            canonical_portal = ((parsed.hostname == "www.magneto365.com" and re.fullmatch(r"/co/empleos/[^/]+-\d+", parsed.path)) or
                                (parsed.hostname == "www.elempleo.com" and re.fullmatch(r"/co/ofertas-trabajo/[^/]+-\d+", parsed.path)))
            for value in documents:
                explicit_identity = isinstance(value.get("url"), str) and _identity(value["url"]) == _identity(url)
                portal_identity = bool(canonical_portal and len(documents) == 1 and parser.canonical and
                                       _identity(parser.canonical) == _identity(url) and value.get("datePosted") and
                                       isinstance(value.get("hiringOrganization"), dict) and value["hiringOrganization"].get("name"))
                if not value.get("title") or not (explicit_identity or portal_identity):
                    continue
                expiry = value.get("validThrough")
                if not isinstance(expiry, str):
                    continue
                date = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                if date.tzinfo:
                    date = date.astimezone(timezone.utc).replace(tzinfo=None)
                # Date-only validity includes the advertised final day.
                if len(expiry) == 10:
                    date = date.replace(hour=23, minute=59, second=59)
                return Availability("verified" if date > now else "closed", "structured_date", date, value)
            return Availability("unknown", "unconfirmed")
        except (PublicHTTPError, ValueError, TypeError, RecursionError):
            return Availability("unavailable", "source_unavailable")
