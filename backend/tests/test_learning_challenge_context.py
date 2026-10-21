# ruff: noqa: F811
from test_api_flows import client, register  # noqa: F401


def test_catalog_resumes_own_latest_attempt_without_exposing_answers_or_other_users(client):
    _, candidate = register(client, "challenge-context", skills=["python"])
    _, other = register(client, "challenge-context-other")
    endpoint = "/api/v1/learning/catalog?area=all"
    initial = client.get(endpoint, headers=candidate).json()
    row = next(item for item in initial["assessments"] if item["id"] == "python-foundations-v1")
    assert row["last_attempt"] is None and "declaraste" in row["relevance_reason"]
    attempt = client.post("/api/v1/learning/assessments/python-foundations-v1/start", headers=candidate).json()
    catalog = client.get(endpoint, headers=candidate).json()
    row = next(item for item in catalog["assessments"] if item["id"] == "python-foundations-v1")
    assert row["last_attempt"]["id"] == attempt["id"] and row["last_attempt"]["status"] == "active"
    assert "questions" not in row["last_attempt"] and "snapshot" not in row["last_attempt"]
    assert "answers" not in row["last_attempt"] and "feedback" not in row["last_attempt"]
    other_catalog = client.get(endpoint, headers=other).json()
    assert all(item["last_attempt"] is None for item in other_catalog["assessments"])
