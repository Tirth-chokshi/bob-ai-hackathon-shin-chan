"""Evaluation metrics with coordination and analyst-triage outcomes kept separate."""


def binary_metrics(expected: set[str], predicted: set[str], universe: set[str]) -> dict[str, float | int]:
    if not expected <= universe or not predicted <= universe:
        raise ValueError("Expected and predicted labels must be within the evaluation universe")
    true_positive = len(expected & predicted)
    false_positive = len(predicted - expected)
    false_negative = len(expected - predicted)
    true_negative = len(universe - expected - predicted)
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
        "precision": true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0,
        "recall": true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0,
        "false_positive_rate": false_positive / (false_positive + true_negative)
        if false_positive + true_negative else 0.0,
    }


def coordination_evaluation(truth: dict, campaigns: list[dict], account_universe: set[str],
                            score_threshold: int = 80) -> dict:
    coordinated = set().union(*(set(truth[group]) for group in "ABCD"))
    detected = {account for campaign in campaigns for account in campaign["accounts"]}
    high_score = {account for campaign in campaigns if campaign["score"] >= score_threshold
                  for account in campaign["accounts"]}
    threat_accounts = set().union(*(set(truth[group]) for group in "ABC"))
    benign_accounts = set(truth["D"])
    return {
        "coordination_detection": binary_metrics(coordinated, detected, account_universe),
        "score_threshold": score_threshold,
        "threat_ring_review_rate": len(threat_accounts & high_score) / len(threat_accounts) if threat_accounts else 0.0,
        "benign_decoy_review_rate": len(benign_accounts & high_score) / len(benign_accounts) if benign_accounts else 0.0,
    }