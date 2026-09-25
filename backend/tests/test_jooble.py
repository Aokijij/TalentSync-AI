import json

from app.infrastructure.job_catalogs import jooble


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_jooble_catalog_maps_and_cleans_authorized_results(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "totalCount": 1,
                "jobs": [
                    {
                        "id": 123,
                        "title": "Asesor de servicio",
                        "company": "Empresa aliada",
                        "location": "Bogotá, Bogotá D.C.",
                        "snippet": "<b>Atiende</b> solicitudes de clientes.",
                        "type": "Full-time",
                        "salary": "$2.500.000 - $3.000.000 al mes",
                        "link": "https://co.jooble.org/jdp/123",
                        "updated": "2026-09-23T12:55:35.3870000",
                    }
                ],
            }
        )

    monkeypatch.setattr(jooble, "urlopen", fake_urlopen)
    catalog = jooble.JoobleJobCatalog(
        api_key="regional-key", base_url="https://co.jooble.org/api", timeout_seconds=7
    )
    result = catalog.search(
        keywords="servicio al cliente", location="Colombia", page=2, result_count=20
    )

    assert captured["url"] == "https://co.jooble.org/api/regional-key"
    assert captured["body"]["page"] == 2
    assert captured["body"]["ResultOnPage"] == 20
    assert captured["timeout"] == 7
    assert result.total == 1
    assert result.jobs[0].description == "Atiende solicitudes de clientes."
    assert result.jobs[0].salary == "$2.500.000 - $3.000.000 al mes"
    assert result.jobs[0].published_at.microsecond == 387000
