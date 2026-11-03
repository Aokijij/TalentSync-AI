import pytest
from test_api_flows import client, register  # noqa: F401

from app.domain.services.career_learning import EXERCISES
from app.domain.services.course_practices import course_practice
from app.domain.services.learning_catalog import LOCAL_RESOURCES
from app.infrastructure.database.models import LearningPlan


def preserve_legacy_plan(test_client, user_id, resource_id):
    # Emulate an existing plan saved before the internal catalog was retired.
    resource = next(row for row in LOCAL_RESOURCES if row["id"] == resource_id)
    with test_client.session_factory() as db:
        db.add(LearningPlan(user_id=user_id, resource_id=resource_id, status="in_progress", progress={"practice_spec": course_practice(resource)}))
        db.commit()


@pytest.mark.parametrize("area", list(EXERCISES))
def test_sector_practice_saves_resumes_and_publishes_profile_evidence(client, area):  # noqa: F811
    user, headers = register(client, f"journey-{area}", skills=[])
    preserve_legacy_plan(client, user["id"], f"practice-{area}-v1")
    resource = client.get("/api/v1/learning/plans", headers=headers).json()[0]["resource"]
    assert resource["journey"]["scenario"] and len(resource["journey"]["steps"]) == 3
    url = f"/api/v1/learning/plans/{resource['id']}"
    plan = client.put(url, headers=headers, json={"status": "in_progress"}).json()[0]
    answers = {step["id"]: "Una propuesta específica del caso, con responsables, hechos y resultado que puede revisarse." for step in resource["journey"]["steps"]}
    result = client.patch(url + "/journey", headers=headers, json={"version": plan["version"], "answers": answers})
    assert result.status_code == 200
    draft = client.get("/api/v1/learning/plans", headers=headers).json()[0]
    assert draft["progress"]["answers"] == answers and draft["version"] == plan["version"] + 1
    assert client.get("/api/v1/matching/evidence", headers=headers).json() == []
    payload = {"version": draft["version"], "answers": answers, "finish": True, "add_to_profile": True}
    published = client.patch(url + "/journey", headers=headers, json=payload)
    assert published.status_code == 200 and published.json()[0]["progress"]["published"]
    assert client.patch(url + "/journey", headers=headers, json=payload).status_code == 409
    evidence = client.get("/api/v1/matching/evidence", headers=headers).json()
    assert len(evidence) == 1 and evidence[0]["source"] == "learning_practice" and not evidence[0]["verified"]
    assert all(step["title"] in evidence[0]["description"] for step in resource["journey"]["steps"])
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    assert set(resource["skills"]) <= set(profile["skills"])
    assert client.get("/api/v1/learning/passport", headers=headers).json()["assessments"] == []
    # Updating the published work replaces its own reference instead of duplicating it.
    payload["version"] = published.json()[0]["version"]
    assert client.patch(url + "/journey", headers=headers, json=payload).status_code == 200
    assert len(client.get("/api/v1/matching/evidence", headers=headers).json()) == 1
    with client.session_factory() as db:
        assert db.query(LearningPlan).filter_by(user_id=user["id"]).count() == 1


def test_journey_rejects_incomplete_cross_user_and_stale_drafts(client):  # noqa: F811
    user, first = register(client, "journey-owner")
    _, other = register(client, "journey-other")
    preserve_legacy_plan(client, user["id"], "practice-sales-v1")
    url = "/api/v1/learning/plans/practice-sales-v1"
    plan = client.put(url, headers=first, json={"status": "in_progress"}).json()[0]
    payload = {"version": plan["version"], "answers": {"understand": "short"}, "finish": True}
    assert client.patch(url + "/journey", headers=first, json=payload).status_code == 422
    assert client.patch(url + "/journey", headers=other, json=payload).status_code == 404
    payload.update(finish=False, answers={"fake": "invalid"})
    assert client.patch(url + "/journey", headers=first, json=payload).status_code == 422
    payload["answers"] = {"understand": "partial draft"}
    assert client.patch(url + "/journey", headers=first, json=payload).status_code == 200
    assert client.patch(url + "/journey", headers=first, json=payload).status_code == 409
    assert client.get("/api/v1/matching/evidence", headers=first).json() == []


def test_revising_published_work_keeps_its_reference_until_candidate_removes_it(client):  # noqa: F811
    user, headers = register(client, "journey-revision", skills=[])
    preserve_legacy_plan(client, user["id"], "practice-sales-v1")
    url = "/api/v1/learning/plans/practice-sales-v1"
    plan = client.put(url, headers=headers, json={"status": "in_progress"}).json()[0]
    answers = {key: "Una propuesta completa con hechos del caso, una decisión justificada y un resultado observable." for key in ["understand", "apply", "demonstrate"]}
    published = client.patch(url + "/journey", headers=headers, json={"version": plan["version"], "answers": answers, "finish": True}).json()[0]
    assert client.get("/api/v1/profiles/me", headers=headers).json()["skills"] == []
    answers["apply"] += " Con una revisión adicional."
    draft = client.patch(url + "/journey", headers=headers, json={"version": published["version"], "answers": answers}).json()[0]
    assert draft["progress"]["published"] and draft["progress"]["has_unpublished_changes"]
    draft = client.patch(url + "/journey", headers=headers, json={"version": draft["version"], "answers": answers}).json()[0]
    assert draft["progress"]["has_unpublished_changes"]
    passport = client.get("/api/v1/learning/passport", headers=headers).json()
    assert len(passport["practice_evidence"]) == 1 and not passport["assessments"]
    evidence = client.get("/api/v1/matching/evidence", headers=headers).json()[0]
    assert "revisión adicional" not in evidence["description"]
    assert client.delete(f"/api/v1/matching/evidence/{evidence['id']}", headers=headers).status_code in {200, 204}
    assert client.get("/api/v1/learning/passport", headers=headers).json()["practice_evidence"] == []
    assert not client.get("/api/v1/learning/plans", headers=headers).json()[0]["progress"]["published"]
