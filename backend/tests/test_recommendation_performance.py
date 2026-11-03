# ruff: noqa: F811
import sqlite3

from sqlalchemy import event
from test_api_flows import client, company_account, register  # noqa: F401

from app.application.use_cases import matching
from app.infrastructure.database.models import (
    Application,
    Company,
    Job,
    Profile,
    Recommendation,
)
from app.infrastructure.database.session import configure_sqlite
from app.infrastructure.matching_gate import matching_slot


def add_jobs(client, count):
    owner, headers = company_account(client, "performance-company")
    with client.session_factory() as db:
        company = db.query(Company).filter_by(owner_user_id=owner["id"]).one()
        db.add_all([Job(company_id=company.id, title=f"Desarrollador Python {index}", description="Desarrollar servicios para el equipo de producto", requirements="Python y SQL", skills=["python", "sql"]) for index in range(count)])
        db.commit()
    return headers


def test_progressive_batches_are_bounded_and_never_return_stale_scores(client, monkeypatch):
    add_jobs(client, 17)
    user, headers = register(client, "performance-owner", skills=["python"])
    calls = []
    original = matching._candidate_match
    def score(profile, job, **kwargs):
        calls.append(job.id)
        return original(profile, job, **kwargs)
    monkeypatch.setattr(matching, "_candidate_match", score)
    path = "/api/v1/recommendations/me/jobs/batch?batch_size=4"
    for index, expected in enumerate([4, 8, 12, 16, 17]):
        response = client.get(path, headers=headers)
        assert response.status_code == 200, response.text
        result = response.json()
        assert len(result["items"]) == expected and result["pending"] == 17 - expected
        assert len(calls) == expected
    calls.clear()
    assert client.get(path, headers=headers).json()["pending"] == 0 and not calls
    with client.session_factory() as db:
        profile = db.query(Profile).filter_by(user_id=user["id"]).one()
        profile.resume_color = "forest"
        db.commit()
    assert client.get(path, headers=headers).json()["pending"] == 0 and not calls
    with client.session_factory() as db:
        profile = db.query(Profile).filter_by(user_id=user["id"]).one()
        profile.skills = ["javascript"]
        db.commit()
    result = client.get(path, headers=headers).json()
    assert len(result["items"]) == 4 and result["pending"] == 13 and len(calls) == 4
    assert client.get("/api/v1/recommendations/me/jobs/batch?batch_size=100", headers=headers).status_code == 422


def test_warm_recommendations_do_not_reload_each_job_after_commit(client):
    add_jobs(client, 40)
    _, headers = register(client, "performance-warm", skills=["python"])
    client.get("/api/v1/recommendations/me/jobs?include_all=true", headers=headers).raise_for_status()
    statements = []
    engine = client.session_factory.kw["bind"]
    def record(*args):
        statements.append(args[2])
    event.listen(engine, "before_cursor_execute", record)
    try:
        response = client.get("/api/v1/recommendations/me/jobs/batch", headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["pending"] == 0
        assert len(response.json()["items"]) == 40
        assert len(statements) < 30, len(statements)
        assert not any(statement.lstrip().startswith(("INSERT", "UPDATE")) for statement in statements)
    finally:
        event.remove(engine, "before_cursor_execute", record)


def test_overlapping_batch_returns_progress_without_waiting_for_inference(client, monkeypatch):
    add_jobs(client, 7)
    user, headers = register(client, "performance-overlap", skills=["python"])
    def unexpected(*args, **kwargs):
        raise AssertionError("Overlapping request must not start inference")
    monkeypatch.setattr(matching, "_candidate_match", unexpected)
    with matching_slot(user["id"]) as acquired:
        assert acquired
        response = client.get("/api/v1/recommendations/me/jobs/batch", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == {"items": [], "pending": 7, "total": 7}


def test_applied_view_scores_only_applicants(client, monkeypatch):
    headers = add_jobs(client, 1)
    users = [register(client, f"performance-candidate-{index}", skills=["python"])[0] for index in range(10)]
    with client.session_factory() as db:
        job_id = db.query(Job).one().id
        db.add_all([Application(user_id=user["id"], job_id=job_id) for user in users[:2]])
        db.commit()
    calls = []
    original = matching._candidate_match
    def score(profile, job, **kwargs):
        calls.append(profile.user_id)
        return original(profile, job, **kwargs)
    monkeypatch.setattr(matching, "_candidate_match", score)
    response = client.get(f"/api/v1/recommendations/jobs/{job_id}/candidates-page?audience=applied", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 2 and set(calls) == {user["id"] for user in users[:2]}
    with client.session_factory() as db:
        assert db.query(Recommendation).count() == 2


def test_sqlite_reader_does_not_block_session_revocation(tmp_path):
    path = tmp_path / "concurrent.sqlite3"
    with sqlite3.connect(path) as setup:
        configure_sqlite(setup, None)
        setup.execute("CREATE TABLE sessions (id INTEGER PRIMARY KEY, revoked INTEGER)")
        setup.execute("INSERT INTO sessions VALUES (1, 0)")
    reader = sqlite3.connect(path, timeout=.1)
    writer = sqlite3.connect(path, timeout=.1)
    try:
        reader.execute("BEGIN")
        assert reader.execute("SELECT revoked FROM sessions").fetchone() == (0,)
        writer.execute("UPDATE sessions SET revoked=1 WHERE id=1")
        writer.commit()
        reader.rollback()
        assert reader.execute("SELECT revoked FROM sessions").fetchone() == (1,)
    finally:
        reader.close(); writer.close()
