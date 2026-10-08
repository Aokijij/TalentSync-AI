"""Optional, strictly local neural inference; lexical CV parsing stays unchanged."""
import hashlib
import json
import os
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from threading import Lock

from app.core.config import settings


class LocalMatchingEncoder:
    def __init__(self, folder):
        path = Path(folder)
        if not path.is_absolute() or not path.is_dir():
            raise ValueError("MATCH_MODEL_PATH debe ser una carpeta absoluta con un modelo local")
        files = sorted(item for item in path.rglob("*") if item.is_file())
        if any(not item.resolve().is_relative_to(path.resolve()) for item in files):
            raise ValueError("El modelo no puede enlazar archivos fuera de su carpeta")
        if any(item.suffix in {".py", ".bin", ".pt", ".pth", ".pkl", ".pickle"} for item in files):
            raise ValueError("El modelo local debe usar safetensors y módulos estándar, sin código ni pickle")
        if not any(item.suffix == ".safetensors" for item in files):
            raise ValueError("Faltan pesos safetensors locales")
        modules = json.loads((path / "modules.json").read_text(encoding="utf-8"))
        allowed = {f"sentence_transformers.models.{name}" for name in ["Transformer", "Pooling", "Dense", "Normalize"]}
        if any(row.get("type") not in allowed for row in modules):
            raise ValueError("El modelo contiene módulos no admitidos")
        if any(not (path / row.get("path", "")).resolve().is_relative_to(path.resolve()) for row in modules):
            raise ValueError("Los módulos deben permanecer dentro de la carpeta local")
        fingerprint = hashlib.sha256()
        for item in files:
            fingerprint.update(item.relative_to(path).as_posix().encode())
            with item.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    fingerprint.update(chunk)
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        try:
            import torch
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ValueError("Falta la dependencia opcional sentence-transformers; consulta DEVELOPMENT.md") from None
        torch.set_num_threads(settings.match_model_cpu_threads)
        self.model = SentenceTransformer(str(path), device="cpu", local_files_only=True, trust_remote_code=False,
            model_kwargs={"use_safetensors": True, "local_files_only": True})
        self.method = f"local-sentence-transformer:{fingerprint.hexdigest()[:16]}"
        self._vectors = OrderedDict()
        self._lock = Lock()

    def _embedding(self, text):
        text = text[:20000]
        key = hashlib.sha256(text.encode()).digest()
        # Bounded, process-only cache. Retains hashes and vectors, never original text.
        with self._lock:
            if key not in self._vectors:
                vector = self.model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]
                vector.setflags(write=False)
                self._vectors[key] = vector
                if len(self._vectors) > 512:
                    self._vectors.popitem(last=False)
            self._vectors.move_to_end(key)
            return self._vectors[key]

    def similarity(self, left, right):
        return round(max(0, min(1, float(self._embedding(left) @ self._embedding(right)))) * 100, 2)


@lru_cache(maxsize=1)
def _configured_encoder(folder):
    return LocalMatchingEncoder(folder) if folder else None


def matching_encoder():
    return _configured_encoder(settings.match_model_path)
