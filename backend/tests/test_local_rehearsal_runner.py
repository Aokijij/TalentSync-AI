import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("fault", [None, "validation", "stale_source"])
def test_rehearsal_stops_on_failure_and_rejects_stale_reports(tmp_path, monkeypatch, fault):
    scripts = Path(__file__).resolve().parents[2] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location("rehearsal_for_tests", scripts / "local_rehearsal.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.local, "ROOT", tmp_path)
    monkeypatch.setattr(module.local, "LOCAL", tmp_path / ".local")
    monkeypatch.setattr(module.local, "prepare_environment", lambda: {"PRIVATE": "never-in-report"})
    monkeypatch.setattr(module, "source_fingerprint", lambda: "current")
    calls, saved = [], []

    def run(command, **kwargs):
        calls.append(command)
        assert kwargs["env"]["TALENTSYNC_LOCAL_REHEARSAL"] == "1"
        return SimpleNamespace(returncode=1 if fault == "validation" else 0)

    for filename, payload in {
        "verification/validation.json": {"source_sha256": "current"},
        "staging/verification.json": {"source_fingerprint": "old" if fault == "stale_source" else "current"},
        "verification/capacity.json": {"passed": True},
        "verification/matching-regressions.json": {"passed": True},
    }.items():
        path = module.local.LOCAL / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(module.subprocess, "run", run)
    monkeypatch.setattr(module, "save_report", lambda name, report: saved.append(report))
    with pytest.raises(SystemExit) as exit_code:
        module.main()
    assert exit_code.value.code == (0 if fault is None else 1)
    assert len(calls) == (1 if fault == "validation" else 3)
    assert saved[0]["passed"] == (fault is None)
    assert "never-in-report" not in json.dumps(saved)
