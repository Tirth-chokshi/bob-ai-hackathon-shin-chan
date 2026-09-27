import json
import hashlib
import logging
import mimetypes
import re
import shutil
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

# Ensure correct MIME types on Windows
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
from fastapi import FastAPI, HTTPException, UploadFile, File, Body
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import WEB_DIST, RUNS, SAMPLES, STREAMS, STREAM_WINDOW_SECONDS, STREAM_RETENTION_SECONDS, MIN_EDGE_WEIGHT
from engine.normalize import load_posts, load_rows
from engine.pipeline import analyze, STAGES
from engine.schema import Campaign, Post
from engine.coordination import build_graph
from engine.campaigns import find_campaigns
from engine.streaming import close as close_stream, ingest as ingest_stream_post, read_state as read_stream_state, save_alert
from engine.escalation import escalate
from bob.client import BobNotConfigured, cached_verdict, classify, is_bob_configured
from brief.render import render_brief
from engine.workflow import get_review, list_audit_events, record_review

log = logging.getLogger(__name__)
DEMO_NAME = "Demo dataset (pre-analysed)"  # shown in the datasets list

# ponytail: in-memory job table for this one server process; a restart forgets running jobs (re-run the analysis)
JOBS: dict[str, dict] = {}
STREAM_DB = STREAMS / "streams.sqlite"
STREAM_LOCK = threading.RLock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Copy the pre-analysed demo on first start
    demo_run = RUNS / "demo"
    if not demo_run.exists() and (SAMPLES / "demo_run").exists():
        shutil.copytree(SAMPLES / "demo_run", demo_run)
    yield


app = FastAPI(title="Social Media Threat Intelligence Engine", lifespan=lifespan)


class ReviewRequest(BaseModel):
    reviewer_id: str = Field(min_length=1, max_length=120)
    reviewer_role: Literal["analyst", "supervisor"]
    decision: Literal["accept", "downgrade", "reject"]
    reason: str = Field(default="", max_length=2000)


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
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        result = analyze(dataset_id, load_posts(source), progress=progress, input_sha256=source_hash)
        job.update(state="done", finished=time.time(), campaigns=len(result["campaigns"]), runtime_ms=result["runtime_ms"])
    except Exception as e:
        log.exception("Analysis of %s failed", dataset_id)
        job.update(state="error", error=str(e), finished=time.time())


@app.get("/api/status")
def status():
    return {"bob_configured": is_bob_configured(), "version": "0.3.0"}


def validate_stream_id(stream_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", stream_id):
        raise HTTPException(status_code=400, detail="Invalid stream id")
    return stream_id


def recompute_stream(stream_id: str, posts: list[Post], latest: int) -> dict:
    window_start = latest - STREAM_WINDOW_SECONDS
    active_posts = [post for post in posts if window_start <= post.created_at <= latest]
    stream_dir = STREAMS / stream_id
    stream_dir.mkdir(parents=True, exist_ok=True)
    graph = build_graph(active_posts, db_path=stream_dir / "coordination.sqlite",
                        window=STREAM_WINDOW_SECONDS, min_weight=MIN_EDGE_WEIGHT)
    campaigns = find_campaigns(graph, active_posts, min_size=5, window=STREAM_WINDOW_SECONDS)
    now = time.time()
    return {
        "stream_id": stream_id,
        "status": "provisional",
        "review_required": True,
        "window_started_at": window_start,
        "window_ended_at": latest,
        "last_updated_at": now,
        "retained_posts": len(posts),
        "window_posts": len(active_posts),
        "campaigns": [
            {"id": campaign.id, "accounts": campaign.size, "post_count": len(campaign.post_ids),
             "coordination_score": campaign.score, "signals": campaign.signals,
             "first_seen": campaign.first_seen, "last_seen": campaign.last_seen}
            for campaign in campaigns
        ],
    }


@app.post("/api/streams/{stream_id}/posts")
def add_stream_post(stream_id: str, payload: dict = Body(...)):
    validate_stream_id(stream_id)
    if not payload:
        raise HTTPException(status_code=422, detail="Post payload cannot be empty")
    try:
        [post] = load_rows([payload], list(payload), source_name=f"stream:{stream_id}", source_id=stream_id)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    with STREAM_LOCK:
        try:
            duplicate, posts, latest = ingest_stream_post(STREAM_DB, stream_id, post, STREAM_RETENTION_SECONDS)
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))
        alert = recompute_stream(stream_id, posts, latest)
        save_alert(STREAM_DB, stream_id, alert)
    return {"duplicate": duplicate, "alert": alert}


@app.get("/api/streams/{stream_id}/alerts")
def get_stream_alerts(stream_id: str):
    validate_stream_id(stream_id)
    state = read_stream_state(STREAM_DB, stream_id)
    if not state:
        raise HTTPException(status_code=404, detail="Stream not found")
    stream, _ = state
    return stream["alert"]


@app.get("/api/streams/{stream_id}/timeline")
def get_stream_timeline(stream_id: str):
    validate_stream_id(stream_id)
    state = read_stream_state(STREAM_DB, stream_id)
    if not state:
        raise HTTPException(status_code=404, detail="Stream not found")
    stream, posts = state
    buckets: dict[int, int] = {}
    for post in posts:
        if post.created_at >= (stream["latest_event_time"] or 0) - STREAM_WINDOW_SECONDS:
            bucket_time = post.created_at // 60 * 60
            buckets[bucket_time] = buckets.get(bucket_time, 0) + 1
    return {"stream_id": stream_id, "bucket_seconds": 60,
            "points": [{"t": t, "total": count} for t, count in sorted(buckets.items())]}


@app.post("/api/streams/{stream_id}/close")
def finish_stream(stream_id: str):
    validate_stream_id(stream_id)
    if not close_stream(STREAM_DB, stream_id):
        state = read_stream_state(STREAM_DB, stream_id)
        if not state:
            raise HTTPException(status_code=404, detail="Stream not found")
    return {"stream_id": stream_id, "status": "closed"}


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

    safe_name = Path((file.filename or "upload").replace("\\", "/")).name
    meta = {"name": safe_name, "posts": len(posts), "accounts": len({p.account_id for p in posts})}
    meta["input_sha256"] = hashlib.sha256(upload_path.read_bytes()).hexdigest()
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
        review = get_review(run_dir / "workflow.sqlite", dataset_id, c["id"])
        assessment = {"threat_type": v.threat_type, "severity": v.severity,
                      "level": escalate(c["score"], v)["level"]} if v else None
        result.append({**campaign_summary(c), "assessment": assessment, "review": review})
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
    return {**campaign_summary(campaign), "accounts": campaign["accounts"],
            "sample_posts": load_samples(run_dir, cid),
            "review": get_review(run_dir / "workflow.sqlite", dataset_id, cid)}


@app.post("/api/datasets/{dataset_id}/campaigns/{cid}/review")
def review_campaign(dataset_id: str, cid: str, request: ReviewRequest):
    run_dir = run_dir_for(dataset_id)
    load_campaign(run_dir, cid)
    try:
        return record_review(run_dir / "workflow.sqlite", dataset_id, cid, request.reviewer_id,
                             request.reviewer_role, request.decision, request.reason)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/api/datasets/{dataset_id}/audit")
def get_audit_events(dataset_id: str, campaign_id: str | None = None):
    run_dir = run_dir_for(dataset_id)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    return list_audit_events(run_dir / "workflow.sqlite", dataset_id, campaign_id)


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
