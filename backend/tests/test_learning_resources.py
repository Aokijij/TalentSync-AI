# ruff: noqa: F811
import pytest
from test_account_security import browser, login  # noqa: F401
from test_api_flows import client, company_account, create_job, register  # noqa: F401
from test_ecosystem import administrator

from app.infrastructure.database.models import EventLog, LearningResource


def content(**changes):
    return {"title": "Curso de Python", "provider": "Catálogo revisado", "url": "https://education.example.com/python",
            "instructions": "Practica funciones, colecciones y manejo de errores.", "skills": ["Python"], "hours": 4, **changes}


def test_curated_courses_target_gaps_preserve_plans_and_never_grant_credit(client):
    admin = administrator(client)
    _, company = company_account(client)
    job = create_job(client, company)
    _, candidate = register(client, "catalog-learner", skills=["Java"])
    endpoint = "/api/v1/admin/learning/resources"
    response = client.post(endpoint, headers=admin, json=content())
    assert response.status_code == 201, response.text
    course = next(row for row in response.json() if row["provider"] == "Catálogo revisado")
    assert course["skills"] == ["python"] and course["assessment_ids"] == ["python-foundations-v1"]
    recommendations = client.get(f"/api/v1/learning/jobs/{job['id']}", headers=candidate).json()["resources"]
    assert course["id"] in {row["id"] for row in recommendations}
    client.put(f"/api/v1/learning/plans/{course['id']}", headers=candidate, json={"status": "completed"}).raise_for_status()
    assert client.get("/api/v1/profiles/me", headers=candidate).json()["skills"] == ["java"]
    assert client.get("/api/v1/learning/passport", headers=candidate).json()["assessments"] == []
    change = content(version=course["version"], active=False)
    assert client.put(f"{endpoint}/{course['id']}", headers=admin, json=change).status_code == 200
    assert client.put(f"{endpoint}/{course['id']}", headers=admin, json=change).status_code == 409
    assert course["id"] not in {row["id"] for row in client.get("/api/v1/learning/catalog", headers=candidate).json()["resources"]}
    plans = client.get("/api/v1/learning/plans", headers=candidate).json()
    assert plans[0]["resource"]["active"] is False and plans[0]["status"] == "completed"
    _, other = register(client, "new-catalog-learner")
    assert client.put(f"/api/v1/learning/plans/{course['id']}", headers=other, json={"status": "in_progress"}).status_code == 404
    with client.session_factory() as db:
        events = db.query(EventLog).filter_by(event_type="learning.catalog_updated").all()
        assert len(events) == 2 and all(set(row.details) == {"source", "status"} for row in events)


@pytest.mark.parametrize("changes", [
    {"url": "http://education.example.com/course"}, {"url": "https://127.0.0.1/course"},
    {"url": "https://user:secret@example.com/course"}, {"url": "https://courses.local/course"},
    {"sponsored": True}, {"affiliate": True}, {"hours": 0}, {"instructions": "           "},
])
def test_invalid_links_and_undisclosed_commercial_resources_are_rejected(client, changes):
    admin = administrator(client)
    assert client.post("/api/v1/admin/learning/resources", headers=admin, json=content(**changes)).status_code == 422


def test_import_is_atomic_bounded_and_commercial_status_does_not_change_ranking(client):
    admin = administrator(client)
    _, company = company_account(client)
    job = create_job(client, company)
    _, candidate = register(client, "ranking-learner", skills=["Java"])
    endpoint = "/api/v1/admin/learning/resources/import"
    assert client.post(endpoint, headers=admin, json={"resources": [content(), content(url="invalid")]}).status_code == 422
    with client.session_factory() as db:
        assert db.query(LearningResource).count() == 0
    response = client.post(endpoint, headers=admin, json={"resources": [content(), content(title="Curso anunciado", sponsored=True, affiliate=True, disclosure="La plataforma puede recibir una comisión por esta compra.")]})
    assert response.status_code == 201
    recommendations = client.get(f"/api/v1/learning/jobs/{job['id']}", headers=candidate).json()["resources"]
    courses = [row for row in recommendations if row["provider"] == "Catálogo revisado"]
    assert len(courses) == 2
    assert courses[0]["estimated_gain"] == courses[1]["estimated_gain"]
    assert [row["id"] for row in courses] == sorted(row["id"] for row in courses)
    assert client.post(endpoint, headers=admin, json={"resources": [content()] * 51}).status_code == 422


def test_catalog_management_is_admin_only_and_browser_writes_require_csrf(browser):
    register(browser, "alex")
    login(browser)
    assert browser.get("/api/v1/admin/learning/resources").status_code == 403
    assert browser.post("/api/v1/admin/learning/resources", json=content()).status_code == 403
    assert browser.get("/api/v1/learning/catalog").status_code == 200
