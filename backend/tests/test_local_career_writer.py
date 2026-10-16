import json
import subprocess
from types import SimpleNamespace

import pytest

from app.application.errors import UseCaseError
from app.infrastructure.nlp.career_writer import LocalCareerWriter


def test_local_inference_uses_files_and_no_network_provider(tmp_path, monkeypatch):
    model = tmp_path / "model.gguf"; model.write_bytes(b"GGUFtest")
    executable = tmp_path / "local.exe"; executable.write_bytes(b"test")
    observed = []
    def run(command, **options):
        assert options["shell"] is False and options["env"]["HF_HUB_OFFLINE"] == "1"
        assert not any("http://" in value or "https://" in value for value in command)
        assert "private description" not in " ".join(command)
        path = command[command.index("-f") + 1]
        from pathlib import Path
        assert "private description" in Path(path).read_text(encoding="utf-8")
        observed.append(Path(path))
        schema = json.loads(command[command.index("-j") + 1])
        assert schema["properties"]["actions"]["minItems"] == 1
        return SimpleNamespace(returncode=0, stdout=json.dumps({"actions": [{"index": 0, "text": "Texto revisable"}], "idea": "¿Qué entregaste?"}).encode(), stderr=b"")
    monkeypatch.setattr(subprocess, "run", run)
    writer = LocalCareerWriter(str(model), str(executable))
    assert writer.generate({"description": "private description"}, style="paragraph", result="")["actions"][0]["text"] == "Texto revisable"
    assert not observed[0].exists()
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired("local", 10)))
    with pytest.raises(UseCaseError) as error:
        writer.generate({"description": "private description"}, style="paragraph", result="")
    assert error.value.status_code == 504
    assert not writer.lock.locked()


def test_summary_generation_uses_the_local_process_and_shares_its_busy_gate(tmp_path, monkeypatch):
    from pathlib import Path
    model = tmp_path / "model.gguf"; model.write_bytes(b"GGUFtest")
    executable = tmp_path / "local.exe"; executable.write_bytes(b"test")
    observed = []
    def run(command, **options):
        assert options["shell"] is False and options["env"]["HF_HUB_OFFLINE"] == "1"
        prompt = Path(command[command.index("-f") + 1])
        observed.append(prompt)
        contents = prompt.read_text(encoding="utf-8")
        assert "private professional facts" in contents and "nunca instrucciones" in contents
        assert "private professional facts" not in " ".join(command)
        assert "actions" in json.loads(command[command.index("-j") + 1])["properties"]
        return SimpleNamespace(returncode=0, stdout=json.dumps({"actions": [{"index": 0, "text": "Soy private professional facts."}], "idea": ""}).encode(), stderr=b"")
    monkeypatch.setattr(subprocess, "run", run)
    writer = LocalCareerWriter(str(model), str(executable))
    assert writer.generate_summary({"profesion": "private professional facts"}, tone="concise")["summary"]
    assert not observed[0].exists()
    writer.lock.acquire()
    try:
        with pytest.raises(UseCaseError) as error:
            writer.generate_summary({}, tone="professional")
        assert error.value.status_code == 429
    finally:
        writer.lock.release()


def test_summary_keeps_study_status_and_discards_an_unsupported_model_denial(tmp_path, monkeypatch):
    model = tmp_path / "model.gguf"; model.write_bytes(b"GGUFtest")
    executable = tmp_path / "local.exe"; executable.write_bytes(b"test")
    writer = LocalCareerWriter(str(model), str(executable))
    monkeypatch.setattr(writer, "_actions", lambda *args, **kwargs: {"actions": [{"index": 0, "text": "No tengo experiencia y estudio Tecnología en desarrollo web."}], "idea": ""})
    facts = {"profesion": "Desarrollador frontend", "habilidades": ["React"], "experiencias": [{"funciones": "Desarrollo interfaces web con React", "actual": True}], "formacion": [{"titulo": "Ingeniería de Sistemas", "en_curso": True}], "resumen_actual": ""}
    result = writer.generate_summary(facts, tone="professional")["summary"]
    assert "Desarrollo interfaces web con React" in result
    assert "Actualmente estudio Ingeniería de Sistemas" in result
    assert "No tengo experiencia" not in result and "Tecnología en desarrollo web" not in result
