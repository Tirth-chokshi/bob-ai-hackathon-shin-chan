import json
import mimetypes
import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure correct MIME types on Windows
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import BOB_API_KEY, WEB_DIST, RUNS, SAMPLES
from engine.normalize import load_posts
from engine.pipeline import analyze
from engine.schema import Campaign, Post
from engine.escalation import escalate
from bob.client import classify
from brief.render import render_brief


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup demo data on startup if not already analyzed
    demo_run = RUNS / "demo"
    demo_bundled = SAMPLES / "demo_run"
    scenario_csv = SAMPLES / "scenario_posts.csv"

    if not demo_run.exists():
        if demo_bundled.exists():
            shutil.copytree(demo_bundled, demo_run)
        elif scenario_csv.exists():
            posts = load_posts(scenario_csv)
            analyze("demo", posts)
    yield


app = FastAPI(title="Social Media Threat Intelligence Engine", lifespan=lifespan)


@app.get("/api/status")
def status():
    return {"bob_configured": bool(BOB_API_KEY), "version": "0.1.0"}


@app.get("/api/datasets/demo")
def get_demo_datasets():
    demo_run = RUNS / "demo"
    posts_path = demo_run / "posts.json"
    is_analyzed = (demo_run / "campaigns.json").exists()

    post_count = 4538
    acc_count = 956
    if posts_path.exists():
        try:
            with open(posts_path, encoding="utf-8") as f:
                posts_data = json.load(f)
                post_count = len(posts_data)
                acc_count = len({p["account_id"] for p in posts_data})
        except Exception:
            pass

    return [
        {
            "id": "demo",
            "name": "Sundarpur scenario (synthetic)",
            "posts": post_count,
            "accounts": acc_count,
            "analyzed": is_analyzed,
        }
    ]


@app.post("/api/datasets")
async def upload_dataset(file: UploadFile = File(...)):
    dataset_id = f"u_{uuid.uuid4().hex[:6]}"
    dataset_dir = RUNS / dataset_id
    dataset_dir.mkdir(parents=True, exist_ok=True)
    temp_file = dataset_dir / f"upload_{file.filename}"

    content = await file.read()
    with open(temp_file, "wb") as f:
        f.write(content)

    try:
        posts = load_posts(temp_file)
    except Exception as e:
        shutil.rmtree(dataset_dir, ignore_errors=True)
        raise HTTPException(status_code=422, detail=f"Failed to parse dataset: {e}")

    with open(dataset_dir / "posts.json", "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in posts], f, indent=2)

    unique_accounts = {p.account_id for p in posts}
    return {
        "dataset_id": dataset_id,
        "posts": len(posts),
        "accounts": len(unique_accounts),
    }


@app.post("/api/datasets/{dataset_id}/analyze")
def run_analysis(dataset_id: str):
    run_dir = RUNS / dataset_id
    posts_file = run_dir / "posts.json"

    if not posts_file.exists():
        if dataset_id == "demo" and (SAMPLES / "scenario_posts.csv").exists():
            posts = load_posts(SAMPLES / "scenario_posts.csv")
        else:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    else:
        with open(posts_file, encoding="utf-8") as f:
            posts = load_posts(posts_file)

    result = analyze(dataset_id=dataset_id, posts=posts)
    return result


@app.get("/api/datasets/{dataset_id}/graph")
def get_graph(dataset_id: str):
    graph_file = RUNS / dataset_id / "graph.json"
    if not graph_file.exists():
        raise HTTPException(status_code=404, detail="Graph not found. Run analysis first.")
    with open(graph_file, encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/datasets/{dataset_id}/timeline")
def get_timeline(dataset_id: str):
    timeline_file = RUNS / dataset_id / "timeline.json"
    if not timeline_file.exists():
        raise HTTPException(status_code=404, detail="Timeline not found. Run analysis first.")
    with open(timeline_file, encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/datasets/{dataset_id}/campaigns/{cid}")
def get_campaign(dataset_id: str, cid: str):
    run_dir = RUNS / dataset_id
    campaigns_file = run_dir / "campaigns.json"
    posts_file = run_dir / "posts.json"

    if not campaigns_file.exists() or not posts_file.exists():
        raise HTTPException(status_code=404, detail="Campaigns or posts not found")

    with open(campaigns_file, encoding="utf-8") as f:
        campaigns_data = json.load(f)

    target_campaign = next((c for c in campaigns_data if c["id"] == cid), None)
    if not target_campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {cid} not found")

    with open(posts_file, encoding="utf-8") as f:
        all_posts = json.load(f)

    target_post_ids = set(target_campaign["post_ids"])
    campaign_posts = [p for p in all_posts if p["post_id"] in target_post_ids]
    campaign_posts.sort(key=lambda p: (p["created_at"], p["post_id"]))
    sample_posts = [
        {
            "post_id": p["post_id"],
            "account_id": p["account_id"],
            "username": p["username"] if p["username"].startswith("@") else f"@{p['username']}",
            "created_at": p["created_at"],
            "text": p["text"],
        }
        for p in campaign_posts[:10]
    ]

    response_data = dict(target_campaign)
    response_data["sample_posts"] = sample_posts
    return response_data


@app.post("/api/datasets/{dataset_id}/campaigns/{cid}/classify")
def classify_campaign(dataset_id: str, cid: str):
    run_dir = RUNS / dataset_id
    campaigns_file = run_dir / "campaigns.json"
    posts_file = run_dir / "posts.json"

    if not campaigns_file.exists() or not posts_file.exists():
        raise HTTPException(status_code=404, detail="Campaigns or posts not found")

    with open(campaigns_file, encoding="utf-8") as f:
        campaigns_data = json.load(f)

    target_raw = next((c for c in campaigns_data if c["id"] == cid), None)
    if not target_raw:
        raise HTTPException(status_code=404, detail=f"Campaign {cid} not found")

    campaign = Campaign.model_validate(target_raw)

    with open(posts_file, encoding="utf-8") as f:
        all_posts_data = json.load(f)
    all_posts = [Post.model_validate(p) for p in all_posts_data]

    camp_post_ids = set(campaign.post_ids)
    sample_posts = [p for p in all_posts if p.post_id in camp_post_ids]
    sample_posts.sort(key=lambda p: (p.created_at, p.post_id))

    try:
        verdict, cost, is_cached = classify(run_dir, campaign, sample_posts[:10])
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification error: {e}")

    esc = escalate(campaign.score, verdict)

    return {
        "verdict": verdict.model_dump(),
        "escalation": esc,
        "cached": is_cached,
        "cost": cost,
    }


@app.get("/api/datasets/{dataset_id}/brief", response_class=HTMLResponse)
def get_brief(dataset_id: str):
    try:
        html_content = render_brief(dataset_id)
        return HTMLResponse(content=html_content)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate brief: {e}")


# Frontend static files mounting
if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
else:
    @app.get("/")
    def frontend_missing():
        return HTMLResponse("Frontend not built — run <code>npm ci && npm run build</code> in src/web.")
