import json
from pathlib import Path

from jsonschema import validate

from eval.metrics import coordination_evaluation
from scenario.generate_scenario import generate


ROOT = Path(__file__).resolve().parents[2]


def test_generated_truth_matches_versioned_fixture_schema():
    _, truth = generate(seed=17)
    schema = json.loads((ROOT / "src" / "eval" / "fixture.schema.json").read_text(encoding="utf-8"))
    validate(truth, schema)
    assert truth["fixture_version"] == "1.0"
    assert truth["seed"] == 17
    checked_in = json.loads((ROOT / "src" / "samples" / "truth.json").read_text(encoding="utf-8"))
    validate(checked_in, schema)
    assert checked_in["seed"] == 42


def test_coordination_metrics_separate_benign_review_rate():
    truth = {"A": ["a", "b"], "B": [], "C": [], "D": ["d"]}
    campaigns = [{"accounts": ["a", "d"], "score": 85}]
    metrics = coordination_evaluation(truth, campaigns, {"a", "b", "d", "background"})

    assert metrics["coordination_detection"]["precision"] == 1.0
    assert metrics["coordination_detection"]["recall"] == 2 / 3
    assert metrics["coordination_detection"]["false_positive_rate"] == 0.0
    assert metrics["benign_decoy_review_rate"] == 1.0
    assert "threat_classification_accuracy" not in metrics