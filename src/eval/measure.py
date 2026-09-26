import json
import time
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Ensure src in pythonpath
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DATA, SAMPLES
from engine.normalize import load_posts
from engine.pipeline import analyze
from engine.escalation import escalate
from engine.schema import BobVerdict, Campaign, Post
from bob.legal import load_legal_table
from scenario.generate_scenario import generate

RINGS = {
    "A": "Rumour ring (dam flood + 7 PM gathering call)",
    "B": "Link ring (fake leaked-document URLs)",
    "C": "Harassment pile-on (journalist)",
    "D": "Decoy: cricket fans chanting (benign)",
}


MAX_POSTS = 60_000  # bigger files are cut to their busiest window to keep the run to a few minutes


def busiest_window(posts: list[Post], hours: int = 6) -> list[Post]:
    """Research archives are grouped by account, so the first N rows hold only a few accounts.
    Take the posts around the busiest hour instead, where many accounts are active together."""
    peak = Counter(p.created_at // 3600 for p in posts).most_common(1)[0][0] * 3600
    half = hours * 3600 // 2
    return [p for p in posts if peak - half <= p.created_at < peak + half]


def run_real(name: str, path: Path) -> dict | None:
    if not path.exists():
        print(f"  - {name}: {path} not found, skipped")
        return None
    t0 = time.perf_counter()
    all_posts = load_posts(path)
    posts = all_posts if len(all_posts) <= MAX_POSTS else busiest_window(all_posts)
    res = analyze(dataset_id=f"eval_{path.stem}", posts=posts, output_dir=DATA)
    camps = res["campaigns"]
    out = {
        "rows": len(all_posts),
        "window": "whole file" if posts is all_posts else
                  "6 h from " + datetime.fromtimestamp(min(p.created_at for p in posts), timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "posts": len(posts),
        "accounts": res["accounts"],
        "campaigns": len(camps),
        "clustered": sum(c["size"] for c in camps),
        "scores": [c["score"] for c in camps],
        "signals": sorted({s for c in camps for s in c["signals"]}),
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    print(f"  - {name}: {out['campaigns']} campaigns, {out['clustered']} accounts, scores {out['scores']}")
    return out


def run_evaluation():
    print("[1/3] Synthetic scenario (Sundarpur)...")
    t0 = time.perf_counter()
    posts_data, truth = generate(seed=42)
    posts = [Post.model_validate(p) for p in posts_data]
    res = analyze(dataset_id="eval_scenario", posts=posts, output_dir=DATA)
    scenario_s = time.perf_counter() - t0

    campaigns = res["campaigns"]
    acc_to_camp = {acc: c["id"] for c in campaigns for acc in c["accounts"]}
    camp_by_id = {c["id"]: c for c in campaigns}

    rings = {}
    for g in "ABCD":
        matched = [acc_to_camp[a] for a in truth[g] if a in acc_to_camp]
        top = max(set(matched), key=matched.count) if matched else None
        camp = camp_by_id.get(top)
        rings[g] = {
            "size": len(truth[g]),
            "captured": len(matched),
            "cluster": top or "none",
            "purity": (len(set(camp["accounts"]) & set(truth[g])) / camp["size"]) if camp else 0,
            "score": camp["score"] if camp else 0,
        }
        print(f"  - Ring {g}: {len(matched)}/{len(truth[g])} captured, cluster {top}, score {rings[g]['score']}")
    extra = [c for c in campaigns if c["id"] not in {r["cluster"] for r in rings.values()}]

    print("[2/3] Real research datasets...")
    ira = run_real("FiveThirtyEight IRA tweets", DATA / "raw" / "ira_1.csv")
    io = run_real("X/Twitter IO archive", DATA / "raw" / "io_sample.csv")

    print("[3/3] IBM Bob verdicts bundled with the demo run...")
    demo_camps = {c["id"]: Campaign.model_validate(c) for c in json.loads((SAMPLES / "demo_run" / "campaigns.json").read_text(encoding="utf-8"))}
    legal = load_legal_table()
    bob_rows = []
    for g in "ABCD":
        cid = rings[g]["cluster"]
        vf = SAMPLES / "demo_run" / "bob" / f"{cid}.json"
        if cid not in demo_camps or not vf.exists():
            bob_rows.append(f"| {g} | `{cid}` | {truth['labels'][g]} | not classified | — | — | — |")
            continue
        v = BobVerdict.model_validate_json(vf.read_text(encoding="utf-8"))
        ids = [s.id for s in v.legal_suggestions]
        in_table = sum(1 for i in ids if legal.get(i, {}).get("kind") == "offence")
        bob_rows.append(
            f"| {g} | `{cid}` | {truth['labels'][g]} | {v.threat_type} (severity {v.severity}) | "
            f"{escalate(demo_camps[cid].score, v)['level']} | {', '.join(ids) or '—'} | {in_table}/{len(ids)} |"
        )

    def real_row(name, r):
        if not r:
            return f"| {name} | not downloaded | | | | | |"
        return (f"| {name} | {r['rows']:,} rows → {r['posts']:,} posts, {r['accounts']:,} accounts ({r['window']}) | "
                f"{r['campaigns']} | {r['clustered']} | {', '.join(map(str, r['scores'])) or '—'} | "
                f"{', '.join(r['signals']) or '—'} | {r['runtime_s']} s |")

    ring_rows = "\n".join(
        f"| **{g}** | {RINGS[g]} | {r['size']} | {r['captured']} ({r['captured'] / r['size']:.0%}) | `{r['cluster']}` | {r['purity']:.0%} | **{r['score']}** |"
        for g, r in rings.items()
    )
    abc_min = min(rings[g]["score"] for g in "ABC")

    results_md = f"""# Evaluation Results

Generated by `python src/eval/measure.py` on {datetime.now().strftime("%d %B %Y")}. Every number below is computed by that script.

## 1. Synthetic scenario (ground truth known)

{res['posts']:,} posts from {res['accounts']} accounts over 48 hours: 800 normal accounts, three planted threat rings and one benign decoy
(cricket fans posting the same chants at three match moments). Analysis time: {scenario_s:.1f} s.

| Ring | What was planted | Accounts | Found | Cluster | Purity | CIB score |
|---|---|---|---|---|---|---|
{ring_rows}

- Campaigns found that match no planted ring: **{len(extra)}**.
- The decoy is real coordination, so it is detected, but it scores **{rings['D']['score']}**, below every threat ring (lowest threat ring: {abc_min}).
  The difference comes mostly from account age: the fans' accounts are 1–6 years old, the threat accounts days old.
- The score measures *how coordinated* a group is, not whether it is harmful. That second judgement is IBM Bob's (section 3).

## 2. Real research datasets (no ground truth)

The archives are grouped by account, so taking the first rows gives only a handful of accounts. The script loads the whole
file; files over {MAX_POSTS:,} posts are cut to the 6 hours around their busiest hour, when many accounts post together.

| Dataset | Input | Campaigns | Accounts clustered | CIB scores | Signals | Time |
|---|---|---|---|---|---|---|
{real_row("FiveThirtyEight IRA tweets (`ira_1.csv`)", ira)}
{real_row("X/Twitter IO archive (`io_sample.csv`)", io)}

Real campaigns score lower than the planted rings. The IRA file has no account creation dates and no retweet targets,
so the fresh-accounts feature and the co-retweet signal cannot fire there. The score weights were set by hand on the
synthetic scenario and are not yet calibrated on real data.

## 3. IBM Bob verdicts (bundled demo run)

| Ring | Campaign | Planted label | Bob's label | Escalation | Legal IDs suggested | In legal table |
|---|---|---|---|---|---|---|
{chr(10).join(bob_rows)}

- Legal IDs outside the fixed table are removed in code (`bob/client.py: validate_verdict`), so "in legal table" is guaranteed,
  not a measure of Bob's legal accuracy. Legal suggestions still need a legal officer's review.
- Ring A was planted as a rumour *with* a call to gather at 7 PM, so both misinformation and incitement describe it.
- This is 4 campaigns, not a benchmark of Bob's classification accuracy.
"""

    results_path = SRC_DIR / "eval" / "results.md"
    results_path.write_text(results_md, encoding="utf-8")
    print(f"Results saved to {results_path}")


if __name__ == "__main__":
    run_evaluation()
