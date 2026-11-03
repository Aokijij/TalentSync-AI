import importlib.util
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def checks(tmp_path, monkeypatch):
    scripts = Path(__file__).resolve().parents[2] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location("local_checks_for_tests", scripts / "local_checks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    local = tmp_path / ".local"
    local.mkdir()
    monkeypatch.setattr(module.local, "ROOT", tmp_path)
    monkeypatch.setattr(module.local, "LOCAL", local)
    monkeypatch.setattr(module.local, "ENV_FILE", local / "backend.env")
    monkeypatch.setattr(module.local, "PYTHON", tmp_path / "python.exe")
    module.local.PYTHON.write_bytes(b"not-executed")
    module.local.ENV_FILE.write_text(f"ENVIRONMENT=development\nDATABASE_URL=sqlite:///{(local / 'talentsync.sqlite3').as_posix()}\nSECRET_KEY=PRIVATE-DO-NOT-PRINT\n", encoding="utf-8")
    versions = tmp_path / "backend/alembic/versions"
    versions.mkdir(parents=True)
    (versions / "001.py").write_text("revision = 'first'\ndown_revision = None\n", encoding="utf-8")
    (versions / "002.py").write_text("revision: str = 'second'\ndown_revision: str | None = 'first'\n", encoding="utf-8")
    for dependency in ["eslint/bin/eslint.js", "vite/bin/vite.js"]:
        path = tmp_path / "frontend/node_modules" / dependency
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    with sqlite3.connect(local / "talentsync.sqlite3") as connection:
        connection.execute("CREATE TABLE alembic_version(version_num TEXT)")
        connection.execute("INSERT INTO alembic_version VALUES ('second')")
    monkeypatch.setattr(module, "node_executable", lambda: "node")
    monkeypatch.setattr(module, "http_probe", lambda *args, **kwargs: False)
    return module


def test_doctor_accepts_stopped_services_and_does_not_disclose_credentials(checks):
    env_before = checks.local.ENV_FILE.read_bytes()
    database = checks.local.LOCAL / "talentsync.sqlite3"
    database_before = database.read_bytes()
    report = checks.diagnose()
    assert report["ready"]
    assert all(not row["required"] for row in report["checks"] if not row["passed"])
    assert "PRIVATE-DO-NOT-PRINT" not in json.dumps(report)
    assert database.read_bytes() == database_before
    assert checks.local.ENV_FILE.read_bytes() == env_before


@pytest.mark.parametrize("fault", ["migration", "corrupt_database", "external_environment", "missing_environment", "model_missing"])
def test_doctor_detects_local_blockers_without_connecting_to_external_database(checks, fault):
    database = checks.local.LOCAL / "talentsync.sqlite3"
    if fault == "migration":
        with sqlite3.connect(database) as connection:
            connection.execute("UPDATE alembic_version SET version_num='first'")
    if fault == "corrupt_database": database.write_bytes(b"not-a-database")
    if fault == "external_environment": checks.local.ENV_FILE.write_text("ENVIRONMENT=development\nDATABASE_URL=postgresql://PRIVATE-EXTERNAL.invalid/data\n")
    if fault == "missing_environment": checks.local.ENV_FILE.unlink()
    if fault == "model_missing":
        with checks.local.ENV_FILE.open("a", encoding="utf-8") as stream:
            stream.write("MATCH_MODEL_PATH=nonexistent-model\n")
    report = checks.diagnose()
    assert not report["ready"]
    assert "PRIVATE-EXTERNAL" not in json.dumps(report)
    if fault == "missing_environment": assert not checks.local.ENV_FILE.exists()


def test_migration_head_is_discovered_and_rejects_multiple_heads(checks):
    assert checks.migration_head(checks.local.ROOT) == "second"
    path = checks.local.ROOT / "backend/alembic/versions/003.py"
    path.write_text("revision = 'third'\ndown_revision = 'first'\n", encoding="utf-8")
    with pytest.raises(ValueError): checks.migration_head(checks.local.ROOT)


@pytest.mark.parametrize("fail_at", [None, "backend_tests"])
def test_verify_reports_success_or_stops_at_failure_without_saving_secrets(checks, monkeypatch, fail_at):
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        assert kwargs["env"]["VITE_API_URL"] == "/api/v1"
        assert kwargs["env"]["HF_HUB_OFFLINE"] == "1"
        failed = fail_at and command[-1] == "test"
        return SimpleNamespace(returncode=1 if failed else 0)
    monkeypatch.setattr(checks, "source_fingerprint", lambda: "only-test-fingerprint")
    monkeypatch.setattr(checks.subprocess, "run", run)
    assert checks.verify() == (1 if fail_at else 0)
    report = json.loads((checks.local.LOCAL / "verification/validation.json").read_text(encoding="utf-8"))
    assert report["passed"] == (fail_at is None)
    assert len(calls) == (3 if fail_at else 6)
    assert "PRIVATE-DO-NOT-PRINT" not in json.dumps(report)
    if fail_at: assert report["steps"][-1] == {"name": "backend_tests", "passed": False, "seconds": report["steps"][-1]["seconds"]}


def test_validation_includes_only_configured_model_and_local_commands(checks):
    steps = checks.validation_steps({"MATCH_MODEL_PATH": "configured-model"}, "node")
    assert steps[-1][0] == "local_model"
    assert all("http" not in str(command) and "deploy" not in str(command) for _, command, _ in steps)
    steps = checks.validation_steps({"CV_ENTITY_MODEL_PATH": "cv-model", "CV_ENTITY_PYTHON": "cv-python"}, "node")
    assert steps[-1][0] == "cv_entity_model"


def test_verify_rejects_source_changes_during_the_checks(checks, monkeypatch):
    fingerprints = iter(["before", "after"])
    monkeypatch.setattr(checks, "source_fingerprint", lambda: next(fingerprints))
    monkeypatch.setattr(checks.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    assert checks.verify() == 1
    report = json.loads((checks.local.LOCAL / "verification/validation.json").read_text(encoding="utf-8"))
    assert report["error_type"] == "source_changed_during_validation" and not report["passed"]
