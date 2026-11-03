# ruff: noqa: F811
import json
import socket
from datetime import datetime

import pytest
from external_fixtures import clear_content, clear_description
from test_api_flows import client, register  # noqa: F401
from test_ecosystem import administrator

from app.application.use_cases.job_availability import check_job
from app.infrastructure.database.models import Company, Job
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.job_availability import Availability, JobAvailability
from app.infrastructure.job_catalogs.ats import EmployerBoardCatalog, board_reference
from app.infrastructure.public_http import (
    PublicHTTP,
    PublicHTTPError,
    PublicResponse,
    public_url,
)

NOW = datetime(2026, 10, 29, 15)
URL = "https://careers.example.com/jobs/123"


class HTTP:
    def __init__(self, *, status=200, html="", payload=None, final=None, robots=""):
        self.status, self.html, self.payload, self.final, self.robots = status, html, payload, final, robots
        self.calls = []

    def get(self, url):
        self.calls.append(url)
        if url.endswith("robots.txt"):
            return PublicResponse(200, url, self.robots.encode(), "text/plain")
        body = json.dumps(self.payload).encode() if self.payload is not None else self.html.encode()
        return PublicResponse(self.status, self.final or url, body, "application/json" if self.payload is not None else "text/html")


def structured(**values):
    return '<script type="application/ld+json">' + json.dumps({"@type": "JobPosting", "title": "Analista", "url": URL, **values}) + "</script>"


def test_200_or_redirect_is_not_proof_of_an_active_listing():
    assert JobAvailability(HTTP(html="Welcome to our careers site")).check(URL, now=NOW).state == "unknown"
    assert JobAvailability(HTTP(html=structured(validThrough="2026-11-01"), final="https://careers.example.com/")).check(URL, now=NOW).state == "unknown"
    assert JobAvailability(HTTP(html=structured(url="https://careers.example.com/jobs/other", validThrough="2026-11-01"))).check(URL, now=NOW).state == "unknown"


@pytest.mark.parametrize("expiry,state", [("2026-11-01", "verified"), ("2026-10-28", "closed"), ("2026-10-29", "verified")])
def test_original_structured_expiry_identifies_this_specific_offer(expiry, state):
    assert JobAvailability(HTTP(html=structured(validThrough=expiry))).check(URL, now=NOW).state == state


@pytest.mark.parametrize("status,state", [(403, "unavailable"), (429, "unavailable"), (500, "unavailable"), (404, "closed"), (410, "closed")])
def test_provider_failure_is_not_misrepresented_as_closed(status, state):
    assert JobAvailability(HTTP(status=status)).check(URL, now=NOW).state == state


def test_robots_disallow_prevents_access_to_listing():
    http = HTTP(robots="User-agent: *\nDisallow: /jobs/")
    assert JobAvailability(http).check(URL, now=NOW).reason == "robots_disallowed"
    assert len(http.calls) == 1


def test_native_ats_checks_use_exact_fixed_endpoint_and_job_id():
    http = HTTP(payload={"id": 123, "title": "Analista"})
    result = JobAvailability(http).check("https://job-boards.greenhouse.io/acme/jobs/123")
    assert result.state == "verified"
    assert http.calls == ["https://boards-api.greenhouse.io/v1/boards/acme/jobs/123"]
    assert JobAvailability(HTTP(payload={"id": 999, "title": "Other"})).check("https://boards.greenhouse.io/acme/jobs/123").state == "unknown"
    assert JobAvailability(HTTP(payload={"id": 123, "title": "Analista"}, final="https://another.example/job")).check("https://boards.greenhouse.io/acme/jobs/123").state == "unknown"


def test_ashby_checks_exact_listed_identity_and_never_infers_colombia_from_remote():
    identifier = "12345678-1234-1234-1234-123456789abc"
    url = f"https://jobs.ashbyhq.com/acme/{identifier}"
    posting = {"id": identifier, "title": "Analista", "jobUrl": url, "isListed": True,
               "location": "Remote", "isRemote": True, "workplaceType": "Remote", "employmentType": "FullTime",
               "publishedAt": "2026-11-01T12:00:00Z", "descriptionHtml": "<h2>What you will do</h2><p>Analyze data and prepare useful reports for the finance team and business users.</p><h2>What we’re looking for</h2><p>Professional experience with SQL, Python and Excel for preparing business reports.</p>"}
    http = HTTP(payload={"jobs": [posting]})
    assert JobAvailability(http).check(url).state == "verified"
    assert http.calls == ["https://api.ashbyhq.com/posting-api/job-board/acme"]
    assert JobAvailability(HTTP(payload={"jobs": [{**posting, "isListed": False}]})).check(url).state == "closed"
    catalog = EmployerBoardCatalog("https://jobs.ashbyhq.com/acme", http)
    assert catalog.preview(location="Colombia")[0] == []
    posting["address"] = {"postalAddress": {"addressCountry": "CO"}}
    jobs, _ = catalog.preview(location="Colombia")
    assert len(jobs) == 1 and jobs[0].employment_type == "full_time"
    from app.domain.services.external_job_content import extract_content
    content, _, _, _ = extract_content(jobs[0].title, jobs[0].description)
    assert content["admission"]["clarity_passed"]


@pytest.mark.parametrize("url", ["http://example.com/job", "https://user:pass@example.com/job", "https://example.com:8080/job", "https://metadata.google.internal/job", "https://example.com\\@127.0.0.1/job"])
def test_public_url_rejects_unsafe_destinations(url):
    with pytest.raises(ValueError):
        public_url(url)


@pytest.mark.parametrize("address", ["127.0.0.1", "10.0.0.2", "169.254.169.254", "::1", "::ffff:127.0.0.1"])
def test_dns_is_checked_before_connecting_and_private_or_mixed_answers_fail(monkeypatch, address):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **kw: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)), (socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))])
    monkeypatch.setattr(socket, "create_connection", lambda *a, **kw: pytest.fail("Must not open a connection"))
    with pytest.raises(PublicHTTPError):
        PublicHTTP().get(URL)


def test_employer_board_preserves_location_and_rejects_other_boards():
    http = HTTP(payload={"jobs": [
        {"id": 123, "title": "Python", "location": {"name": "Colombia"}, "content": "<p>Python y SQL</p>", "absolute_url": "https://boards.greenhouse.io/acme/jobs/123"},
        {"id": 124, "title": "Python", "location": {"name": "Remote US"}, "content": "Python", "absolute_url": "https://boards.greenhouse.io/acme/jobs/124"},
        {"id": 125, "title": "Python", "location": {"name": "Colombia"}, "content": "Python", "absolute_url": "https://boards.greenhouse.io/other/jobs/125"},
    ]})
    jobs, count = EmployerBoardCatalog("https://boards.greenhouse.io/acme", http).preview(keywords="Python", location="Colombia")
    assert count == 3 and len(jobs) == 1 and jobs[0].location == "Colombia"
    assert "<p>" not in jobs[0].description
    with pytest.raises(ValueError):
        board_reference("https://boards.greenhouse.io/acme/jobs/123")


@pytest.mark.parametrize("url", ["https://www.magneto365.com/co/empleos/analista-123", "https://www.elempleo.com/co/ofertas-trabajo/analista-123"])
def test_colombian_original_portals_require_exact_canonical_and_unique_posting(url):
    payload = {"@type": "JobPosting", "title": "Analista", "datePosted": "2026-10-28",
               "validThrough": "2026-11-15", "hiringOrganization": {"name": "Empresa"}}
    html = '<link rel="canonical" href="' + url + '"><script type="application/ld+json">' + json.dumps(payload) + '</script>'
    result = JobAvailability(HTTP(html=html)).check(url, now=NOW)
    assert result.state == "verified" and result.posting["title"] == "Analista"
    assert JobAvailability(HTTP(html=html.replace(url, "https://www.magneto365.com/co/empleos/other-124"))).check(url, now=NOW).state == "unknown"
    assert JobAvailability(HTTP(html=html + '<script type="application/ld+json">' + json.dumps(payload) + '</script>')).check(url, now=NOW).state == "unknown"
    assert JobAvailability(HTTP(html=html.replace("2026-11-15", "2026-10-01"))).check(url, now=NOW).state == "closed"


def test_external_jobs_hidden_until_verified_and_failed_checks_never_close_them(client):
    user, headers = register(client, "freshness-candidate")
    with client.session_factory() as session:
        company = Company(owner_user_id=user["id"], name="External", nit="EXT-test", is_external=True)
        session.add(company); session.flush()
        job = Job(company_id=company.id, title="Analista", description=clear_description("Análisis de información"), requirements="Python y SQL", external_content=clear_content(), source_kind="external", external_url=URL, skills=["python", "sql", "excel"], external_published_at=datetime.utcnow(), status="active")
        session.add(job); session.commit()
        job_id = job.id
    assert client.get("/api/v1/jobs", headers=headers).json() == []
    class Gateway:
        def check(self, url, now=None):
            return Availability("verified", "source_api")
    with client.session_factory() as session:
        db = SqlAlchemyUnitOfWork(session)
        check_job(db, session.get(Job, job_id), Gateway())
    assert len(client.get("/api/v1/jobs", headers=headers).json()) == 1
    class Failure:
        def check(self, url, now=None):
            return Availability("unavailable", "source_unavailable")
    with client.session_factory() as session:
        db = SqlAlchemyUnitOfWork(session)
        job = session.get(Job, job_id)
        check_job(db, job, Failure())
        assert job.status == "active" and job.external_verified_at
    assert client.get("/api/v1/jobs", headers=headers).json() == []
    assert client.post(f"/api/v1/jobs/{job_id}/external-access", headers=headers).status_code == 409
    # Candidates cannot trigger unrestricted bulk probes.
    assert client.post("/api/v1/admin/jobs/availability/check", headers=headers).status_code == 403


def test_public_board_preview_does_not_import_and_import_requires_authorized_selection(client, monkeypatch):
    admin = administrator(client)
    _, candidate = register(client, "board-viewer")
    monkeypatch.setattr(EmployerBoardCatalog, "preview", lambda self, **kw: ([], 0))
    payload = {"board_url": "https://jobs.lever.co/acme"}
    response = client.post("/api/v1/admin/jobs/sources/ats/preview", headers=admin, json=payload)
    assert response.status_code == 200 and response.json()["items"] == []
    with client.session_factory() as session:
        assert session.query(Job).count() == 0
    assert client.post("/api/v1/admin/jobs/sources/ats/preview", headers=candidate, json=payload).status_code == 403
    assert client.post("/api/v1/admin/jobs/sources/ats/import", headers=admin, json=payload).status_code == 422


def test_selected_native_board_import_is_refetched_and_confirmed(client, monkeypatch):
    from app.domain.entities.catalog import CatalogJob
    admin = administrator(client)
    job = CatalogJob(external_id="123", title="Analista Python SQL", company="acme", location="Colombia", description=clear_description("Análisis de datos con Python, Excel y SQL para productos digitales."), employment_type="full_time", salary="", url="https://boards.greenhouse.io/acme/jobs/123", published_at=datetime.utcnow())
    calls = []
    def preview(self, **kwargs):
        calls.append(kwargs)
        return [job], 1
    monkeypatch.setattr(EmployerBoardCatalog, "preview", preview)
    payload = {"board_url": "https://boards.greenhouse.io/acme", "selected_ids": ["123"], "authorized": True}
    response = client.post("/api/v1/admin/jobs/sources/ats/import", headers=admin, json=payload)
    assert response.status_code == 200, response.text
    assert len(calls) == 1 and response.json()["created"] == 1
    visible = client.get("/api/v1/jobs").json()
    assert len(visible) == 1 and visible[0]["external_available"] and visible[0]["external_check_state"] == "verified"
    payload["selected_ids"] = ["missing"]
    assert client.post("/api/v1/admin/jobs/sources/ats/import", headers=admin, json=payload).status_code == 409
