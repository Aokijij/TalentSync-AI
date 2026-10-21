import importlib.util
from pathlib import Path

import pytest


def local_commands(monkeypatch, tmp_path):
    path = Path(__file__).parents[2] / "scripts/local.py"
    spec = importlib.util.spec_from_file_location("local_commands", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "LOCAL", tmp_path)
    monkeypatch.setattr(module, "ENV_FILE", tmp_path / "backend.env")
    return module


def test_local_environment_overrides_inherited_production_configuration(monkeypatch, tmp_path):
    module = local_commands(monkeypatch, tmp_path)
    monkeypatch.setenv("DATABASE_URL", "postgresql://production.invalid/db")
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_URL", "https://production.invalid")
    monkeypatch.setenv("PERIODIC_MAINTENANCE_ENABLED", "true")
    monkeypatch.setenv("JSEARCH_API_KEY", "must-not-be-used")
    env = module.prepare_environment()
    assert env["DATABASE_URL"] == f"sqlite:///{(tmp_path / 'talentsync.sqlite3').as_posix()}"
    assert env["AZURE_STORAGE_ACCOUNT_URL"] == ""
    assert env["PERIODIC_MAINTENANCE_ENABLED"] == "false"
    assert env["JSEARCH_API_KEY"] == ""
    assert env["LOCAL_MFA_REVIEW_ENABLED"] == "true"
    assert env["COMPANY_MFA_REQUIRED"] == "false"
    assert module.prepare_environment(testing=True)["LOCAL_MFA_REVIEW_ENABLED"] == "false"
    secret = env["SECRET_KEY"]
    assert len(secret) >= 32
    assert module.prepare_environment()["SECRET_KEY"] == secret


def test_local_commands_refuse_an_external_database(monkeypatch, tmp_path):
    module = local_commands(monkeypatch, tmp_path)
    module.ENV_FILE.write_text("DATABASE_URL=postgresql://external.invalid/db\nENVIRONMENT=development\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="SQLite"):
        module.prepare_environment()
