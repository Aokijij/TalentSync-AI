# ruff: noqa: F811
from copy import deepcopy

import pytest
from test_api_flows import client, register  # noqa: F401
from test_ecosystem import administrator
from test_learning_resources import content

from app.domain.services.course_practices import (
    TOPICS,
    course_practice,
    practice_for_plan,
    public_practice,
)
from app.domain.services.learning_activities import activities_for, evaluate
from app.infrastructure.database.models import LearningPlan, LearningResource


def course(**changes):
    return {"id": "imported-example", "title": "Limpiar y transformar datos en Power BI", "url": "https://learn.microsoft.com/training/modules/example/",
            "skills": ["power bi", "power query"], "category": "technology", "kind": "course", "hours": 1,
            "details": {"level": "beginner", "syllabus": ["Tipos de columna", "Quitar duplicados"]}, **changes}


def test_practice_requires_explicit_reviewed_association_instead_of_inferred_subject():
    assert course_practice(course()) is None
    binding = {"mode": "template", "template_id": "excel", "level": "beginner", "rationale": "El temario revisado desarrolla fórmulas y referencias."}
    practice = course_practice(course(title="Curso de Python", practice=binding))
    assert practice["adaptation"]["topic"] == "excel"
    assert "Referencia absoluta" in practice["activities"][2]["terms"]
    assert practice["binding"]["rationale"] == binding["rationale"]

@pytest.mark.parametrize("topic", TOPICS, ids=[row[0] for row in TOPICS])
@pytest.mark.parametrize("level", ["beginner", "intermediate", "advanced"])
def test_adaptive_tasks_are_solvable_and_never_publish_answers(topic, level):
    practice = course_practice(course(title=topic[1][0].rstrip("*"), hours=8, details={"level": level}), topic_id=topic[0])
    for item in practice["activities"]:
        assert evaluate(item, item["answer"])
    public = public_practice(practice)
    assert all("answer" not in item and "feedback" not in item for item in public["activities"])
    assert practice["activities"][0]["answer"] != list(range(len(practice["activities"][0]["choices"])))


def test_legacy_saved_answers_keep_their_original_questions():
    source = course()
    progress = {"activity_answers": {"calculation": "7"}}
    practice = practice_for_plan(source, progress)
    assert practice["activities"] == activities_for("technology")
    snapshot = course_practice(source, topic_id="data-cleaning")
    progress = {"practice_spec": snapshot}
    changed = course(title="Azure Firewall", hours=8, details={"level": "advanced"})
    assert practice_for_plan(changed, progress) == snapshot
    # Serialization and presentation must not mutate the stored answers.
    public_practice(practice_for_plan(changed, progress))
    assert progress["practice_spec"] == snapshot


def test_plan_pins_private_tasks_across_editorial_changes_and_grades_that_snapshot(client):
    admin = administrator(client)
    _, candidate = register(client, "adaptive-plan", skills=[])
    response = client.post("/api/v1/admin/learning/resources", headers=admin, json=content(title="Curso Excel", hours=1, details={"level": "beginner"}, practice={"mode": "template", "template_id": "excel", "level": "beginner", "rationale": "El temario revisado trabaja fórmulas y hojas de cálculo."}))
    assert response.status_code == 201, response.text
    source = next(row for row in response.json() if row["title"] == "Curso Excel")
    base = f"/api/v1/learning/plans/{source['id']}"
    created = client.put(base, headers=candidate, json={}).json()[0]
    assert created["resource"]["journey"]["adaptation"]["topic"] == "excel"
    assert "practice_spec" not in created["progress"]
    assert all("answer" not in item and "feedback" not in item for item in created["resource"]["journey"]["activities"])
    with client.session_factory() as db:
        row = db.query(LearningPlan).filter_by(resource_id=source["id"]).one()
        snapshot = deepcopy(row.progress["practice_spec"])
        source_row = db.get(LearningResource, source["id"])
        source_row.content = {**source_row.content, "title": "Azure Firewall", "hours": 8, "details": {"level": "advanced"}, "practice": {"mode": "template", "template_id": "firewall", "level": "advanced", "rationale": "Se revisaron las actividades contra el nuevo temario."}}
        db.commit()
    refreshed = client.get("/api/v1/learning/plans", headers=candidate).json()[0]
    assert refreshed["resource"]["journey"]["activities"] == created["resource"]["journey"]["activities"]
    answers = {item["id"]: item["answer"] for item in snapshot["activities"]}
    result = client.patch(base + "/journey", headers=candidate, json={"version": refreshed["version"], "activity_answers": answers, "finish": True})
    assert result.status_code == 200, result.text
    assert result.json()[0]["progress"]["score"] == 100
    assert client.get("/api/v1/profiles/me", headers=candidate).json()["skills"] == []
    retried = client.patch(base + "/journey", headers=candidate, json={"version": result.json()[0]["version"], "retry": True})
    assert retried.status_code == 200
    assert retried.json()[0]["resource"]["journey"]["adaptation"]["topic"] == "firewall"
    assert "practice_spec" not in retried.json()[0]["progress"]
