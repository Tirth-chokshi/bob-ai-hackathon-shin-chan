# Execution Plan — Build Steps

Build the project by following these steps from top to bottom. Each step says **what to build** and **how to check it works**. The *what* and *why* are in [`project-plan.md`](project-plan.md).

The frontend (steps 14–17) can be built at the same time as the backend by using mock mode.

---

## Before You Start

- [ ] Python 3.10+, Node 24+, Git and Bob Shell 2.0+ installed (`python --version`, `node --version`, `bob --version`).
- [ ] Signed in to Bob (`bob`, log in with IBMid; `/status` shows coins).
- [ ] Bob **Inference** API key in `src/.env` (copy of `src/.env.example`) and tested — see [Commands](#commands).
- [ ] Datasets downloaded into `data/raw/` — see [Commands](#commands).

**Rules**
- Never commit `src/.env`, the root `data/` folder, `node_modules/` or `dist/`.
- Never put code in a folder named `data/`, `build/` or `dist/` (the template's `.gitignore` ignores them).
- Before every push: `git pull --rebase`, then the key check `git grep -E "bob_prod_[A-Za-z0-9_-]{30,}"` must print nothing.

---

## Part 1 — Setup

### Step 1 · Project skeleton

```bash
mkdir -p src/engine src/bob src/brief src/api src/mcp_server src/scenario/adapters src/samples src/eval src/tests
touch src/engine/__init__.py src/bob/__init__.py src/brief/__init__.py src/api/__init__.py \
      src/mcp_server/__init__.py src/scenario/__init__.py src/scenario/adapters/__init__.py src/eval/__init__.py
```

`src/config.py` — paths and settings in one place:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
load_dotenv(SRC / ".env")

DATA = ROOT / "data"                    # gitignored
RAW = DATA / "raw"                      # downloaded datasets
RUNS = DATA / "runs"                    # analysis output, one folder per dataset
SAMPLES = SRC / "samples"               # committed: scenario CSV, truth.json, demo_run/
BOB_RULES = ROOT / ".bob" / "rules-osint-analyst"
WEB_DIST = SRC / "web" / "dist"

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
TIME_WINDOW = int(os.getenv("TIME_WINDOW_SECONDS", "60"))
MIN_EDGE_WEIGHT = int(os.getenv("MIN_EDGE_WEIGHT", "2"))
BOB_API_KEY = os.getenv("BOB_API_KEY", "")
BOB_MAX_COST = os.getenv("BOB_MAX_COST", "0.25")
```

`src/main.py`:

```python
from pathlib import Path
import uvicorn
from config import APP_HOST, APP_PORT

if __name__ == "__main__":
    uvicorn.run("api.main:app", host=APP_HOST, port=APP_PORT, app_dir=str(Path(__file__).parent))
```

`src/api/main.py` — status route first, built frontend mounted last:

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from config import BOB_API_KEY, WEB_DIST

app = FastAPI(title="Social Media Threat Intelligence Engine")

@app.get("/api/status")
def status():
    return {"bob_configured": bool(BOB_API_KEY), "version": "0.1.0"}

# ... all other /api routes go ABOVE this line ...

if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
else:
    @app.get("/")
    def frontend_missing():
        return HTMLResponse("Frontend not built — run <code>npm ci && npm run build</code> in src/web.")
```

`src/tests/conftest.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
```

**Check:** `python src/main.py`, then `curl.exe -s http://127.0.0.1:8000/api/status` returns `{"bob_configured": true, ...}`.

### Step 2 · `.bob/` files

Create the six files from [Appendix B](#appendix-b--bob-files).

**Check:** in the repo root, `bob chat` → `/mode` lists `osint-analyst`.

### Step 3 · Scenario generator — `src/scenario/generate_scenario.py`

```python
def generate(seed: int = 42) -> tuple[list[dict], dict]:   # (posts, truth)
# Run as a script → writes src/samples/scenario_posts.csv and src/samples/truth.json
```

CSV columns: `post_id, account_id, username, created_at, text, repost_of, reply_to, urls, hashtags, account_created_at` (unix seconds; `urls` and `hashtags` space-separated).

| Part | Accounts | Account age | Behaviour | Expected result |
|---|---|---|---|---|
| Background | ~800 | 1–8 years | ~5 posts each at random times over 48 h: traffic, weather, food, festival, cricket chatter in fictional **Sundarpur**; some replies and reposts; links to fictional news sites | Noise |
| **A — Rumour ring** | 40 | 2–10 days | 6 bursts; in each burst every account posts a variant of 3 templates within 30 s; `#SundarpurAlert`; call to gather at the Collector office 7 PM | organized misinformation + real-world call to action |
| **B — Link ring** | 25 | 5–20 days | 5 rounds; all share `http://sundarpur-truth.example/<slug>` within 60 s with short varied text | organized misinformation |
| **C — Harassment pile-on** | 30 | 3–15 days | 3 waves of replies to posts by fictional journalist `@asha_reports` within 5 min, similar hostile-but-mild text | targeted harassment |
| **D — Decoy** | 60 | 1–6 years | one burst of varied celebratory posts with `#SundarpurStrikers` over ~10 min | benign — must score lowest |

Variants: swap words, punctuation, emoji and order, but stay above 0.8 word overlap for A. Keep all text **mild and fictional**.
`truth.json`: `{"A": [account ids], "B": [...], "C": [...], "D": [...], "labels": {"A": "organized_misinformation", "B": "organized_misinformation", "C": "targeted_harassment", "D": "benign_coordination"}}`

**Check:** both files are written, and running twice gives identical output.

---

## Part 2 — Engine

### Step 4 · Data models — `src/engine/schema.py`

`Post`, `Campaign` (with `size`, `top_hashtag`), `LegalSuggestion`, `BobVerdict` — exactly as in `project-plan.md` Section 11.

**Check:** `from engine.schema import Post, Campaign, BobVerdict` works.

### Step 5 · Load posts — `src/engine/normalize.py` + `src/scenario/adapters/`

- `load_posts(path) -> list[Post]` detects the format and calls the right loader.
- Scenario CSV loader.
- `io_archive.py`: `tweetid → post_id`, `userid → account_id`, `user_screen_name → username`, `tweet_time → created_at`, `tweet_text → text`, `retweet_tweetid → repost_of`, `in_reply_to_tweetid → reply_to`, `urls`, `hashtags`, `account_creation_date → account_created_at`.
- `ira.py`: `tweet_id → post_id`, `author → account_id/username`, `publish_date → created_at`, `content → text`, URLs from `tco1_step1…`.
- Loaders take an optional row limit.

**Check:** the scenario CSV and a 20k-row sample of each real dataset load without errors.

### Step 6 · Coordination graph — `src/engine/coordination.py`

```python
from coordination_network_toolkit import preprocess, graph, compute_networks as cn

NETWORKS = {"co_tweet": cn.compute_co_tweet_network, "co_similar_tweet": cn.compute_co_similar_tweet,
            "co_link": cn.compute_co_link_network, "co_reply": cn.compute_co_reply_network,
            "co_retweet": cn.compute_co_retweet_parallel}

def build_graph(posts, db_path, window, min_weight) -> nx.Graph:
    # 1. delete db_path, then preprocess.preprocess_data(db_path, rows)
    #    rows = (post_id, account_id, username, repost_of or "", reply_to or "", text, created_at, urls)
    # 2. each network: compute(db_path, time_window=window, min_edge_weight=min_weight)
    #    (co_similar_tweet also: similarity_threshold=0.8)
    # 3. graph.load_networkx_graph(db_path, name) → merge into one undirected graph:
    #    weight = sum of weights, "signals" = set of network names
```

**Check:** on the scenario, accounts of A, B and C are connected to each other.

### Step 7 · Campaigns — `src/engine/campaigns.py`

`find_campaigns(G, posts, min_size=5)`: `nx.community.louvain_communities(G, weight="weight", seed=42)`, keep groups of ≥ 5 accounts, fill `accounts`, `post_ids`, `size`, `top_hashtag`, `first_seen`, `last_seen`, `signals`. Number them `c1, c2, …` by score (after Step 8).

**Check:** the scenario gives one campaign per planted group.

### Step 8 · CIB score — `src/engine/scoring.py`

Weights: speed 0.25, duplication 0.25, multi-signal 0.15, fresh accounts 0.15, burst 0.10, concentration 0.10.

| Feature | Formula (each 0–1) |
|---|---|
| speed | group campaign posts by action (same text, URL, reply target or repost target); gaps between consecutive posts by different accounts; `1 − median_gap / window` |
| duplication | share of posts with ≥ 0.8 word overlap with a post by another campaign account |
| multi-signal | `(number of signals − 1) / 4` |
| fresh accounts | share of accounts whose first post is < 30 days after account creation |
| burst | campaign's peak posts/min ÷ (5 × dataset's median posts/min) |
| concentration | share of posts with the top hashtag or top URL |

Points per feature = `round(100 × weight × value)`; score = sum of points (these points drive the "why flagged" bars).

**Check:** A, B and C score higher than D.

### Step 9 · Pipeline + test — `src/engine/pipeline.py`, `src/tests/test_engine.py`

`analyze(dataset_id, posts)` writes to `data/runs/<dataset_id>/`: `posts.json`, `toolkit.db`, `campaigns.json`, `graph.json` (Cytoscape format, only accounts with edges), `timeline.json` (60-second buckets, `total` plus one key per campaign).

Test: generate the scenario → analyze → each of A, B, C has ≥ 80% of its accounts in one campaign, and D scores lowest.

**Check:** `python -m pytest src/tests` passes.

### Step 10 · API routes — `src/api/main.py`

`GET /api/datasets/demo`, `POST /api/datasets` (CSV upload), `POST /api/datasets/{id}/analyze`, `GET /api/datasets/{id}/graph`, `GET /api/datasets/{id}/timeline`, `GET /api/datasets/{id}/campaigns/{cid}` (plus 10 sample posts, oldest first). Shapes: [Appendix A](#appendix-a--api-contract). On startup, copy `src/samples/demo_run` → `data/runs/demo` if missing.

**Check:**

```bash
curl.exe -s -X POST http://127.0.0.1:8000/api/datasets/demo/analyze
curl.exe -s http://127.0.0.1:8000/api/datasets/demo/graph
```

> ✅ **Milestone 1:** the backend analyses the demo dataset and returns campaigns, graph and timeline.

---

## Part 3 — IBM Bob

### Step 11 · Legal table parser — `src/bob/legal.py`

`load_legal_table()` reads `.bob/rules-osint-analyst/01-legal-table.md` rows into `{id: {law, ipc, title, kind}}`; `allowed_offence_ids()` returns the IDs of kind `offence`.

**Check:** 9 offence IDs and 3 procedural IDs.

### Step 12 · Bob client — `src/bob/client.py`

```python
BOB = shutil.which("bob")

def run_bob(prompt, work_dir, max_cost=BOB_MAX_COST) -> tuple[str, float]:
    out = subprocess.run(
        [BOB, "run", "--accept-license", "--format", "json", "--max-turns", "2", "--max-cost", max_cost,
         "--disable-mcp", "--disable-subagents",
         "Classify the campaign described on stdin. Follow its instructions exactly."],
        input=prompt, cwd=work_dir, env={**os.environ, "BOB_API_KEY": BOB_API_KEY},
        capture_output=True, text=True, encoding="utf-8", timeout=120)
    data = json.loads(out.stdout)
    return data["last_message"], data["stats"]["session_costs"]
```

`classify(run_dir, campaign, sample_posts)`:
1. Return the cached verdict from `run_dir/bob/<campaign>.json` if it exists.
2. Build the prompt: the `.bob/rules-osint-analyst/*.md` files + output schema + allowed legal IDs + campaign stats + up to 10 posts + "Reply with ONLY one JSON object".
3. `run_bob` in an empty temp folder → extract the JSON → validate as `BobVerdict`; on failure retry once, then mark `verified=False`.
4. Keep only evidence IDs that belong to the campaign and legal IDs from the table.
5. Save the cache.

No key and no cache → a clear "Bob not configured" error.

**Check:** the 8-post Sundarpur test campaign returns `organized_misinformation` with a call to action and legal IDs only from the table; a second call is instant (cached).

### Step 13 · Escalation + classify route

- `src/engine/escalation.py`: `escalate(score, verdict) -> {level, actions}` using the rules in `project-plan.md` Section 8.
- Route `POST /api/datasets/{id}/campaigns/{cid}/classify`: run `classify` + `escalate`, add title and IPC to each legal ID, return the shape in Appendix A; HTTP 503 when Bob is not configured and nothing is cached.

**Check:** one quick test per escalation level passes; classifying a demo campaign through the API returns a verdict.

---

## Part 4 — React Frontend

### Step 14 · Scaffold + mock mode

```bash
cd src
npm create vite@latest web -- --template react
cd web
npm install
npm install cytoscape react-cytoscapejs recharts
npm install -D tailwindcss @tailwindcss/vite
```

`vite.config.js`:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
})
```

- `src/index.css` → `@import "tailwindcss";`
- `src/web/.env.local` → `VITE_USE_MOCK=true` while the backend is not ready.
- Save the JSON examples from Appendix A as `src/web/src/mock/<name>.json`, and a sample brief as `src/web/public/mock-brief.html`.
- `src/api.js`: one function per endpoint; in mock mode return the mock files:

```js
const MOCK = import.meta.env.VITE_USE_MOCK === 'true'
const mocks = import.meta.glob('./mock/*.json', { eager: true, import: 'default' })
const mock = (name) => Promise.resolve(structuredClone(mocks[`./mock/${name}.json`]))

async function req(method, path, body) {
  const r = await fetch(`/api${path}`, { method, body })
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
  return r.json()
}

export const api = {
  status:   ()        => MOCK ? mock('status')   : req('GET',  '/status'),
  datasets: ()        => MOCK ? mock('datasets') : req('GET',  '/datasets/demo'),
  upload:   (file)    => { const f = new FormData(); f.append('file', file); return req('POST', '/datasets', f) },
  analyze:  (id)      => MOCK ? mock('analyze')  : req('POST', `/datasets/${id}/analyze`),
  graph:    (id)      => MOCK ? mock('graph')    : req('GET',  `/datasets/${id}/graph`),
  timeline: (id)      => MOCK ? mock('timeline') : req('GET',  `/datasets/${id}/timeline`),
  campaign: (id, cid) => MOCK ? mock('campaign') : req('GET',  `/datasets/${id}/campaigns/${cid}`),
  classify: (id, cid) => MOCK ? mock('verdict')  : req('POST', `/datasets/${id}/campaigns/${cid}/classify`),
  briefUrl: (id)      => MOCK ? '/mock-brief.html' : `/api/datasets/${id}/brief`,
}
```

**Check:** `npm run dev` opens http://localhost:5173.

### Step 15 · App shell, Upload and Overview

- `App.jsx`: tabs Upload / Overview / Network / Brief; state `datasetId`, `campaigns`, `selectedCampaignId`, `verdicts`.
- `UploadPanel`: demo dataset list, CSV upload, **Analyze** button with a loading state.
- `StatTiles`: posts, accounts, campaigns found, highest score.
- `TimelineChart`: Recharts `AreaChart` over `points` — grey `total`, one coloured area per campaign.
- `CampaignList`: rows sorted by score (size, top hashtag, score badge, signal chips); clicking selects and opens Network.

**Check:** with mock data, Analyze → Overview shows tiles, chart and list.

### Step 16 · Network graph and campaign panel

```jsx
import CytoscapeComponent from 'react-cytoscapejs'

<CytoscapeComponent
  elements={CytoscapeComponent.normalizeElements(graph)}
  layout={{ name: 'cose', animate: false }}
  stylesheet={styles}                 // colour from data(campaign), size from data(degree)
  style={{ width: '100%', height: '70vh' }}
  cy={(cy) => { cy.on('tap', 'node', (e) => onSelect(e.target.data('campaign'))) }}
/>
```

- One colour per campaign; accounts without a campaign small and grey; the selected campaign highlighted.
- `CampaignPanel`: stats, `WhyFlagged` (one bar per feature, width = points), 10 sample posts.

**Check:** clicking a node opens its campaign in the side panel.

### Step 17 · Ask Bob and status banner

- `VerdictCard`: **Ask Bob** button → spinner "Bob is analysing (~10 s)…" → threat type, severity, target, narrative, call to action, legal suggestions (ID, title, IPC, reason, "verify with a legal officer"), evidence post IDs, escalation badge (URGENT red / ALERT amber / MONITOR grey) with actions, "cached" tag.
- `BobStatusBanner`: shown when `bob_configured` is false — "IBM Bob is not configured — showing cached analysis only."

**Check:** set `VITE_USE_MOCK=false`, run the backend: Upload → Analyze → Network → Ask Bob works with real data.

> ✅ **Milestone 2:** the full journey works in the browser against the real backend.

---

## Part 5 — Brief and Bob Chat

### Step 18 · Threat brief

- `src/brief/render.py` → `render_brief(dataset_id)` returns a full HTML page:
  - header: title, generated time (IST, `zoneinfo.ZoneInfo("Asia/Kolkata")`), dataset ID, SHA-256 of `posts.json`
  - **executive summary written by Bob** (one `run_bob` call following the `threat-brief` skill; cached in `bob/summary.json`)
  - per campaign with score ≥ 50: escalation level, score breakdown, verdict, legal suggestions "for verification", evidence table (post ID, time, account, text, SHA-256), actions
  - limitations; `html.escape()` all text; print CSS and a Print button
- Route `GET /api/datasets/{id}/brief`.
- `BriefView`: iframe preview + **Open printable brief** (new tab).

**Check:** the brief opens, and Print → Save as PDF looks clean.

### Step 19 · MCP server for Bob chat — `src/mcp_server/server.py`

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("threat-intel")

@mcp.tool()
def list_campaigns(dataset_id: str) -> list[dict]:
    """Campaigns in an analysed dataset, highest CIB score first."""

# also: list_datasets, get_campaign, get_posts, timeline, account_profile — read-only, from data/runs/

if __name__ == "__main__":
    mcp.run()
```

**Check:** with the venv active, in the repo root: `bob chat` → `/mode osint-analyst` → `/mcp` lists `threat-intel`; "List the campaigns in dataset demo" returns real campaigns.

---

## Part 6 — Proof and Submission

### Step 20 · Real datasets

Run the pipeline on 20k-row samples of the IO archive and IRA data. Note: number of campaigns, largest sizes, top hashtags, runtime; for IRA, compare campaigns with `account_category`.

### Step 21 · Evaluation — `src/eval/measure.py`

Prints: campaign detection precision/recall against `truth.json`, the decoy's rank, runtime, and Bob's agreement with human labels on 100 CONSTRAINT posts (two `run_bob` calls of 50 posts; mapping in `project-plan.md` Section 14). Save to `src/eval/results.md`.

### Step 22 · Bundle the demo and build

1. Analyze the scenario, classify every campaign scoring ≥ 50, generate the brief.
2. Copy `data/runs/demo` → `src/samples/demo_run/` (skip `toolkit.db` if large).
3. `cd src/web && npm run build`.
4. Run only `python src/main.py` — the whole app works on http://127.0.0.1:8000.

**Check:** a fresh clone **without** an API key shows the demo with cached Bob verdicts.

### Step 23 · Clean-machine test

Clone the repo into a new folder and follow `docs/setup-guide.md` word by word. Fix anything that doesn't work in the guide itself.

### Step 24 · Docs, screenshots, video, slides

- README: only features that work, numbers from `results.md`, credits (QUT toolkit, datasets), honest limitations; `src/README.md` with the real folder layout.
- Screenshots in `demo/screenshots/`: `01-upload.png`, `02-overview.png`, `03-network.png`, `04-bob-verdict.png`, `05-brief.png`, `06-bob-chat-mcp.png`.
- 3–5 min video following `project-plan.md` Section 20; upload as unlisted YouTube / Loom / Drive ("anyone with the link"); URL on the first line of `demo/demo-video-link.txt`.
- Slides → `presentation/slides.pdf`.

### Step 25 · Final checks and submit

- [ ] `submission.yaml`: all members; features match the README
- [ ] Key check prints nothing; `git status` clean; pushed
- [ ] `gh run list --limit 1` → **Validate Submission** green; repo public
- [ ] Submit the repo URL at **ibm.biz/bob-ai-nfsu** (open 12:00–19:00 on submission day)

**If short on time, cut in this order:** UI polish → real datasets → MCP console → Bob brief summary. Never cut: engine, graph, Ask Bob, video, submission.

---

## Appendix A — API Contract

Save these as the mock files (`src/web/src/mock/<name>.json`). The backend must return the same shapes. Errors: `{"detail": "message"}` with 404, 422 or 503.

**`status.json`** — `GET /api/status`

```json
{ "bob_configured": true, "version": "0.1.0" }
```

**`datasets.json`** — `GET /api/datasets/demo`

```json
[ { "id": "demo", "name": "Sundarpur scenario (synthetic)", "posts": 5230, "accounts": 955, "analyzed": true } ]
```

`POST /api/datasets` (form field `file`) → `{ "dataset_id": "u_3f9a1c", "posts": 1200, "accounts": 340 }`

**`analyze.json`** — `POST /api/datasets/{id}/analyze`

```json
{
  "dataset_id": "demo", "posts": 5230, "accounts": 955, "runtime_ms": 4200,
  "campaigns": [
    {
      "id": "c1", "size": 40, "top_hashtag": "#SundarpurAlert",
      "accounts": ["a_1001", "a_1002"], "post_ids": ["p5001", "p5002"],
      "score": 87,
      "features": { "speed": 22, "duplication": 24, "multi_signal": 11, "fresh_accounts": 15, "burst": 9, "concentration": 6 },
      "signals": ["co_tweet", "co_similar_tweet", "co_link"],
      "first_seen": 1790142124, "last_seen": 1790152924
    }
  ]
}
```

**`graph.json`** — `GET /api/datasets/{id}/graph`

```json
{
  "nodes": [ { "data": { "id": "a_1001", "label": "@rahul_s77", "campaign": "c1", "degree": 12 } },
             { "data": { "id": "a_0042", "label": "@meena_k", "campaign": null, "degree": 1 } } ],
  "edges": [ { "data": { "id": "a_1001__a_1002", "source": "a_1001", "target": "a_1002", "weight": 5, "signals": ["co_tweet"] } } ]
}
```

**`timeline.json`** — `GET /api/datasets/{id}/timeline`

```json
{
  "bucket_seconds": 60,
  "campaign_ids": ["c1", "c2"],
  "points": [ { "t": 1790142120, "total": 14, "c1": 0, "c2": 0 },
              { "t": 1790142180, "total": 55, "c1": 40, "c2": 0 } ]
}
```

**`campaign.json`** — `GET /api/datasets/{id}/campaigns/{cid}`

```json
{
  "id": "c1", "size": 40, "score": 87, "top_hashtag": "#SundarpurAlert",
  "features": { "speed": 22, "duplication": 24, "multi_signal": 11, "fresh_accounts": 15, "burst": 9, "concentration": 6 },
  "signals": ["co_tweet", "co_similar_tweet", "co_link"],
  "first_seen": 1790142124, "last_seen": 1790152924, "median_account_age_days": 6,
  "sample_posts": [
    { "post_id": "p5001", "account_id": "a_1001", "username": "@rahul_s77", "created_at": 1790142124,
      "text": "Sundarpur dam gates will be opened TONIGHT, whole east side will flood. Officials hiding it! #SundarpurAlert" }
  ]
}
```

**`verdict.json`** — `POST /api/datasets/{id}/campaigns/{cid}/classify`

```json
{
  "verdict": {
    "threat_type": "organized_misinformation",
    "target": "Residents of east Sundarpur and the district administration",
    "narrative": "38 new accounts spread a false dam-flooding claim within 9 minutes and urged people to gather at the Collector office at 7 PM.",
    "severity": 5,
    "offline_call_to_action": true,
    "legal_suggestions": [
      { "id": "BNS-353", "title": "Statements conducing to public mischief", "law": "BNS 353", "ipc": "IPC 505",
        "why": "False claim of imminent flooding likely to cause fear and alarm" },
      { "id": "BNS-61", "title": "Criminal conspiracy", "law": "BNS 61", "ipc": "IPC 120A/120B",
        "why": "Coordinated posting by a network of new accounts" }
    ],
    "evidence_post_ids": ["p5001", "p5002", "p5017"],
    "verified": true
  },
  "escalation": {
    "level": "URGENT",
    "actions": ["Notify SHO and district control room", "Preserve evidence (hashes in brief)",
                "Request platform takedown through the law-enforcement channel (see ITA-69A)",
                "Consider preventive orders (BNSS-163)", "Issue a public fact-check advisory"]
  },
  "cached": false,
  "cost": 0.025
}
```

`GET /api/datasets/{id}/brief` → a complete HTML page (`text/html`).

---

## Appendix B — `.bob/` Files

### `.bob/custom_modes.yaml`

```yaml
customModes:
  - slug: osint-analyst
    name: 🛡️ OSINT Analyst
    roleDefinition: >-
      You are a police cyber cell OSINT analyst assessing coordinated social media campaigns in India.
      You investigate using the threat-intel MCP tools and give decision support, never verdicts.
    whenToUse: Use when investigating analysed datasets, campaigns, accounts and posts, or drafting threat briefs.
    customInstructions: |-
      - Always fetch evidence with the threat-intel tools before answering; cite post IDs for every claim.
      - Suggest legal sections only from the legal table in the rules, by ID, and say they need verification by a legal officer.
      - Never infer or label anyone by religion, caste, community, or other protected attribute.
      - If the evidence is weak, say so.
    groups:
      - read
      - mcp
```

### `.bob/rules-osint-analyst/01-legal-table.md`

```markdown
# Legal reference table (suggestions for verification by a legal officer)

Only suggest sections of kind `offence`, by ID. `procedural` rows are for escalation actions only.
Never cite IT Act 66A (struck down in Shreya Singhal v. Union of India, 2015).

| ID | Law | Old law | Covers | Kind |
|---|---|---|---|---|
| BNS-196 | BNS 196 | IPC 153A | Promoting enmity between groups | offence |
| BNS-197 | BNS 197 | IPC 153B | Imputations or assertions prejudicial to national integration | offence |
| BNS-351 | BNS 351 | IPC 506 | Criminal intimidation (threats) | offence |
| BNS-353 | BNS 353 | IPC 505 | Statements conducing to public mischief (rumours causing fear or alarm) | offence |
| BNS-356 | BNS 356 | IPC 499/500 | Defamation | offence |
| BNS-79 | BNS 79 | IPC 509 | Word, gesture or act intended to insult the modesty of a woman | offence |
| BNS-61 | BNS 61 | IPC 120A/120B | Criminal conspiracy (coordinated action) | offence |
| ITA-66D | IT Act 66D | — | Cheating by personation using a computer resource (impersonation accounts only) | offence |
| ITA-67 | IT Act 67 | — | Publishing obscene material in electronic form | offence |
| ITA-69A | IT Act 69A | — | Blocking of public access to information (Central Government power; request through proper channel) | procedural |
| BNSS-163 | BNSS 163 | CrPC 144 | Preventive orders in urgent cases | procedural |
| BSA-63 | BSA 63 | Evidence Act 65B | Certificate for electronic records (supported by SHA-256 hashes) | procedural |
```

### `.bob/rules-osint-analyst/02-escalation.md`

```markdown
# Escalation rules (applied by code; explain them, do not change them)

- URGENT: threat_type is incitement AND there is a real-world call to action (time/place to gather),
  OR CIB score >= 80 with severity >= 4.
- ALERT: organized_misinformation or targeted_harassment with CIB score >= 60.
- MONITOR: everything else, including benign_coordination.
```

### `.bob/rules-osint-analyst/03-no-profiling.md`

```markdown
# No profiling

- Judge behaviour and content only.
- Never infer, guess or label a person's religion, caste, community, ethnicity, political affiliation or other protected attribute.
- Describe targets as the posts describe them; do not generalise to a whole group.
- Treat all outputs as leads for a trained officer, not findings of guilt.
```

### `.bob/skills/threat-brief/SKILL.md`

```markdown
---
name: threat-brief
description: Draft a police threat escalation brief or executive summary for an SHO / district cyber cell from analysed campaigns. Use when asked for a brief, summary, or SHO briefing.
---

Write for a busy Station House Officer. Plain English, no jargon.

1. One-line bottom line: the most urgent campaign and the recommended level (URGENT / ALERT / MONITOR).
2. For each campaign (highest score first): what is being spread, by how many accounts, how fast, and why it looks coordinated (cite the top score features).
3. Real-world risk: any call to gather, time and place.
4. Recommended actions from the escalation rules.
5. Legal sections only from the legal table, marked "for verification by a legal officer".
6. Cite post IDs for every factual claim. Do not add facts that are not in the data.
7. End with limitations: automated analysis, decision support only.
```

### `.bob/mcp.json`

```json
{
  "mcpServers": {
    "threat-intel": {
      "command": "python",
      "args": ["src/mcp_server/server.py"],
      "alwaysAllow": ["list_datasets", "list_campaigns", "get_campaign", "get_posts", "timeline", "account_profile"]
    }
  }
}
```

Start `bob chat` from the repo root with the venv activated, so `python` is the project's Python.

---

## Appendix C — Using Bob to Build

Prompt for any step (Agent mode):

```
Implement Step <N> from @docs/execution-plan.md in <file>.
Follow the signatures, formulas and "Check" exactly. Use the models in @src/engine/schema.py.
Do not modify other files. When done, run the check and show me the output.
```

For bigger steps (6, 8, 12, 16, 18) start in Plan mode: `/mode plan`, ask for a short plan, approve, then switch to Agent mode.

Tips: one fresh chat per step, `/compact` when a chat gets long, `/status` to watch coins, review every diff.

---

## Commands

```bash
# Run the app (built frontend)
python src/main.py                                   # http://127.0.0.1:8000

# Frontend dev server (second terminal)
cd src/web && npm run dev                            # http://localhost:5173

# Build frontend
cd src/web && npm ci && npm run build

# Tests, evaluation, scenario
python -m pytest src/tests
python src/eval/measure.py
python src/scenario/generate_scenario.py

# Bob key test (Git Bash; key read from src/.env, prompt via stdin)
export $(grep -E '^BOB_API_KEY=' src/.env | xargs)
echo "Reply with exactly: ok" | bob run --accept-license --format json --max-turns 1 --max-cost 0.05 --disable-mcp --disable-subagents "Follow the instructions on stdin."

# Datasets (into the gitignored data/raw/)
mkdir -p data/raw
curl -L -o data/raw/constraint_train.csv https://raw.githubusercontent.com/mohit19014/Hindi-Hostility-Detection-CONSTRAINT-2021/master/Dataset/train.csv
curl -L -o data/raw/ira_1.csv https://raw.githubusercontent.com/fivethirtyeight/russian-troll-tweets/master/IRAhandle_tweets_1.csv
curl -L -r 0-300000000 -o data/raw/io_sample.csv https://archive.org/download/X_Twitter_Information_Operations/ioa_tweets.csv

# Before every push
git pull --rebase
git grep -E "bob_prod_[A-Za-z0-9_-]{30,}"            # must print nothing
git status
git push

# Validator
gh run list --limit 3
gh run view --log-failed
```
