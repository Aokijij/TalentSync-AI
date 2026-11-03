"""Reproducible diagnostic comparison, not a production accuracy claim."""
import json
import time
from pathlib import Path

from app.domain.services.skill_context import fold
from app.infrastructure.nlp.cv_entities import LABELS, METHOD, extract_entities
from app.infrastructure.nlp.text_processor import text_processor

ROOT = Path(__file__).resolve().parents[2]
KINDS = ("role", "company", "degree", "institution", "skill")


def canonical(value):
    return " ".join(fold(value).split()).strip(" .,:;")


def metrics(expected, predicted):
    tp = len(expected & predicted)
    fp, fn = len(predicted - expected), len(expected - predicted)
    precision, recall = tp / (tp + fp) if tp + fp else 0, tp / (tp + fn) if tp + fn else 0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0}


def baseline(text):
    experiences, studies, _ = text_processor.extract_resume_items(text)
    result = {kind: set() for kind in KINDS}
    profession = text_processor.extract_profession(text)
    if profession:
        result["role"].add(canonical(profession))
    for row in experiences:
        for field in ("role", "company"):
            if row.get(field):
                result[field].add(canonical(row[field]))
    for row in studies:
        for field in ("degree", "institution"):
            if row.get(field):
                result[field].add(canonical(row[field]))
    # This benchmark measures mentions, including learning/negated mentions.
    result["skill"] = {canonical(skill) for skill in text_processor.extract_skills(text)}
    return result


def main():
    fixture = ROOT / "backend/tests/fixtures/cv_entities_v1.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))
    records = []
    for case in data["cases"]:
        started = time.perf_counter()
        result = extract_entities(case["text"], model_path=str(ROOT / ".local/models/gliner_multi-v2.1"), python_path=str(ROOT / ".local/cv-runtime/Scripts/python.exe"))
        if result["status"] != "ready":
            raise SystemExit(f"Entity inference failed: {result['status']}")
        actual = {kind: {canonical(row["text"]) for row in result["entities"] if row["kind"] == kind} for kind in KINDS}
        expected = {kind: {canonical(value) for value in case["expected"][kind]} for kind in KINDS}
        current = baseline(case["text"])
        records.append({"id": case["id"], "split": case["split"], "seconds": round(time.perf_counter() - started, 2),
                        "expected": {key: sorted(value) for key, value in expected.items()},
                        "rules": {key: sorted(value) for key, value in current.items()},
                        "neural": {key: sorted(value) for key, value in actual.items()}})
        print(f"{case['id']}: {records[-1]['seconds']} s", flush=True)
    summary = {}
    for split in ("development", "holdout"):
        summary[split] = {}
        selected = [row for row in records if row["split"] == split]
        for method in ("rules", "neural"):
            expected = {(row["id"], kind, value) for row in selected for kind in KINDS for value in row["expected"][kind]}
            predicted = {(row["id"], kind, value) for row in selected for kind in KINDS for value in row[method][kind]}
            summary[split][method] = {"micro": metrics(expected, predicted), "by_field": {
                kind: metrics({item for item in expected if item[1] == kind}, {item for item in predicted if item[1] == kind}) for kind in KINDS}}
    report = {"fixture": data["version"], "method": METHOD, "labels": LABELS, "threshold": .5, "description": data["description"],
              "protocol": "Exact normalized entity strings per document/type; duplicate mentions counted once. No record linking, OCR or confirmed-skill accuracy measured. Independent neural suggestions are compared with rules; outputs are not merged.",
              "summary": summary, "cases": records}
    target = ROOT / ".local/verification/cv-entities-evaluation.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
