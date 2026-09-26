import json
import logging
import mimetypes
import re
import shutil
import threading
import time
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

from config import WEB_DIST, RUNS, SAMPLES
from engine.normalize import load_posts
from engine.pipeline import analyze, STAGES
from engine.schema import Campaign, Post
from engine.escalation import escalate
from bob.client import BobNotConfigured, cached_verdict, classify, is_bob_configured
from brief.render import render_brief

log = logging.getLogger(__name__)
DEMO_NAME = "Demo dataset (pre-analysed)"  # shown in the datasets list

# ponytail: in-memory job table for this one server process; a restart forgets running jobs (re-run the analysis)
JOBS: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Copy the pre-analysed demo on first start
    demo_run = RUNS / "demo"
    if not demo_run.exists() and (SAMPLES / "demo_run").exists():
        shutil.copytree(SAMPLES / "demo_run", demo_run)
    yield


app = FastAPI(title="Social Media Threat Intelligence Engine", lifespan=lifespan)


def run_dir_for(dataset_id: str) -> Path:
    # dataset_id becomes a folder name, so allow only simple IDs (no "..", slashes or drive letters)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", dataset_id):
        raise HTTPException(status_code=400, detail="Invalid dataset id")
    return RUNS / dataset_id


def read_json(path: Path, missing: str):
    if not path.exists():
        raise HTTPException(status_code=404, detail=missing)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def source_file(dataset_id: str, run_dir: Path) -> Path:
    """The posts a dataset is analysed from: the uploaded file, or the scenario CSV for the demo."""
    if dataset_id == "demo":
        return SAMPLES / "scenario_posts.csv"
    uploads = sorted(run_dir.glob("upload*"))
    if uploads:
        return uploads[0]
    raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")


def dataset_meta(run_dir: Path) -> dict:
    """Name and counts, stored in meta.json so listing never re-reads the posts."""
    meta_path = run_dir / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    if "posts" not in meta:  # runs from older versions: count once, then remember
        posts = load_posts(source_file(run_dir.name, run_dir))
        meta.update(posts=len(posts), accounts=len({p.account_id for p in posts}))
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
    return meta


def load_campaign(run_dir: Path, cid: str) -> Campaign:
    campaigns = read_json(run_dir / "campaigns.json", "Campaigns not found. Run analysis first.")
    target = next((c for c in campaigns if c["id"] == cid), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Campaign {cid} not found")
    return Campaign.model_validate(target)


def load_samples(run_dir: Path, cid: str) -> list[dict]:
    samples = read_json(run_dir / "samples.json", "This dataset was analysed by an older version. Run the analysis again.")
    return samples.get(cid, [])


def campaign_summary(c: dict) -> dict:
    """Campaign without its (possibly huge) account and post ID lists."""
    return {**{k: v for k, v in c.items() if k not in ("accounts", "post_ids")}, "post_count": len(c["post_ids"])}


def run_job(dataset_id: str, source: Path):
    job = JOBS[dataset_id]

    def progress(stage: str):
        job["step"] = STAGES.index(stage)

    try:
        progress("Reading posts")
        result = analyze(dataset_id, load_posts(source), progress=progress)
        job.update(state="done", finished=time.time(), campaigns=len(result["campaigns"]), runtime_ms=result["runtime_ms"])
    except Exception as e:
        log.exception("Analysis of %s failed", dataset_id)
        job.update(state="error", error=str(e), finished=time.time())


@app.get("/api/status")
def status():
    return {"bob_configured": is_bob_configured(), "version": "0.2.0"}


@app.get("/api/datasets")
def list_datasets():
    datasets = []
    for d in sorted(RUNS.iterdir()) if RUNS.exists() else []:
        if not d.is_dir():
            continue
        try:
            meta = dataset_meta(d)
        except Exception:
            log.exception("Skipping unreadable dataset %s", d.name)
            continue
        datasets.append({
            "id": d.name,
            "name": meta.get("name") or (DEMO_NAME if d.name == "demo" else d.name),
            "posts": meta["posts"],
            "accounts": meta["accounts"],
            # results from older versions lack samples.json and must be re-run
            "analyzed": (d / "campaigns.json").exists() and (d / "samples.json").exists(),
            "job": JOBS.get(d.name, {"state": "idle"}),
        })
    return sorted(datasets, key=lambda d: d["id"] != "demo")  # demo first


@app.post("/api/datasets")
def upload_dataset(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".csv", ".json"):
        raise HTTPException(status_code=422, detail="Upload a .csv or .json file")

    dataset_id = f"u_{uuid.uuid4().hex[:6]}"
    dataset_dir = RUNS / dataset_id
    dataset_dir.mkdir(parents=True, exist_ok=True)
    upload_path = dataset_dir / f"upload{suffix}"  # never build paths from the client's filename
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        posts = load_posts(upload_path)
        if not posts:
            raise ValueError("no posts found")
    except Exception as e:
        shutil.rmtree(dataset_dir, ignore_errors=True)
        raise HTTPException(status_code=422, detail=f"Could not read this file: {e}")

    meta = {"name": Path(file.filename).name, "posts": len(posts), "accounts": len({p.account_id for p in posts})}
    (dataset_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return {"dataset_id": dataset_id, **meta}


@app.delete("/api/datasets/{dataset_id}")
def delete_dataset(dataset_id: str):
    run_dir = run_dir_for(dataset_id)
    if dataset_id == "demo":
        raise HTTPException(status_code=400, detail="The demo dataset can't be deleted")
    if JOBS.get(dataset_id, {}).get("state") == "running":
        raise HTTPException(status_code=409, detail="Wait for the analysis to finish")
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    shutil.rmtree(run_dir)
    JOBS.pop(dataset_id, None)
    return {"deleted": dataset_id}


@app.post("/api/datasets/{dataset_id}/analyze", status_code=202)
def start_analysis(dataset_id: str):
    """Starts analysis in the background; poll /job for progress."""
    source = source_file(dataset_id, run_dir_for(dataset_id))
    if JOBS.get(dataset_id, {}).get("state") != "running":
        JOBS[dataset_id] = {"state": "running", "step": 0, "stages": STAGES, "started": time.time()}
        threading.Thread(target=run_job, args=(dataset_id, source), daemon=True).start()
    return JOBS[dataset_id]


@app.get("/api/datasets/{dataset_id}/job")
def job_status(dataset_id: str):
    run_dir_for(dataset_id)
    return JOBS.get(dataset_id, {"state": "idle"})


@app.get("/api/datasets/{dataset_id}/campaigns")
def get_campaigns(dataset_id: str):
    run_dir = run_dir_for(dataset_id)
    campaigns = read_json(run_dir / "campaigns.json", "Campaigns not found. Run analysis first.")
    result = []
    for c in campaigns:
        v = cached_verdict(run_dir, c["id"])
        assessment = {"threat_type": v.threat_type, "severity": v.severity,
                      "level": escalate(c["score"], v)["level"]} if v else None
        result.append({**campaign_summary(c), "assessment": assessment})
    return result


@app.get("/api/datasets/{dataset_id}/graph")
def get_graph(dataset_id: str):
    return read_json(run_dir_for(dataset_id) / "graph.json", "Graph not found. Run analysis first.")


@app.get("/api/datasets/{dataset_id}/timeline")
def get_timeline(dataset_id: str):
    return read_json(run_dir_for(dataset_id) / "timeline.json", "Timeline not found. Run analysis first.")


@app.get("/api/datasets/{dataset_id}/campaigns/{cid}")
def get_campaign(dataset_id: str, cid: str):
    run_dir = run_dir_for(dataset_id)
    campaign = load_campaign(run_dir, cid).model_dump()
    return {**campaign_summary(campaign), "accounts": campaign["accounts"], "sample_posts": load_samples(run_dir, cid)}


@app.get("/api/datasets/{dataset_id}/campaigns/{cid}/verdict")
def get_verdict(dataset_id: str, cid: str):
    """Cached Bob verdict only; never calls Bob (so selecting a campaign costs nothing)."""
    run_dir = run_dir_for(dataset_id)
    campaign = load_campaign(run_dir, cid)
    verdict = cached_verdict(run_dir, cid)
    if not verdict:
        raise HTTPException(status_code=404, detail="Not classified yet")
    return {"verdict": verdict.model_dump(), "escalation": escalate(campaign.score, verdict), "cached": True, "cost": 0.0}


@app.post("/api/datasets/{dataset_id}/campaigns/{cid}/classify")
def classify_campaign(dataset_id: str, cid: str):
    run_dir = run_dir_for(dataset_id)
    campaign = load_campaign(run_dir, cid)
    sample_posts = [Post.model_validate(p) for p in load_samples(run_dir, cid)[:20]]

    try:
        verdict, cost, is_cached = classify(run_dir, campaign, sample_posts)
    except BobNotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:  # Bob failed or never gave a valid answer
        raise HTTPException(status_code=502, detail=str(e))

    return {
        "verdict": verdict.model_dump(),
        "escalation": escalate(campaign.score, verdict),
        "cached": is_cached,
        "cost": cost,
    }


@app.get("/api/datasets/{dataset_id}/brief", response_class=HTMLResponse)
def get_brief(dataset_id: str):
    run_dir_for(dataset_id)
    try:
        return HTMLResponse(content=render_brief(dataset_id))
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
