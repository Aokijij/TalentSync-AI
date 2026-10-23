import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("pilot_evaluation", ROOT / "scripts/pilot_evaluation.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


def example():
    return json.loads((ROOT / "docs/pilot/synthetic-example.json").read_text(encoding="utf-8"))


def test_synthetic_perfect_scores_are_never_claimed_as_real_validation():
    result = pilot.evaluate(example())
    assert result["metrics"]["extraction_f1"] == result["metrics"]["ranking_ndcg_at_5"] == 1
    assert result["status"] == "synthetic_example" and not result["real_world_validated"]
    assert not result["minimum_sample_reached"]
    assert "python" not in json.dumps(result).lower()


def test_false_entities_and_irrelevant_first_ranking_reduce_quality():
    data = example()
    data["samples"][0]["extraction"]["skills"]["actual"] = ["python", "invented-skill"]
    data["samples"][0]["ranking"] = ["J003", "J002", "J001"]
    result = pilot.evaluate(data)
    assert result["metrics"]["extraction_f1"] == .75
    assert result["metrics"]["ranking_ndcg_at_5"] < .8


@pytest.mark.parametrize("change", ["consent", "duplicate", "invalid-label", "duplicate-ranking", "missing-result"])
def test_pilot_rejects_unconsented_or_unusable_rows(change):
    data = example()
    if change == "consent":
        data["mode"] = "consented_pilot"
    elif change == "duplicate":
        data["samples"][1]["id"] = "S001"
    elif change == "invalid-label":
        data["samples"][0]["relevance"]["J001"] = 99
    elif change == "duplicate-ranking":
        data["samples"][0]["ranking"] = ["J001", "J001"]
    else:
        del data["samples"][0]["flow_completed"]
    with pytest.raises(ValueError):
        pilot.evaluate(data)
