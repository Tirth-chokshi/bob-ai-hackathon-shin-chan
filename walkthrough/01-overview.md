# 01 — System Overview

## What This System Does

This is an **AI-powered OSINT and Coordinated Inauthentic Behavior (CIB) detection engine** built for Law Enforcement Cyber Cells in India. It ingests raw social media posts, automatically detects synchronized bot/sock-puppet networks, scores their danger level, and generates legal escalation briefs compliant with Indian law.

**Problem it solves:** Individual posts in a coordinated campaign often appear harmless in isolation. The system detects *behavioral synchronization across many accounts* — posting the same content, sharing the same links, replying to the same targets — all within tight time windows. This is behavior that no human analyst can spot manually at scale.

---

## Two-Phase Architecture

```
Phase 1 — Deterministic (no AI needed)
 CSV Posts  →  Normalize  →  Build Multi-Signal Graph  →  Louvain Clustering  →  CIB Score

Phase 2 — AI-Powered (IBM Bob)
 Flagged Campaign  →  Build Prompt  →  bob run (headless)  →  Threat Verdict  →  Legal Escalation Brief
```

### Phase 1 — Behavioral Coordination Detection

Processes posts using the **QUT Digital Observatory `coordination_network_toolkit`** across **5 signal layers**:

| Signal | What it detects | Time window |
|---|---|---|
| `co_tweet` | Accounts posting **identical text** | 60 s |
| `co_similar_tweet` | Accounts sharing **paraphrased text** (Jaccard ≥ 0.8) | 60 s |
| `co_link` | Accounts sharing the **same URL** | 60 s |
| `co_reply` | Accounts replying to the **same victim** | 300 s |
| `co_retweet` | Accounts retweeting the **same source** | 60 s |

Each signal is computed separately and merged into a single **undirected weighted graph** using NetworkX. **Louvain community detection** is then run on the merged graph to find clusters (campaigns). Each cluster is scored 0–100 using 6 forensic features:

| Feature | Weight | What it measures |
|---|---|---|
| `speed` | 25 pts | Median gap between consecutive identical actions by different accounts |
| `duplication` | 25 pts | Share of posts with ≥ 0.8 Jaccard overlap with another account's post |
| `multi_signal` | 15 pts | Number of distinct coordination signals present |
| `fresh_accounts` | 15 pts | Share of accounts whose first post came < 30 days after account creation |
| `burst` | 10 pts | Campaign peak posts/minute ÷ (5 × dataset median posts/minute) |
| `concentration` | 10 pts | Share of posts using the single top hashtag or URL |

### Phase 2 — IBM Bob AI Threat Synthesis

For each flagged cluster, IBM Bob (`bob run --format json`) is called headlessly with a structured prompt containing:
- Campaign statistics and CIB score breakdown
- Up to 10 representative sample posts
- The verified Indian legal reference table
- Strict JSON output schema

Bob returns:
- **Threat type** (`incitement` / `targeted_harassment` / `organized_misinformation` / `benign_coordination`)
- **Target** entity (who is being attacked or mobilized against)
- **Narrative** summary
- **Severity** (1–5 scale)
- **Offline Call-to-Action** flag (physical gathering/mobilization detected)
- **Legal suggestions** filtered to verified Indian law sections (BNS 2023, IT Act, BNSS, BSA)

This verdict then feeds into a **deterministic escalation engine** (`URGENT` / `ALERT` / `MONITOR`) and is rendered into an **HTML brief** compliant with BSA Section 63 (tamper-evident with SHA-256 hashes).

---

## End-to-End Data Flow

```
User uploads CSV
      ↓
POST /api/datasets          → saves posts.json
      ↓
POST /api/datasets/:id/analyze
      ↓
  engine/normalize.py       → load & parse posts (auto-detect format)
  engine/coordination.py    → build multi-signal graph (SQLite, toolkit)
  engine/campaigns.py       → Louvain clustering → Campaign objects
  engine/scoring.py         → CIB score (0–100) + feature breakdown
  engine/pipeline.py        → save campaigns.json, graph.json, timeline.json
      ↓
React UI loads:
  GET /api/datasets/:id/graph    → NetworkGraph (Cytoscape.js)
  GET /api/datasets/:id/timeline → TimelineChart
  GET /api/datasets/:id/campaigns/:cid → CampaignPanel
      ↓
User clicks "Ask IBM Bob"
      ↓
POST /api/datasets/:id/campaigns/:cid/classify
      ↓
  bob/client.py             → build prompt → bob run → parse JSON verdict
  engine/escalation.py      → determine URGENT/ALERT/MONITOR
      ↓
User clicks "View Brief"
      ↓
GET /api/datasets/:id/brief
      ↓
  brief/render.py           → full HTML with SHA-256 evidence chain
```

---

## Directory Structure

```
src/
├── api/main.py           FastAPI REST API (all routes)
├── bob/
│   ├── client.py         IBM Bob headless runner, prompt builder, cache
│   └── legal.py          Legal table parser (markdown → structured dict)
├── brief/render.py       HTML escalation brief generator
├── config.py             Central config (paths, env vars)
├── engine/
│   ├── campaigns.py      Louvain clustering → Campaign objects
│   ├── coordination.py   Multi-signal graph builder (toolkit wrapper)
│   ├── escalation.py     Deterministic URGENT/ALERT/MONITOR rules
│   ├── normalize.py      CSV/JSON post loading (multi-format auto-detect)
│   ├── pipeline.py       End-to-end analysis orchestrator
│   ├── schema.py         Pydantic models (Post, Campaign, BobVerdict, etc.)
│   └── scoring.py        CIB risk score (0–100) with feature breakdown
├── mcp_server/server.py  FastMCP server for Bob Chat OSINT queries
├── samples/              Demo dataset, scenario CSV, ground-truth JSON
├── scenario/             Synthetic data generators & real-data adapters
│   └── adapters/
│       ├── io_archive.py  X/Twitter Information Operations Archive adapter
│       └── ira.py         FiveThirtyEight IRA Troll Tweet adapter
└── web/src/              React 19 frontend (Vite + Tailwind CSS v4)
    ├── App.jsx            Root component, all state, tab routing
    ├── api.js             Thin fetch wrapper for all backend calls
    └── components/
        ├── BriefView.jsx
        ├── CampaignList.jsx
        ├── CampaignPanel.jsx
        ├── Navbar.jsx
        ├── NetworkGraph.jsx   Cytoscape.js graph renderer
        ├── StatTiles.jsx
        ├── TimelineChart.jsx
        ├── UploadPanel.jsx
        └── VerdictCard.jsx
```
