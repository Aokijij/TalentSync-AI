# ruff: noqa: F811
from types import SimpleNamespace as Row

import pytest
from sqlalchemy import event
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.application.use_cases import matching, profiles
from app.domain.services.skill_context import CONTEXT_VERSION
from app.domain.services.skill_levels import inferred_skill_levels
from app.infrastructure.database.models import User
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.matching_gate import matching_slot


@pytest.mark.parametrize("text,expected", [
    ("Python avanzado, SQL básico", {"python": "advanced", "sql": "basic"}),
    ("Conocimientos avanzados de Python y manejo intermedio de SQL", {"python": "advanced", "sql": "intermediate"}),
    ("Python: nivel experto. SQL (intermedio)", {"python": "expert", "sql": "intermediate"}),
    ("Desarrollador senior con 10 años usando Python y SQL", {"python": "learning", "sql": "learning"}),
    ("CURSOS\nCurso avanzado de Python\nSQL avanzado", {"python": "learning", "sql": "learning"}),
    ("Estoy aprendiendo Python y SQL", {"python": "learning", "sql": "learning"}),
    ("No tengo conocimientos avanzados en Python. SQL básico", {"python": "learning", "sql": "basic"}),
])
def test_cv_levels_require_adjacent_explicit_context_and_default_to_learning(text, expected):
    assert {key: row["level"] for key, row in inferred_skill_levels(text, ["python", "sql"]).items()} == expected


def test_cv_import_keeps_manual_levels_and_records_uncertain_defaults(client):
    user, _ = register(client, "cv-level-import", skills=["python"])
    nlp = Row(analyze_cv=lambda _: Row(clean_text="texto", profession=None, skills=["python", "sql", "git"], experience=None, education=None, location=None, phone=None, experiences=[], educations=[], certifications=[], embedding=[1], skill_context=[]))
    with client.session_factory() as session:
        stored = session.get(User, user["id"])
        stored.profile.preferences = {"skill_levels": {"python": "expert"}}
        profile = profiles.upload_cv(None, stored, SqlAlchemyUnitOfWork(session), nlp=nlp, resumes=Row(extract=lambda *_: ("sample.pdf", "Python básico; SQL avanzado; Git")))
        assert profile.skill_levels == {"python": "expert", "sql": "advanced", "git": "learning"}
        assert profile.skill_level_sources["git"]["source"] == "default"
        assert profile.skill_level_sources["sql"]["source"] == "cv_explicit"


def test_discarded_mentions_can_be_deleted_without_removing_declared_skills(client):
    user, headers = register(client, "cv-remove-dismissed", skills=["python"])
    with client.session_factory() as session:
        session.get(User, user["id"]).profile.preferences = {"cv_skill_context": [{"skill": "sql", "state": "learning", "excerpt": "Estoy aprendiendo SQL", "context_version": CONTEXT_VERSION}], "cv_context_version": CONTEXT_VERSION}
        session.commit()
    endpoint = "/api/v1/profiles/me/cv-mentions"
    assert client.patch(endpoint, headers=headers, json={"skill": "sql", "action": "delete"}).status_code == 409
    client.patch(endpoint, headers=headers, json={"skill": "sql", "action": "dismiss"}).raise_for_status()
    deleted = client.patch(endpoint, headers=headers, json={"skill": "sql", "action": "delete"})
    deleted.raise_for_status()
    assert deleted.json()["cv_skill_context"] == [] and deleted.json()["skills"] == ["python"]
    assert "sql" not in deleted.json()["cv_mention_decisions"]
    assert client.get("/api/v1/profiles/me", headers=headers).json()["cv_skill_context"] == []


def test_company_ranking_is_progressive_scoped_and_uses_a_constant_number_of_queries(client, monkeypatch):
    _, owner = company_account(client, "bounded-ranking-company")
    _, other = company_account(client, "bounded-ranking-other")
    job = create_job(client, owner)
    for index in range(15):
        register(client, f"bounded-person-{index}", skills=["python"])
    calls = []
    original = matching._candidate_match
    def score(profile, job, **kwargs):
        calls.append(profile.user_id)
        return original(profile, job, **kwargs)
    monkeypatch.setattr(matching, "_candidate_match", score)
    endpoint = f"/api/v1/recommendations/jobs/{job['id']}/candidates-page?minimum_match=0&limit=5"
    first = client.get(endpoint, headers=owner)
    assert first.status_code == 200, first.text
    assert len(calls) == 12 and first.json()["pending"] == 3 and len(first.json()["items"]) == 5
    second = client.get(endpoint, headers=owner)
    assert second.json()["pending"] == 0 and second.json()["pool_total"] == 15 and len(calls) == 15
    calls.clear()
    statements = []
    with client.session_factory() as session:
        engine = session.get_bind()
    def record(_, __, statement, *args):
        if statement.lstrip().startswith("SELECT"):
            statements.append(statement)
    event.listen(engine, "before_cursor_execute", record)
    try:
        warm = client.get(endpoint, headers=owner)
        assert warm.status_code == 200 and not calls
        assert len(statements) <= 18, len(statements)
    finally:
        event.remove(engine, "before_cursor_execute", record)
    assert client.get(endpoint, headers=other).status_code == 403
    with matching_slot(("company-job", job["id"])) as acquired:
        assert acquired
        assert client.get(endpoint, headers=owner).json()["pending"] == 0


def test_company_job_selector_is_paginated_and_never_returns_another_company(client):
    _, owner = company_account(client, "selector-owner")
    _, other = company_account(client, "selector-other")
    owned = [create_job(client, owner) for _ in range(3)]
    foreign = create_job(client, other)
    response = client.get("/api/v1/jobs/mine/choices?limit=2", headers=owner)
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 3 and len(response.json()["items"]) == 2
    assert foreign["id"] not in {row["id"] for row in response.json()["items"]}
    assert all("description" not in row and "embedding" not in row for row in response.json()["items"])
    last = client.get("/api/v1/jobs/mine/choices?limit=2&offset=2", headers=owner).json()
    assert len(last["items"]) == 1
    assert {row["id"] for row in [*response.json()["items"], *last["items"]]} == {row["id"] for row in owned}


def test_inference_capacity_never_blocks_readers_waiting_for_a_slot():
    with matching_slot("first") as first, matching_slot("second") as second, matching_slot("third") as third:
        assert first and second and not third
    with matching_slot("third") as available:
        assert available
