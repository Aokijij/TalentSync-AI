import hashlib
import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from app.infrastructure.nlp.matching_encoder import LocalMatchingEncoder
from scripts.local_model import valid_file


def test_download_verifies_size_git_blob_and_lfs_sha(tmp_path):
    path = tmp_path / "weights.safetensors"
    path.write_bytes(b"fixed-contents")
    metadata = {"size": path.stat().st_size, "blobId": hashlib.sha1(b"blob 14\0fixed-contents").hexdigest()}
    assert valid_file(path, metadata)
    metadata["lfs"] = {"sha256": hashlib.sha256(b"fixed-contents").hexdigest()}
    assert valid_file(path, metadata)
    path.write_bytes(b"other-contents")
    assert not valid_file(path, metadata)
    path.write_bytes(b"short")
    assert not valid_file(path, metadata)


def test_encoder_cache_is_bounded_versioned_and_does_not_store_text(tmp_path, monkeypatch):
    calls = []
    options = []

    class Model:
        def __init__(self, path, **kwargs):
            options.append(kwargs)

        def encode(self, texts, **kwargs):
            calls.append(texts)
            return np.array([[1.0, 0.0] for text in texts])

    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=Model))
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(set_num_threads=lambda value: None))
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    (tmp_path / "model.safetensors").write_bytes(b"fake-test-weights")
    (tmp_path / "modules.json").write_text(json.dumps([{"type": "sentence_transformers.models.Transformer", "path": ""}]))
    encoder = LocalMatchingEncoder(str(tmp_path))
    assert options[0]["local_files_only"] is True
    assert options[0]["trust_remote_code"] is False
    assert options[0]["model_kwargs"]["use_safetensors"] is True
    assert encoder.similarity("private-profile", "vacancy") == 100
    assert encoder.similarity("private-profile", "vacancy") == 100
    assert len(calls) == 2
    assert all(isinstance(key, bytes) and len(key) == 32 for key in encoder._vectors)
    assert "private-profile" not in str(encoder._vectors)
    for index in range(513):
        encoder._embedding(str(index))
    assert len(encoder._vectors) == 512
    assert not next(iter(encoder._vectors.values())).flags.writeable
    previous = encoder.method
    (tmp_path / "model.safetensors").write_bytes(b"changed-test-weights")
    assert LocalMatchingEncoder(str(tmp_path)).method != previous


def test_encoder_refuses_untrusted_modules(tmp_path):
    (tmp_path / "model.safetensors").write_bytes(b"fake-test-weights")
    (tmp_path / "modules.json").write_text(json.dumps([{"type": "remote.custom.Model", "path": ""}]))
    with pytest.raises(ValueError, match="módulos no admitidos"):
        LocalMatchingEncoder(str(tmp_path))
