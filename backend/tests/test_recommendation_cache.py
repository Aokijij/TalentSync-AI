# ruff: noqa: F811
from datetime import datetime, timedelta

from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.application.use_cases import matching
from app.infrastructure.database.models import Recommendation


def test_cache_refreshes_only_changed_added_or_expired_jobs(client, monkeypatch):
    _, company = company_account(client, "cache-company")
    jobs = [create_job(client, company) for _ in range(3)]
    _, candidate = register(client, "cache-person", skills=["python"])
    original = matching._candidate_match
    calls = []
    def record(profile, job, *, nlp):
        calls.append(job.id)
        return original(profile, job, nlp=nlp)
    monkeypatch.setattr(matching, "_candidate_match", record)
    endpoint = "/api/v1/recommendations/me/jobs?include_all=true"
    first = client.get(endpoint, headers=candidate)
    assert first.status_code == 200, first.text
    assert set(calls) == {job["id"] for job in jobs}
    calls.clear()
    assert client.get(endpoint, headers=candidate).status_code == 200 and not calls
    with client.session_factory() as db:
        row = db.query(Recommendation).filter_by(job_id=jobs[1]["id"]).one()
        row.created_at = datetime.utcnow() - timedelta(minutes=11)
        db.commit()
    refreshed = client.get(endpoint, headers=candidate)
    assert refreshed.status_code == 200 and calls == [jobs[1]["id"]]
    calls.clear()
    extra = create_job(client, company)
    client.get(endpoint, headers=candidate).raise_for_status()
    assert calls == [extra["id"]]
    calls.clear()
    from app.infrastructure.database.models import Job
    with client.session_factory() as db:
        db.get(Job, jobs[0]["id"]).description += " Construcción de informes nuevos."
        db.commit()
    client.get(endpoint, headers=candidate).raise_for_status()
    assert calls == [jobs[0]["id"]]
    calls.clear()
    p = client.get("/api/v1/profiles/me", headers=candidate).json()
    p["skills"] = ["python", "sql"]
    client.put("/api/v1/profiles/me", headers=candidate, json=p).raise_for_status()
    client.get(endpoint, headers=candidate).raise_for_status()
    assert set(calls) == {job["id"] for job in [*jobs, extra]}
