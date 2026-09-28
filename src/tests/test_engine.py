from pathlib import Path
from engine.pipeline import analyze
from engine.xstore import load_posts
from tests.fixtures import planted_response, write_json


def test_planted_rings_found_and_ordinary_posters_left_alone(tmp_path: Path):
    response, truth = planted_response()
    posts = load_posts(write_json(tmp_path / "search.json", response))
    res = analyze(dataset_id="test_run", posts=posts, output_dir=tmp_path)

    run_dir = tmp_path / "test_run"
    for f in ("campaigns.json", "samples.json", "graph.json", "timeline.json"):
        assert (run_dir / f).exists(), f
    assert not (run_dir / "posts.json").exists()  # posts live only in the X database

    acc_to_camp = {a: c for c in res["campaigns"] for a in c["accounts"]}
    for group in ("R", "H"):
        found = [acc_to_camp[a]["id"] for a in truth[group] if a in acc_to_camp]
        assert len(found) >= 0.8 * len(truth[group]) and len(set(found)) == 1, f"ring {group} not found as one campaign"
        camp = acc_to_camp[truth[group][0]]
        assert set(camp["accounts"]) <= set(truth[group]), f"ring {group} mixed with other accounts"

    assert not any(a in acc_to_camp for a in truth["organic"])  # independent posters are not a campaign
    assert len(res["campaigns"]) == 2

    # The copy-paste ring: flagged once it had repeated itself, days-old accounts, all on X
    ring = acc_to_camp[truth["R"][0]]
    assert ring["first_seen"] < ring["detected_at"] <= ring["last_seen"]
    assert ring["new_account_share"] == 1.0
    assert [p["name"] for p in ring["platform_path"]] == ["x"]
    assert ring["languages"] == {"hi": 40} and ring["top_hashtag"] == "#RajpuraBachao"
    assert "co_reply" in acc_to_camp[truth["H"][0]]["signals"]
