import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def rehearsal(tmp_path, monkeypatch):
    scripts = Path(__file__).resolve().parents[2] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location("postgres_rehearsal_tests", scripts / "staging_postgres.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "FOLDER", tmp_path / "staging")
    monkeypatch.setattr(module, "DATA", tmp_path / "staging/pgdata")
    return module


def test_cluster_without_owned_credentials_is_never_adopted(rehearsal):
    rehearsal.DATA.mkdir(parents=True)
    with pytest.raises(RuntimeError):
        rehearsal.credentials()
    assert not (rehearsal.FOLDER / "credentials.json").exists()


@pytest.mark.parametrize("actual,listen", [("foreign-data", "127.0.0.1"), ("own", "*")])
def test_foreign_or_public_cluster_is_rejected_before_admin_actions(rehearsal, actual, listen):
    answers = [str(rehearsal.DATA) if actual == "own" else actual, listen]
    connection = SimpleNamespace(execute=lambda query: SimpleNamespace(fetchone=lambda: (answers.pop(0),)))
    with pytest.raises(RuntimeError):
        rehearsal.assert_owned(connection)


def test_incomplete_cluster_is_never_overwritten(rehearsal, monkeypatch):
    rehearsal.DATA.mkdir(parents=True)
    monkeypatch.setattr(rehearsal, "run", lambda *args, **kwargs: pytest.fail("initdb must not execute"))
    with pytest.raises(RuntimeError):
        rehearsal.initialize({}, {"admin": "not-used"})


def test_non_rehearsal_database_is_rejected_before_connecting(rehearsal, monkeypatch):
    monkeypatch.setattr(rehearsal, "connect", lambda *args: pytest.fail("must not connect"))
    with pytest.raises(RuntimeError):
        rehearsal.create_database({}, "production")


def test_existing_application_role_must_not_have_admin_privileges(rehearsal, monkeypatch):
    calls = []
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, statement, params=None):
            calls.append(str(statement))
            return SimpleNamespace(fetchone=lambda: (True, False, False) if "rolsuper" in str(statement) else (1,))
    monkeypatch.setattr(rehearsal, "connect", lambda *args: Connection())
    monkeypatch.setattr(rehearsal, "assert_owned", lambda connection: None)
    with pytest.raises(RuntimeError):
        rehearsal.create_database({}, "talentsync_rehearsal_test")
    assert all("CREATE" not in query for query in calls)


def test_process_failure_never_echoes_driver_credentials_or_sql(rehearsal, monkeypatch):
    def failure(command, **kwargs):
        kwargs["stdout"].write("PRIVATE-DRIVER-URL / SQL TOKEN VALUE")
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(rehearsal.subprocess, "run", failure)
    with pytest.raises(RuntimeError) as error:
        rehearsal.run(["fake-process"])
    assert "PRIVATE" not in str(error.value) and "TOKEN" not in str(error.value)
