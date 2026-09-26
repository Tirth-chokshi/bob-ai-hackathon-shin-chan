import json
from pathlib import Path
from scenario.generate_scenario import generate
from engine.schema import Post
from engine.pipeline import analyze


def test_scenario_analysis(tmp_path: Path):
    posts_data, truth = generate(seed=42)
    posts = [Post(**p) for p in posts_data]

    res = analyze(dataset_id="test_run", posts=posts, output_dir=tmp_path)

    # 1. Output files exist
    run_dir = tmp_path / "test_run"
    assert (run_dir / "posts.json").exists()
    assert (run_dir / "campaigns.json").exists()
    assert (run_dir / "graph.json").exists()
    assert (run_dir / "timeline.json").exists()

    campaigns = res["campaigns"]
    assert len(campaigns) >= 3

    # Check graph.json structure
    with open(run_dir / "graph.json", encoding="utf-8") as f:
        graph_data = json.load(f)
        assert "nodes" in graph_data
        assert "edges" in graph_data
        assert len(graph_data["nodes"]) > 0
        assert len(graph_data["edges"]) > 0

    # Check timeline.json structure
    with open(run_dir / "timeline.json", encoding="utf-8") as f:
        timeline_data = json.load(f)
        assert "points" in timeline_data
        assert len(timeline_data["points"]) > 0

    # 2. Check campaign detection recall for A, B, C (>= 80% in one campaign)
    acc_to_camp = {acc: c["id"] for c in campaigns for acc in c["accounts"]}
    camp_by_id = {c["id"]: c for c in campaigns}

    for group in ["A", "B", "C"]:
        truth_accs = truth[group]
        matched_camps = [acc_to_camp[acc] for acc in truth_accs if acc in acc_to_camp]
        assert len(matched_camps) >= 0.8 * len(truth_accs), f"Group {group} match rate < 80%"

        # Most frequent campaign
        top_camp_id = max(set(matched_camps), key=matched_camps.count)
        top_count = matched_camps.count(top_camp_id)
        assert top_count >= 0.8 * len(truth_accs), (
            f"Group {group} not clustered in one campaign ({top_count}/{len(truth_accs)})"
        )

        top_camp = camp_by_id[top_camp_id]
        assert top_camp["score"] >= 70, f"Group {group} score {top_camp['score']} is too low"

    # 3. Decoy D (benign fan chants) is detected as coordination but scores lowest
    d_accs = truth["D"]
    d_camps = [camp_by_id[acc_to_camp[acc]] for acc in d_accs if acc in acc_to_camp]
    assert len(d_camps) >= 0.8 * len(d_accs), "Decoy should be detected, otherwise 'ranks lowest' proves nothing"
    d_max_score = max(c["score"] for c in d_camps)

    # A, B, C minimum score
    abc_camps = [
        camp_by_id[acc_to_camp[acc]]
        for g in ["A", "B", "C"]
        for acc in truth[g]
        if acc in acc_to_camp
    ]
    abc_min_score = min(c["score"] for c in abc_camps)

    assert d_max_score < abc_min_score, (
        f"Decoy score ({d_max_score}) is not lower than threat campaigns ({abc_min_score})"
    )
