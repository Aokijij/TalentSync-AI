import json

from app.domain.services.external_sources import (
    clean_external_location,
    external_portal,
)
from app.infrastructure.job_catalogs import adzuna, jsearch


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, size=-1) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_jsearch_maps_full_description_and_structured_skills(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["key"] = request.headers["X-api-key"]
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "data": {
                    "jobs": [{
                        "job_id": "real-101",
                        "job_title": "Analista de información - $3.200.000",
                        "employer_name": "Empresa real",
                        "job_location": "Bogotá, Colombia",
                        "job_description": "Descripción completa de la oportunidad.",
                        "job_employment_type": "FULLTIME",
                        "job_apply_link": "https://example.com/jobs/real-101",
                        "job_posted_at_datetime_utc": "2026-09-20T10:00:00Z",
                        "required_technologies": ["Excel", "Power BI", "SQL"],
                        "preferred_technologies": ["Python"],
                        "job_benefits_strings": ["health_insurance"],
                        "job_highlights": {
                            "Qualifications": ["Experiencia analizando información."]
                        },
                        "work_arrangement": "remote",
                    }]
                },
            }
        )

    monkeypatch.setattr(jsearch, "urlopen", fake_urlopen)
    catalog = jsearch.JSearchJobCatalog(api_key="private-key")
    result = catalog.search(
        keywords="analista", location="Colombia", page=1, result_count=20
    )

    assert "country=co" in captured["url"]
    assert captured["key"] == "private-key"
    assert captured["timeout"] == 25
    assert result.jobs[0].skills == ("excel", "power bi", "sql", "python")
    assert result.jobs[0].title == "Analista de información"
    assert result.jobs[0].salary == "3200000"
    assert result.jobs[0].remote is True
    assert result.jobs[0].published_at.year == 2026
    assert result.jobs[0].requirements == "• Experiencia analizando información."


def test_adzuna_requires_both_credentials_and_maps_results(monkeypatch):
    def fake_urlopen(request, timeout):
        assert "max_days_old=60" in request.full_url
        return FakeResponse(
            {
                "count": 1,
                "results": [
                    {
                        "id": "adz-1",
                        "title": "Customer success specialist",
                        "company": {"display_name": "Remote Company"},
                        "location": {"display_name": "United States"},
                        "description": "Customer support and account management.",
                        "created": "2026-09-25T08:00:00Z",
                        "redirect_url": "https://example.com/adz-1",
                        "contract_time": "full_time",
                        "salary_min": 40000,
                        "salary_max": 50000,
                    }
                ],
            }
        )

    monkeypatch.setattr(adzuna, "urlopen", fake_urlopen)
    assert not adzuna.AdzunaJobCatalog(app_id=None, app_key="key").configured
    catalog = adzuna.AdzunaJobCatalog(app_id="id", app_key="key")
    result = catalog.search(
        keywords="customer success", location="remote", page=1, result_count=20
    )

    assert result.total == 1
    assert result.jobs[0].company == "Remote Company"
    assert result.jobs[0].salary == "40000-50000"


def test_external_portal_and_relative_publication_are_user_facing():
    item = {
        "job_id": "portal-1",
        "job_title": "Analista de servicio",
        "employer_name": "Empresa",
        "job_location": "Bogotá • a través de Computrabajo",
        "job_description": "Atención al cliente y comunicación con usuarios.",
        "job_apply_link": "https://co.computrabajo.com/ofertas/portal-1",
        "job_posted_at": "2 weeks ago",
    }
    mapped = jsearch.JSearchJobCatalog(api_key="key")._map_job(item)

    assert mapped.location == "Bogotá"
    assert 13 <= (jsearch.datetime.utcnow() - mapped.published_at).days <= 14
    assert external_portal(mapped.url, mapped.location) == "Computrabajo"
    assert clean_external_location("Medellín • a través de LinkedIn") == "Medellín"


def test_jsearch_uses_the_cursor_and_stops_without_spending_on_empty_pages(monkeypatch):
    calls = []
    def request(req, timeout):
        calls.append(req.full_url)
        return FakeResponse({"data": {"jobs": [], "cursor": "next-token" if len(calls) == 1 else None}})
    monkeypatch.setattr(jsearch, "urlopen", request)
    catalog = jsearch.JSearchJobCatalog(api_key="private-key")
    for page in (1, 2, 3):
        catalog.search(keywords="analista", location="Colombia", page=page, result_count=10)
    assert len(calls) == 2
    assert "cursor=next-token" in calls[1]
    assert "num_pages=1" in calls[0]


def test_jsearch_prefers_original_ats_and_never_labels_foreign_salary_as_cop():
    catalog = jsearch.JSearchJobCatalog(api_key="private-key")
    item = {"job_id": "one", "job_title": "Engineer", "job_min_salary": 100000,
            "job_salary_period": "YEAR", "job_salary_currency": "USD",
            "job_apply_link": "https://aggregator.example/jobs/one", "apply_options": [
                {"apply_link": "https://aggregator.example/jobs/one"},
                {"apply_link": "https://job-boards.greenhouse.io/company/jobs/123", "is_direct": True}]}
    job = catalog._map_job(item)
    assert job.url == "https://job-boards.greenhouse.io/company/jobs/123"
    assert job.salary == ""
    item["job_salary_currency"] = "COP"
    item["job_min_salary"] = 60000000
    assert catalog._map_job(item).salary == "5000000"


def test_jsearch_never_sends_key_to_an_alternate_host():
    import pytest

    from app.application.errors import CatalogProviderError
    catalog = jsearch.JSearchJobCatalog(api_key="private-key", base_url="https://other.example/search")
    with pytest.raises(CatalogProviderError):
        catalog.search(keywords="analista", location="Colombia", page=1, result_count=10)


def test_listing_url_identity_ignores_tracking_but_preserves_job_ids():
    from app.application.use_cases.job_imports import listing_url_identity
    assert listing_url_identity("https://example.com/jobs/123?utm_source=one#apply") == listing_url_identity("https://example.com/jobs/123/?utm_source=two")
    assert listing_url_identity("https://example.com/job?id=123") != listing_url_identity("https://example.com/job?id=124")


def test_ats_monthly_salary_requires_explicit_cop_and_period():
    from app.infrastructure.job_catalogs.ats import monthly_cop
    assert monthly_cop("Salario base de $2.100.000 COP mensuales.") == "2100000"
    assert monthly_cop("COP 2,800,000 monthly salary") == "2800000"
    assert monthly_cop("The salary is $2,800 - $6,000 per month in USD") == ""
    assert monthly_cop("Un auxilio de 300,000 y salario competitivo") == ""


def test_live_ats_keeps_its_old_publication_date_without_expiring_on_import():
    from datetime import datetime

    from app.application.use_cases.job_imports import _catalog_row
    from app.domain.entities.catalog import CatalogJob
    from app.infrastructure.job_catalogs.ats import published_date

    date = published_date({"first_published": "2025-01-01T10:00:00-05:00"}, "greenhouse")
    assert date == datetime(2025, 1, 1, 15)
    job = CatalogJob(external_id="old-open", title="Analista", company="Empresa", location="Colombia",
                     description="Una oferta antigua aún publicada en su fuente original.", employment_type="",
                     salary="", url="https://example.org/jobs/123", published_at=date)
    row = _catalog_row(job, source_name="Greenhouse", max_age_days=30)
    assert row["fecha_publicacion"] == date
    assert row["fecha_vencimiento"] > datetime.utcnow()
