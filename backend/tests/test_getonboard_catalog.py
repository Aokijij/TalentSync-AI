import json
from datetime import datetime
from types import SimpleNamespace

from app.domain.services.external_job_content import extract_content
from app.infrastructure.job_catalogs.getonboard import GetOnBoardCatalog


def row(**changes):
    return {"id": "analyst-test", "links": {"public_url": "https://www.getonbrd.com/jobs/analyst-test"}, "attributes": {
        "title": "Analista de datos", "countries": ["Colombia"], "remote": True,
        "company": {"data": {"attributes": {"name": "Empresa de prueba"}}},
        "functions": "<p>Construir reportes y documentar controles de calidad de datos para el equipo comercial.</p>",
        "description": "<p>Experiencia con Python y SQL para análisis de información.</p>",
        "tags": {"data": [{"attributes": {"name": "Python"}}, {"attributes": {"name": "SQL"}}]},
        "published_at": 1793700000, **changes}}


def test_source_preserves_published_sections_tags_and_date_without_inventing_salary():
    job = GetOnBoardCatalog.map_job(row())
    assert job.company == "Empresa de prueba" and job.skills == ("Python", "SQL")
    assert "Funciones y responsabilidades\nConstruir reportes" in job.description
    assert "Requisitos\nExperiencia con Python" in job.description
    assert isinstance(job.published_at, datetime) and job.salary == ""
    content, _, _, _ = extract_content(job.title, job.description, job.requirements)
    assert content["admission"]["clarity_passed"]


def test_remote_alone_does_not_imply_colombian_eligibility():
    assert not GetOnBoardCatalog.colombia_eligible(row(countries=["Remote"], remote_zone=None))
    assert GetOnBoardCatalog.colombia_eligible(row(countries=["Remote"], remote_zone="latam"))
    assert GetOnBoardCatalog.colombia_eligible(row(countries=["Remote"], location_regions={"data": [{"id": "south_america"}]}))
    assert not GetOnBoardCatalog.colombia_eligible(row(countries=["Remote"], location_regions={"data": [{"id": "europe"}]}))


def test_search_sends_documented_expand_and_excludes_unknown_remote_eligibility():
    class HTTP:
        def get(self, url):
            assert "expand=%5B%22company%22" in url and "query=Colombia" in url
            return SimpleNamespace(status=200, body=json.dumps({"data": [row(), row(countries=["Remote"])], "meta": {"total_pages": 2}}).encode())
    assert len(GetOnBoardCatalog(HTTP()).search().jobs) == 1
