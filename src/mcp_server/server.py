import json
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Ensure src is in sys.path
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import RUNS

mcp = FastMCP("threat-intel")


@mcp.tool()
def list_datasets() -> list[dict]:
    """Lists all analysed social media datasets available in the engine."""
    datasets = []
    if not RUNS.exists():
        return datasets

    for d in sorted(RUNS.iterdir()):
        if d.is_dir() and (d / "campaigns.json").exists():
            try:
                with open(d / "campaigns.json", encoding="utf-8") as f:
                    camps = json.load(f)
                datasets.append({
                    "id": d.name,
                    "campaigns_count": len(camps),
                    "analyzed": True
                })
            except Exception:
                pass
    return datasets


@mcp.tool()
def list_campaigns(dataset_id: str) -> list[dict]:
    """Lists all detected campaigns in a dataset, sorted by highest CIB risk score first."""
    camp_file = RUNS / dataset_id / "campaigns.json"
    if not camp_file.exists():
        return []
    with open(camp_file, encoding="utf-8") as f:
        camps = json.load(f)
    return sorted(camps, key=lambda c: c.get("score", 0), reverse=True)


@mcp.tool()
def get_campaign(dataset_id: str, campaign_id: str) -> dict:
    """Returns detailed statistics, forensic features, and Bob threat verdict for a specific campaign."""
    run_dir = RUNS / dataset_id
    camp_file = run_dir / "campaigns.json"
    if not camp_file.exists():
        return {"error": f"Dataset {dataset_id} not found"}

    with open(camp_file, encoding="utf-8") as f:
        camps = json.load(f)

    target = next((c for c in camps if c["id"] == campaign_id), None)
    if not target:
        return {"error": f"Campaign {campaign_id} not found"}

    result = dict(target)
    # Check for cached Bob verdict
    verdict_file = run_dir / "bob" / f"{campaign_id}.json"
    if verdict_file.exists():
        try:
            with open(verdict_file, encoding="utf-8") as vf:
                result["verdict"] = json.load(vf)
        except Exception:
            pass

    return result


@mcp.tool()
def get_posts(dataset_id: str, campaign_id: str, limit: int = 10) -> list[dict]:
    """Returns sample posts belonging to a campaign, ordered chronologically (oldest first)."""
    run_dir = RUNS / dataset_id
    camp_file = run_dir / "campaigns.json"
    posts_file = run_dir / "posts.json"

    if not camp_file.exists() or not posts_file.exists():
        return []

    with open(camp_file, encoding="utf-8") as f:
        camps = json.load(f)
    target = next((c for c in camps if c["id"] == campaign_id), None)
    if not target:
        return []

    target_post_ids = set(target.get("post_ids", []))
    with open(posts_file, encoding="utf-8") as f:
        all_posts = json.load(f)

    camp_posts = [p for p in all_posts if p.get("post_id") in target_post_ids]
    camp_posts.sort(key=lambda p: (p.get("created_at", 0), p.get("post_id", "")))
    return camp_posts[:limit]


@mcp.tool()
def timeline(dataset_id: str, campaign_id: str | None = None) -> list[dict]:
    """Returns activity volume timeline points per 60-second window."""
    timeline_file = RUNS / dataset_id / "timeline.json"
    if not timeline_file.exists():
        return []

    with open(timeline_file, encoding="utf-8") as f:
        data = json.load(f)

    points = data.get("points", [])
    if not campaign_id:
        return points

    # Filter to requested campaign
    filtered = []
    for pt in points:
        filtered.append({
            "t": pt["t"],
            "total": pt.get("total", 0),
            campaign_id: pt.get(campaign_id, 0)
        })
    return filtered


@mcp.tool()
def account_profile(dataset_id: str, account_id: str) -> dict:
    """Returns the operational profile of an account: age, post history, and campaign memberships."""
    run_dir = RUNS / dataset_id
    posts_file = run_dir / "posts.json"
    camp_file = run_dir / "campaigns.json"

    if not posts_file.exists():
        return {"error": f"Dataset {dataset_id} not found"}

    with open(posts_file, encoding="utf-8") as f:
        all_posts = json.load(f)

    acc_posts = [p for p in all_posts if p.get("account_id") == account_id]
    if not acc_posts:
        return {"account_id": account_id, "found": False}

    username = acc_posts[0].get("username", account_id)
    created_at = acc_posts[0].get("account_created_at")
    first_post_time = min(p.get("created_at", 0) for p in acc_posts)
    last_post_time = max(p.get("created_at", 0) for p in acc_posts)

    campaign_memberships = []
    if camp_file.exists():
        with open(camp_file, encoding="utf-8") as f:
            camps = json.load(f)
        for c in camps:
            if account_id in c.get("accounts", []):
                campaign_memberships.append(c["id"])

    return {
        "account_id": account_id,
        "username": username,
        "total_posts_in_dataset": len(acc_posts),
        "first_seen": first_post_time,
        "last_seen": last_post_time,
        "account_created_at": created_at,
        "associated_campaigns": campaign_memberships,
        "recent_samples": [p.get("text", "") for p in acc_posts[:3]]
    }


if __name__ == "__main__":
    mcp.run()
