# ruff: noqa: F811
import json
import subprocess
from types import SimpleNamespace

import pytest
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.infrastructure.nlp import cv_entities
from scripts.evaluate_cv_entities import metrics


def entity(text="Python", **changes):
    return {"start": 0, "end": len(text), "text": text, "label": "technical skill", "score": .9, **changes}


def test_entities_require_exact_source_spans_supported_labels_and_finite_scores():
    rows = [entity(), entity(score=.95), entity(text="Inventado"), entity(start=-1),
            entity(score=float("nan")), entity(score=True), entity(score=.49), entity(label="person"), entity(label={}), entity(end=1000)]
    result = cv_entities.validated_entities("Python", rows)
    assert len(result) == 1 and result[0]["text"] == "Python" and result[0]["score"] == .95
    assert result[0]["excerpt"] == "Python"
    assert cv_entities.validated_entities("Python", {}) == []


@pytest.mark.parametrize("text,state", [("Estoy aprendiendo Python", "learning"), ("Python: sin experiencia", "negated"), ("Proyectos\nImplementé Python", "project")])
def test_neural_skill_suggestions_retain_negative_learning_and_project_context(text, state):
    start = text.index("Python")
    result = cv_entities.validated_entities(text, [entity(start=start, end=start + 6)])
    assert result[0]["context"] == state


def test_windows_preserve_original_offsets_and_cover_boundaries():
    text = "\n  ".join(f"palabra{index}" for index in range(500))
    windows = list(cv_entities.chunks(text))
    assert len(windows) > 1
    covered = set()
    for start, window in windows:
        assert text[start:start + len(window)] == window
        covered.update(range(start, start + len(window)))
    assert all(index in covered for index, char in enumerate(text) if not char.isspace())


def test_worker_is_offline_receives_no_integration_secrets_and_truncates(monkeypatch, tmp_path):
    python = tmp_path / "python.exe"
    python.touch()
    (tmp_path / "model.safetensors").touch()
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-private-key")
    monkeypatch.setenv("HF_TOKEN", "test-private-token")
    monkeypatch.setenv("PYTHONPATH", "unexpected-path")
    def run(command, **kwargs):
        assert "test-private" not in str(kwargs["env"])
        assert "PYTHONPATH" not in kwargs["env"]
        assert kwargs["env"]["HF_HUB_OFFLINE"] == kwargs["env"]["TRANSFORMERS_OFFLINE"] == "1"
        assert len(json.loads(kwargs["input"])["text"]) == cv_entities.MAX_CHARS
        assert "Python" not in " ".join(command)
        return SimpleNamespace(stdout=json.dumps({"entities": [entity()]}))
    monkeypatch.setattr(subprocess, "run", run)
    result = cv_entities.extract_entities("Python" + " " * 40_000, model_path=tmp_path, python_path=python)
    assert result["status"] == "ready" and result["truncated"] and len(result["entities"]) == 1


@pytest.mark.parametrize("failure,status", [(subprocess.TimeoutExpired("worker", 1), "timeout"), (subprocess.CalledProcessError(1, "worker", stderr="private CV"), "unavailable"), (OSError("private CV"), "unavailable")])
def test_worker_fails_closed_without_returning_private_errors_and_releases_slot(monkeypatch, tmp_path, failure, status):
    python = tmp_path / "python.exe"
    python.touch()
    (tmp_path / "model.safetensors").touch()
    def run(*args, **kwargs):
        raise failure
    monkeypatch.setattr(subprocess, "run", run)
    result = cv_entities.extract_entities("private CV", model_path=tmp_path, python_path=python)
    assert result["status"] == status and result["entities"] == [] and "private" not in str(result)
    assert cv_entities._gate.acquire(blocking=False)
    cv_entities._gate.release()


def test_benchmark_counts_false_positives_and_false_negatives():
    score = metrics({"correct", "missed"}, {"correct", "incorrect"})
    assert score == {"tp": 1, "fp": 1, "fn": 1, "precision": .5, "recall": .5, "f1": .5}


def test_busy_worker_and_absent_configuration_do_not_spawn(monkeypatch, tmp_path):
    from app.core.config import settings
    monkeypatch.setattr(settings, "cv_entity_model_path", "")
    monkeypatch.setattr(settings, "cv_entity_python", "")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: pytest.fail("Unexpected worker"))
    assert cv_entities.extract_entities("private CV")["status"] == "disabled"
    python = tmp_path / "python.exe"
    python.touch()
    (tmp_path / "model.safetensors").touch()
    cv_entities._gate.acquire()
    try:
        assert cv_entities.extract_entities("private CV", model_path=tmp_path, python_path=python)["status"] == "busy"
    finally:
        cv_entities._gate.release()


def test_neural_upload_suggestions_are_owner_only_and_not_automatically_applied(client, monkeypatch, tmp_path):
    from app.core.config import settings
    from app.infrastructure.nlp import resumes
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr(resumes, "extract_pdf_text", lambda _: "Habilidades\nSQL\nEstoy aprendiendo DuckDB.")
    suggestions = {"method": cv_entities.METHOD, "status": "ready", "entities": [{"kind": "skill", "text": "DuckDB", "excerpt": "Estoy aprendiendo DuckDB.", "context": "learning"}]}
    monkeypatch.setattr(cv_entities, "extract_entities", lambda _: suggestions)
    user, candidate = register(client, "neural-review", skills=["sql"])
    _, company = company_account(client)
    job = create_job(client, company)
    client.post("/api/v1/applications", headers=candidate, json={"job_id": job["id"]}).raise_for_status()
    response = client.post("/api/v1/profiles/me/cv", headers=candidate, files={"file": ("cv.pdf", b"%PDF-1.4", "application/pdf")})
    assert response.status_code == 200, response.text
    profile = response.json()
    assert profile["cv_entity_review"] == suggestions
    assert not any(skill.lower() == "duckdb" for skill in profile["skills"])
    visible = client.get(f"/api/v1/profiles/candidates/{user['id']}", headers=company).json()
    assert visible["cv_entity_review"] == {} and "Estoy aprendiendo DuckDB." not in str(visible["cv_entity_review"])
    # An explicit profile edit is required to incorporate a neural skill.
    profile["skills"].append("DuckDB")
    saved = client.put("/api/v1/profiles/me", headers=candidate, json=profile)
    assert saved.status_code == 200, saved.text
    assert "duckdb" in [skill.lower() for skill in saved.json()["skills"]]
    assert saved.json()["cv_entity_review"] == suggestions
