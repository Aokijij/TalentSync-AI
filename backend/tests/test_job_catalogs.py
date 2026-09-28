import json

from app.infrastructure.job_catalogs import adzuna, jsearch


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_jsearch_maps_full_description_and_structured_skills(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["key"] = request.headers["X-api-key"]
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "data": [
                    {
                        "job_id": "real-101",
                        "job_title": "Analista de información",
                        "employer_name": "Empresa real",
                        "job_location": "Bogotá, Colombia",
                        "job_description": "Descripción completa de la oportunidad.",
                        "job_employment_type": "FULLTIME",
                        "job_apply_link": "https://example.com/jobs/real-101",
                        "job_posted_at_datetime_utc": "2026-09-20T10:00:00Z",
                        "required_technologies": ["Excel", "Power BI", "SQL"],
                        "preferred_technologies": ["Python"],
                        "job_benefits": ["health_insurance"],
                        "work_arrangement": "remote",
                    }
                ]
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
    assert result.jobs[0].remote is True
    assert result.jobs[0].published_at.year == 2026


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
