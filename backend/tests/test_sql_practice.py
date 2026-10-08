# ruff: noqa: F811
import json
from datetime import datetime, timedelta

import pytest
from test_account_security import browser, csrf, login  # noqa: F401
from test_api_flows import client, register  # noqa: F401

from app.domain.services.sql_challenges import DATASETS
from app.infrastructure.database.models import AssessmentAttempt, EventLog
from app.infrastructure.sql_sandbox import SQLSandbox

TOTALS = "SELECT c.name AS customer, SUM(o.total) AS total FROM customers c JOIN orders o ON o.customer_id=c.id WHERE o.status='paid' GROUP BY c.id,c.name HAVING SUM(o.total)>=100"
COUNTS = "SELECT c.name AS customer, COUNT(o.id) AS paid_orders FROM customers c LEFT JOIN orders o ON o.customer_id=c.id AND o.status='paid' GROUP BY c.id,c.name"


@pytest.mark.parametrize("query", ["ATTACH DATABASE '/private/file.db' AS secret", "SELECT * FROM sqlite_master", "DELETE FROM orders", "DROP TABLE customers", "PRAGMA database_list", "SELECT load_extension('/private/library')", "SELECT readfile('/private/file')", "SELECT randomblob(1000000000)", "SELECT 1; SELECT 2", "SELECT 1e999", "SELECT x'fffe'"])
def test_sql_only_reads_synthetic_tables_and_results_are_safe_to_serialize(query):
    result = SQLSandbox().run(query, DATASETS[0])
    assert result["ok"] is False
    assert "/private/" not in json.dumps(result)
    assert SQLSandbox().run("SELECT COUNT(*) AS n FROM customers", DATASETS[0])["rows"] == [[3]]


def test_sql_work_and_result_budgets_interrupt_expensive_queries():
    sandbox = SQLSandbox()
    assert sandbox.run("SELECT a.id FROM orders a, orders b, orders c, orders d", DATASETS[0])["error"] == "result_limit"
    assert sandbox.run("SELECT COUNT(*) FROM orders a, orders b, orders c, orders d, orders e, orders f, orders g, orders h, orders i, orders j", DATASETS[0])["ok"] is False
    query = "WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n) SELECT sum(x) FROM n"
    assert sandbox.run(query, DATASETS[0])["ok"] is False
    assert sandbox.run("SELECT '" + "x" * 4001 + "'", DATASETS[0])["ok"] is False


@pytest.mark.parametrize("challenge,query", [("sql-paid-totals-v1", TOTALS), ("sql-paid-counts-v1", COUNTS)])
def test_real_queries_are_evaluated_once_and_enter_existing_passport(client, challenge, query):
    _, candidate = register(client, "sql-practitioner", skills=["Java"])
    start = client.post(f"/api/v1/learning/practical/{challenge}/start", headers=candidate)
    assert start.status_code == 200, start.text
    attempt = start.json()
    assert "expected" not in start.text and "Noa" not in start.text
    assert client.post(f"/api/v1/learning/practical/{challenge}/start", headers=candidate).json()["id"] == attempt["id"]
    endpoint = f"/api/v1/learning/practical/attempts/{attempt['id']}"
    assert client.post(endpoint + "/preview", headers=candidate, json={"query": query}).json()["ok"] is True
    assert "sql" not in client.get("/api/v1/profiles/me", headers=candidate).json()["skills"]
    assert client.post(f"/api/v1/learning/attempts/{attempt['id']}/submit", headers=candidate, json={"answers": {}}).status_code == 422
    result = client.post(endpoint + "/submit", headers=candidate, json={"query": query})
    assert result.status_code == 200, result.text
    assert result.json()["passed"] is True and result.json()["score"] == 100
    assert client.post(endpoint + "/submit", headers=candidate, json={"query": query}).status_code == 409
    assert client.post(f"/api/v1/learning/practical/{challenge}/start", headers=candidate).status_code == 429
    passport = client.get("/api/v1/learning/passport", headers=candidate).json()["assessments"]
    assert passport[0]["assessment_id"] == challenge and passport[0]["valid"] is True
    assert "sql" in client.get("/api/v1/profiles/me", headers=candidate).json()["skills"]
    with client.session_factory() as db:
        attempt = db.get(AssessmentAttempt, attempt["id"])
        assert query not in json.dumps(attempt.snapshot) and query not in json.dumps(attempt.feedback)
        events = db.query(EventLog).filter_by(event_type="assessment.completed").all()
        assert all(query not in json.dumps(row.details) for row in events)


def test_hardcoded_visible_answer_does_not_accredit_a_skill(client):
    _, candidate = register(client, "hardcoded-sql", skills=["Java"])
    attempt = client.post("/api/v1/learning/practical/sql-paid-totals-v1/start", headers=candidate).json()
    result = client.post(f"/api/v1/learning/practical/attempts/{attempt['id']}/submit", headers=candidate, json={"query": "SELECT 'Ana' AS customer, 150 AS total"})
    assert result.status_code == 200 and result.json()["passed"] is False
    assert "sql" not in client.get("/api/v1/profiles/me", headers=candidate).json()["skills"]


def test_attempt_scope_expiry_and_browser_csrf(browser):
    register(browser, "alex")
    login(browser)
    endpoint = "/api/v1/learning/practical/sql-paid-totals-v1/start"
    assert browser.post(endpoint).status_code == 403
    attempt = browser.post(endpoint, headers=csrf(browser)).json()
    preview = f"/api/v1/learning/practical/attempts/{attempt['id']}/preview"
    register(browser, "sql-outsider")
    browser.cookies.clear()
    # The browser fixture uses session mode, so authenticate the second account.
    login(browser, email="sql-outsider@example.com")
    assert browser.post(preview, headers=csrf(browser), json={"query": TOTALS}).status_code == 404
    browser.cookies.clear()
    login(browser)
    with browser.session_factory() as db:
        db.get(AssessmentAttempt, attempt["id"]).expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
    assert browser.post(preview, headers=csrf(browser), json={"query": TOTALS}).status_code == 409
