# ruff: noqa: F811
from urllib.parse import urlsplit

import pytest
from pydantic import ValidationError
from test_api_flows import client, register  # noqa: F401
from test_ecosystem import administrator

from app.api.schemas.learning import ResourceContent
from app.infrastructure import curated_learning
from app.infrastructure.database.models import EventLog, LearningResource

ENDPOINT = "/api/v1/admin/learning/sources/curated"


def test_official_portfolio_is_diverse_validated_and_defensively_copied():
    catalog = curated_learning.catalog()
    assert len(catalog["resources"]) >= 30 and len(catalog["providers"]) >= 10
    assert len({row["source_id"] for row in catalog["resources"]}) == len(catalog["resources"])
    assert len({row["content"]["url"] for row in catalog["resources"]}) == len(catalog["resources"])
    assert {row["content"]["cost"] for row in catalog["resources"]} == {"free", "paid"}
    assert {"technology", "sales", "administration", "logistics", "finance", "general", "design", "education", "service"} <= {row["content"]["category"] for row in catalog["resources"]}
    for row in catalog["resources"]:
        content = ResourceContent(**row["content"])
        assert content.details.syllabus and content.details.languages
        assert content.details.portfolio_idea and content.details.access_notes and content.details.certificate_notes
        assert content.details.duration_notes and urlsplit(content.url).scheme == "https"
        assert row["source"]["mode"] == "editorial" and row["source"]["reference_url"] == content.url
        assert not content.sponsored and not content.affiliate
    catalog["resources"][0]["content"]["title"] = "MUTATED"
    assert curated_learning.catalog()["resources"][0]["content"]["title"] != "MUTATED"


def test_import_defaults_to_drafts_and_publishes_only_new_selected_resources(client):
    admin = administrator(client)
    _, candidate = register(client, "education-candidate", skills=["Java"])
    assert client.get(ENDPOINT, headers=candidate).status_code == 403
    source = client.get(ENDPOINT, headers=admin).json()
    first, second = source["resources"][:2]
    payload = {"revision": source["revision"], "ids": [first["source_id"]]}
    assert client.post(ENDPOINT + "/import", headers=candidate, json=payload).status_code == 403
    result = client.post(ENDPOINT + "/import", headers=admin, json=payload)
    assert result.status_code == 200, result.text
    assert result.json()["created"] == 1
    first_course = next(row for row in result.json()["resources"] if row.get("source", {}).get("id") == first["source_id"])
    assert not first_course["active"] and first_course["details"] == first["content"]["details"]
    before_publish = client.get("/api/v1/learning/catalog?area=all", headers=candidate).json()["resources"]
    assert "microsoft-data-analytics" in {row["id"] for row in before_publish}
    assert all("_published_once" not in row for row in result.json()["resources"])
    second_result = client.post(ENDPOINT + "/import", headers=admin, json={**payload, "ids": [first["source_id"], second["source_id"]], "publish": True})
    assert second_result.status_code == 200 and second_result.json()["created"] == 1 and second_result.json()["existing"] == 1
    visible = client.get("/api/v1/learning/catalog?area=all", headers=candidate).json()["resources"]
    assert first_course["id"] not in {row["id"] for row in visible}
    published = next(row for row in visible if row.get("source", {}).get("id") == second["source_id"])
    assert published["active"] and published["journey"] and published["details"]["syllabus"]
    # Completing a local plan does not issue a provider credential or change skills.
    client.put(f"/api/v1/learning/plans/{published['id']}", headers=candidate, json={"status": "completed"}).raise_for_status()
    assert client.get("/api/v1/profiles/me", headers=candidate).json()["skills"] == ["java"]
    assert client.get("/api/v1/learning/passport", headers=candidate).json()["assessments"] == []
    with client.session_factory() as db:
        events = db.query(EventLog).filter_by(event_type="learning.catalog_updated").all()
        assert len(events) == 2 and all(set(row.details) == {"source", "status"} for row in events)


def test_reimport_preserves_edits_archive_rich_details_and_existing_plans(client):
    admin = administrator(client)
    _, candidate = register(client, "preserved-education", skills=["python"])
    catalog = curated_learning.catalog()
    selected = catalog["resources"][0]
    payload = {"revision": catalog["revision"], "ids": [selected["source_id"]], "publish": True}
    result = client.post(ENDPOINT + "/import", headers=admin, json=payload).json()
    course = next(row for row in result["resources"] if row.get("source", {}).get("id") == selected["source_id"])
    client.put(f"/api/v1/learning/plans/{course['id']}", headers=candidate, json={"status": "in_progress"}).raise_for_status()
    edit = {**selected["content"], "version": course["version"], "active": False, "title": "Título revisado por la administración"}
    del edit["details"]  # Older editors must retain the richer metadata.
    updated = client.put(f"/api/v1/admin/learning/resources/{course['id']}", headers=admin, json=edit)
    assert updated.status_code == 200, updated.text
    repeated = client.post(ENDPOINT + "/import", headers=admin, json=payload).json()
    assert repeated["created"] == 0 and repeated["existing"] == 1
    kept = next(row for row in repeated["resources"] if row["id"] == course["id"])
    assert not kept["active"] and kept["title"] == edit["title"]
    assert kept["details"] == course["details"] and kept["source"] == course["source"]
    assert client.get("/api/v1/learning/plans", headers=candidate).json()[0]["resource"]["id"] == course["id"]


def test_import_replaces_legacy_reference_cards_without_losing_their_plans(client):
    admin = administrator(client)
    _, candidate = register(client, "legacy-course-plan", skills=["ventas"])
    legacy_id = "hubspot-inbound-sales"
    client.put(f"/api/v1/learning/plans/{legacy_id}", headers=candidate, json={"status": "in_progress"}).raise_for_status()
    catalog = curated_learning.catalog()
    source = next(row for row in catalog["resources"] if row["source_id"] == "hubspot:sales")
    imported = client.post(ENDPOINT + "/import", headers=admin, json={"revision": catalog["revision"], "ids": [source["source_id"]], "publish": True}).json()
    course = next(row for row in imported["resources"] if row.get("source", {}).get("id") == source["source_id"])
    visible = client.get("/api/v1/learning/catalog?area=all", headers=candidate).json()["resources"]
    assert len([row for row in visible if row.get("url") == source["content"]["url"]]) == 1
    old_plan = client.get("/api/v1/learning/plans", headers=candidate).json()[0]
    assert old_plan["resource"]["id"] == legacy_id and old_plan["resource"]["active"] is False
    edit = {**source["content"], "version": course["version"], "active": False}
    client.put(f"/api/v1/admin/learning/resources/{course['id']}", headers=admin, json=edit).raise_for_status()
    visible = client.get("/api/v1/learning/catalog?area=all", headers=candidate).json()["resources"]
    assert not any(row.get("url") == source["content"]["url"] for row in visible)
    assert client.get("/api/v1/learning/plans", headers=candidate).json()[0]["resource"]["id"] == legacy_id


@pytest.mark.parametrize("changes,status", [({"revision": "0" * 24}, 409), ({"ids": ["unknown"]}, 422), ({"ids": []}, 422), ({"ids": ["microsoft:data-analytics"] * 2}, 422), ({"ids": ["x"] * 51}, 422)])
def test_invalid_import_is_atomic(client, changes, status):
    admin = administrator(client)
    source = curated_learning.catalog()
    payload = {"revision": source["revision"], "ids": [source["resources"][0]["source_id"]], **changes}
    response = client.post(ENDPOINT + "/import", headers=admin, json=payload)
    assert response.status_code == status, response.text
    with client.session_factory() as db:
        assert db.query(LearningResource).count() == 0


@pytest.mark.parametrize("details", [{"level": "expert"}, {"syllabus": ["valid"] * 13}, {"languages": ["x"]}, {"certificate_cost": "guaranteed"}, {"surprise": True}])
def test_rich_course_metadata_has_bounded_strict_schema(details):
    row = curated_learning.catalog()["resources"][0]["content"]
    with pytest.raises(ValidationError):
        ResourceContent(**{**row, "details": details})
