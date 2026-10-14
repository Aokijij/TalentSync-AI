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
        return SimpleNamespace(returncode=0, stdout=json.dumps({"text": "Texto revisable", "idea": "¿Qué entregaste?"}).encode(), stderr=b"")
    monkeypatch.setattr(subprocess, "run", run)
    writer = LocalCareerWriter(str(model), str(executable))
    assert writer.generate({"description": "private description"}, style="paragraph", result="")["text"] == "Texto revisable"
    assert not observed[0].exists()
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired("local", 10)))
    with pytest.raises(UseCaseError) as error:
        writer.generate({"description": "private description"}, style="paragraph", result="")
    assert error.value.status_code == 504
    assert not writer.lock.locked()
