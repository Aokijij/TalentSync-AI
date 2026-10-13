"""Optional offline NER. Neural suggestions never become confirmed profile data."""
import json
import math
import os
import subprocess
import threading
from pathlib import Path

LABELS = {"job title": "role", "employer": "company", "degree": "degree", "university": "institution", "technical skill": "skill", "date": "date"}
METHOD = "gliner-multi-v2.1-review-v1"
MAX_CHARS = 30_000
_gate = threading.BoundedSemaphore(1)


def chunks(text, words=128, overlap=24):
    """Overlapping exact-source windows; retain offsets rather than rewritten text."""
    import re
    tokens = list(re.finditer(r"\S+", text))
    for index in range(0, len(tokens), words - overlap):
        end = min(index + words, len(tokens))
        yield tokens[index].start(), text[tokens[index].start():tokens[end - 1].end()]
        if end == len(tokens):
            break


def validated_entities(text, rows):
    entities = {}
    if not isinstance(rows, list):
        return []
    for row in rows[:2000]:
        if not isinstance(row, dict):
            continue
        start, end, label, score = (row.get(key) for key in ("start", "end", "label", "score"))
        if (type(start) is not int or type(end) is not int or not isinstance(label, str) or label not in LABELS
                or not 0 <= start < end <= len(text) or end - start > 180
                or type(score) not in (int, float) or not math.isfinite(score) or not .5 <= score <= 1
                or row.get("text") != text[start:end] or not text[start:end].strip()):
            continue
        key = (start, end, label)
        entity = {"kind": LABELS[label], "text": text[start:end], "start": start, "end": end,
                  "score": round(score, 3), "excerpt": text[max(0, start - 100):min(len(text), end + 100)]}
        if entity["kind"] == "skill":
            from app.domain.services.skill_context import skill_mentions
            clause_end = text.find("\n", end)
            states = {item["state"] for item in skill_mentions(text[:clause_end if clause_end >= 0 else len(text)], [entity["text"]])}
            entity["context"] = next((state for state in ("negated", "learning", "project", "applied", "declared") if state in states), "declared")
        if key not in entities or entity["score"] > entities[key]["score"]:
            entities[key] = entity
    return sorted(entities.values(), key=lambda item: (item["start"], item["kind"]))[:300]


def extract_entities(text, *, model_path=None, python_path=None, timeout=None):
    from app.core.config import settings
    folder = Path(model_path or settings.cv_entity_model_path) if model_path or settings.cv_entity_model_path else None
    python = Path(python_path or settings.cv_entity_python) if python_path or settings.cv_entity_python else None
    result = {"method": METHOD, "status": "disabled", "entities": [], "truncated": len(text) > MAX_CHARS}
    if folder is None or python is None:
        return result
    if not folder.is_dir() or not python.is_file() or not (folder / "model.safetensors").is_file():
        return {**result, "status": "unavailable"}
    if not _gate.acquire(blocking=False):
        return {**result, "status": "busy"}
    try:
        # No integration keys, account tokens, inherited Python paths or CV files.
        env = {key: value for key, value in os.environ.items() if key.upper() in {
            "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA"}}
        env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
                   TOKENIZERS_PARALLELISM="false", PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        output = subprocess.run([str(python.resolve()), str(Path(__file__).with_name("cv_entity_worker.py")), str(folder.resolve())],
                                input=json.dumps({"text": text[:MAX_CHARS]}, ensure_ascii=False), text=True, encoding="utf-8",
                                capture_output=True, timeout=timeout or settings.cv_entity_timeout_seconds, env=env,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0, check=True)
        if len(output.stdout) > 1_000_000:
            raise ValueError("Unexpected entity output")
        payload = json.loads(output.stdout)
        return {**result, "status": "ready", "entities": validated_entities(text[:MAX_CHARS], payload["entities"])}
    except subprocess.TimeoutExpired:
        return {**result, "status": "timeout"}
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError):
        # Never log subprocess output: it can contain private resume fragments.
        return {**result, "status": "unavailable"}
    finally:
        _gate.release()
