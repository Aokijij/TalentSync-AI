# ruff: noqa: F811
from datetime import date, datetime, timedelta

import httpx
import pytest
from pydantic import ValidationError
from test_api_flows import client, register  # noqa: F401
from test_ecosystem import administrator

from app.api.deps import get_public_learning_catalog
from app.api.schemas.learning import CourseEnrollment
from app.application.errors import UseCaseError
from app.application.use_cases import learning_sources
from app.application.use_cases.learning_resources import import_source
from app.domain.services.learning_availability import availability
from app.infrastructure.database.models import LearningResource, LearningSourceSnapshot
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.public_learning import (
    PublicLearningCatalog,
    parse_sapiencia,
    parse_sena_listing,
    parse_sena_observation,
    sena_url,
)

LISTING = '''<h1>Resultados de búsqueda</h1><article><a href="/oferta/excel-practico?search=excel&amp;programId=42&amp;modality=V">
<h2>EXCEL PRÁCTICO</h2><output aria-label="Modalidad: Virtual">Virtual</output>
<dl><dd>48 horas</dd><span aria-label="Edad mínima: 14 años">14+</span></dl></a></article>'''
DETAIL = '''<h1>Betowa</h1><h1>EXCEL PRÁCTICO</h1><h2>Requisitos para inscribirte</h2>
<h2>Cursos disponibles</h2><p>Código: 123</p><button>Inscribirme</button>'''
CALLS = '''<a class="tarjeta" href="https://sapiencia.gov.co/estudia-cursos/" data-estado="Cerrada">
<h3>Convocatoria Estud-IA Cursos Cortos</h3><p>Formación híbrida en Medellín.</p></a>
<a class="tarjeta" href="https://arrobamedellin.edu.co/" data-estado="Abierta"><h3>Convocatoria @medellin</h3><p>Inscripción permanente.</p></a>
<a class="tarjeta" href="https://evil.example/" data-estado="Abierta"><h3>Oracle</h3></a>
<a class="tarjeta" href="https://sapiencia.gov.co/metro/" data-estado="Abierta"><h3>Tiquete Metro</h3></a>'''


def gateway_with_pages():
    calls = []
    def handle(request):
        calls.append(str(request.url))
        body = "User-agent: *\nAllow: /" if request.url.path == "/robots.txt" else CALLS if request.url.host == "sapiencia.gov.co" else LISTING if request.url.path == "/oferta" else DETAIL
        return httpx.Response(200, text=body, headers={"Content-Type": "text/plain" if request.url.path == "/robots.txt" else "text/html"})
    return PublicLearningCatalog(httpx.MockTransport(handle)), calls


def test_parsers_use_visible_modality_keep_unknown_cupos_and_skip_untrusted_links():
    rows = parse_sena_listing(LISTING + LISTING)
    assert len(rows) == 1 and rows[0]["source_id"] == "sena:42"
    assert rows[0]["content"]["details"]["enrollment"]["status"] == "unknown"
    assert rows[0]["content"]["details"]["enrollment"]["minimum_age"] == 14
    assert rows[0]["content"]["skills"] == ["excel"]
    assert not parse_sena_listing(LISTING.replace("Modalidad: Virtual", "Modalidad: Presencial"))
    assert not parse_sena_listing(LISTING.replace("/oferta/excel-practico?", "https://evil.example/oferta/excel-practico?"))
    assert parse_sena_observation(DETAIL)["title"] == "EXCEL PRÁCTICO"
    assert parse_sena_observation(DETAIL)["status"] == "open"
    assert parse_sena_observation(DETAIL.replace("Código: 123", ""))["status"] == "unknown"
    calls = parse_sapiencia(CALLS)
    assert len(calls) == 2 and {row["status"] for row in calls} == {"open", "closed"}
    assert all("Medellín" in row["region"] for row in calls)
    assert parse_sapiencia(CALLS)[0]["id"] == calls[0]["id"]


@pytest.mark.parametrize("url", ["http://betowa.sena.edu.co/oferta/excel?programId=42", "https://betowa.sena.edu.co.evil.example/oferta/excel?programId=42", "https://user@betowa.sena.edu.co/oferta/excel?programId=42", "https://betowa.sena.edu.co/api/private?programId=42", "https://betowa.sena.edu.co/oferta/excel?programId=42&programId=43", "https://127.0.0.1/oferta/excel?programId=42"])
def test_sena_only_accepts_canonical_public_course_links(url):
    with pytest.raises(ValueError):
        sena_url(url)


def test_robot_policy_failures_and_redirects_do_not_fetch_a_second_host():
    seen = []
    def denied(request):
        seen.append(str(request.url))
        return httpx.Response(200, text="User-agent: *\nDisallow: /")
    with pytest.raises(UseCaseError):
        PublicLearningCatalog(httpx.MockTransport(denied)).search("excel")
    assert len(seen) == 1 and seen[0].endswith("/robots.txt")
    def redirected(request):
        seen.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(302, headers={"Location": "http://127.0.0.1/private"})
    with pytest.raises(UseCaseError):
        PublicLearningCatalog(httpx.MockTransport(redirected)).search("excel")
    assert all("127.0.0.1" not in url for url in seen)


def test_public_discovery_is_admin_only_cached_and_imports_idempotently(client):
    gateway, calls = gateway_with_pages()
    client.app.dependency_overrides[get_public_learning_catalog] = lambda: gateway
    admin = administrator(client)
    _, candidate = register(client, "public-learning-candidate", skills=["excel"])
    endpoint = "/api/v1/admin/learning/sources/sena"
    assert client.post(endpoint + "/preview", headers=candidate, json={"query": "excel"}).status_code == 403
    first = client.post(endpoint + "/preview", headers=admin, json={"query": "excel"})
    assert first.status_code == 200, first.text
    preview = first.json()
    again = client.post(endpoint + "/preview", headers=admin, json={"query": "excel"})
    assert again.status_code == 200 and len(calls) == 2
    payload = {"preview_id": preview["preview_id"], "ids": ["sena:42"], "publish": True}
    result = client.post(endpoint + "/import", headers=admin, json=payload)
    assert result.status_code == 200, result.text
    assert result.json()["created"] == 1
    repeat = client.post(endpoint + "/import", headers=admin, json=payload)
    assert repeat.json()["created"] == 0 and repeat.json()["existing"] == 1
    visible = client.get("/api/v1/learning/catalog?area=all", headers=candidate).json()["resources"]
    resource = next(row for row in visible if row.get("source", {}).get("id") == "sena:42")
    assert resource["availability"]["status"] == "unknown"
    before = len(calls)
    assert client.get("/api/v1/learning/opportunities", headers=candidate).json()["items"] == []
    assert len(calls) == before  # Candidate reads are strictly local.
    assert client.post(endpoint + "/import", headers=admin, json={**payload, "ids": ["sena:42", "sena:42"]}).status_code == 422


def test_public_previews_cannot_be_imported_by_another_actor_or_after_expiration():
    gateway, _ = gateway_with_pages()
    preview = gateway.preview(parse_sena_listing(LISTING), 1)
    with pytest.raises(UseCaseError):
        gateway.selected(preview["preview_id"], ["sena:42"], 2)
    expiry, actor, rows = gateway.previews[preview["preview_id"]]
    gateway.previews[preview["preview_id"]] = (0, actor, rows)
    with pytest.raises(UseCaseError):
        gateway.selected(preview["preview_id"], ["sena:42"], 1)


def test_refresh_preserves_editorial_content_and_handles_provider_outage(client):
    admin = administrator(client)
    gateway, calls = gateway_with_pages()
    client.app.dependency_overrides[get_public_learning_catalog] = lambda: gateway
    endpoint = "/api/v1/admin/learning/sources"
    p = client.post(endpoint + "/sena/preview", headers=admin, json={"query": "excel"}).json()
    client.post(endpoint + "/sena/import", headers=admin, json={"preview_id": p["preview_id"], "ids": ["sena:42"], "publish": True}).raise_for_status()
    with client.session_factory() as session:
        course = session.query(LearningResource).one()
        course.content = {**course.content, "title": "Nombre editado", "skills": ["excel", "contabilidad"]}
        session.commit()
    r = client.post(endpoint + "/public/refresh", headers=admin, json={"provider": "sena"})
    assert r.status_code == 200 and r.json()["checked"] == 1
    with client.session_factory() as session:
        course = session.query(LearningResource).one()
        assert course.content["title"] == "Nombre editado" and course.content["skills"] == ["excel", "contabilidad"]
        assert course.content["source"]["observation"]["status"] == "open"
        for snapshot in session.query(LearningSourceSnapshot).all():
            snapshot.fetched_at = snapshot.attempted_at = datetime.utcnow() - timedelta(days=2)
        session.commit()
        def fail():
            raise UseCaseError(status_code=503, detail="Source temporarily unavailable")
        db = SqlAlchemyUnitOfWork(session)
        key = next(row.id for row in session.query(LearningSourceSnapshot).all() if row.id.startswith("sena-course:"))
        data, snapshot = learning_sources.cached(db, key, fail, force=True)
        assert data["status"] == "open" and snapshot.error
    client.post(endpoint + "/public/refresh", headers=admin, json={"provider": "sapiencia"}).raise_for_status()
    _, candidate = register(client, "local-calls-reader", skills=["excel"])
    count = len(calls)
    saved = client.get("/api/v1/learning/opportunities", headers=candidate).json()
    assert len(saved["items"]) == 2 and saved["fetched_at"]
    assert len(calls) == count


def test_enrollment_expires_and_requires_realistic_dates():
    today = date.today()
    base = {"status": "open", "checked_on": today.isoformat()}
    assert availability({"details": {"enrollment": base}})["status"] == "open"
    assert availability({"details": {"enrollment": {**base, "checked_on": (today - timedelta(days=15)).isoformat()}}})["status"] == "unknown"
    assert availability({"details": {"enrollment": base}, "source": {"observation": {"unavailable": True}}})["status"] == "unknown"
    assert availability({"details": {"enrollment": {**base, "closes_on": (today - timedelta(days=1)).isoformat()}}})["status"] == "closed"
    with pytest.raises(ValidationError):
        CourseEnrollment(status="open")
    with pytest.raises(ValidationError):
        CourseEnrollment(opens_on="2026-12-01", closes_on="2026-01-01")
    with pytest.raises(ValidationError):
        CourseEnrollment(minimum_age=-1)


def test_live_source_does_not_duplicate_a_previously_reviewed_editorial_course(client):
    administrator(client)
    with client.session_factory() as session:
        from app.domain.entities.enums import UserRole
        from app.infrastructure.database.models import User
        actor = session.query(User).filter_by(role=UserRole.ADMIN).first()
        db = SqlAlchemyUnitOfWork(session)
        rows = parse_sena_listing(LISTING)
        first = import_source(db, actor, rows, namespace="curated", publish=True)
        second = import_source(db, actor, rows, namespace="sena", publish=True)
        assert first["created"] == 1 and second["created"] == 0 and second["existing"] == 1
        assert session.query(LearningResource).count() == 1


def test_first_provider_failure_is_persisted_and_retries_are_bounded(client):
    administrator(client)
    calls = []
    def fail():
        calls.append(1)
        raise UseCaseError(status_code=503, detail="Unavailable")
    with client.session_factory() as session:
        db = SqlAlchemyUnitOfWork(session)
        with pytest.raises(UseCaseError):
            learning_sources.cached(db, "sapiencia", fail)
        content, state = learning_sources.cached(db, "sapiencia", fail, force=True)
        assert content == [] and state.error and len(calls) == 1
