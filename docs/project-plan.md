# Project Plan & Engineering Specification — Social Media Threat Intelligence Engine

**Engineering Authors:** Tirth Chokshi (lead), Milind Pawar, Jainik Devada, Jigar Jariwala  
**Domain:** Cyber Forensics, OSINT & Coordinated Inauthentic Behavior (CIB) Detection  

> This document details the architectural design and implementation plan: the core problem space, pipeline mechanics, algorithms, IBM Bob integration layers, and evaluation methodology. Step-by-step build instructions are in [`execution-plan.md`](execution-plan.md).

---

## Table of Contents

1. [TL;DR](#1-tldr)
2. [Project Context and Objectives](#2-project-context-and-objectives)
3. [The Problem](#3-the-problem)
4. [Why CIB Forensics Matters](#4-why-cib-forensics-matters)
5. [The Key Insight: Behaviour First, Content Second](#5-the-key-insight-behaviour-first-content-second)
6. [Solution Overview](#6-solution-overview)
7. [System Architecture](#7-system-architecture) — incl. **What We Use and Where**
8. [The CIB Engine in Detail](#8-the-cib-engine-in-detail)
9. [IBM Bob Integration](#9-ibm-bob-integration)
10. [Tech Stack and Why](#10-tech-stack-and-why)
11. [Data Model and API Contract](#11-data-model-and-api-contract)
12. [Frontend](#12-frontend)
13. [Data Strategy](#13-data-strategy)
14. [Evaluation Plan](#14-evaluation-plan)
15. [Legal Reference Table](#15-legal-reference-table)
16: [Ethics, Safety and Limitations](#16-ethics-safety-and-limitations)
17. [Repository Layout](#17-repository-layout)
18. [Build Plan](#18-build-plan)
19. [Risks and Mitigations](#19-risks-and-mitigations)
20. [Demo Script](#20-demo-script)
21. [System Verification](#21-system-verification)
22. [References](#22-references)

---

## 1. TL;DR

- **What:** A tool for police cyber cells that takes a batch of social media posts, finds **groups of accounts acting together** (coordinated inauthentic behaviour, CIB), scores how suspicious each group is, has **IBM Bob** classify the threat and suggest BNS / IT Act sections, and produces a **time-stamped threat brief** with escalation steps.
- **Why it matters:** Most systems classify posts one at a time. Real-world agitational events are *coordinated campaigns*. We detect coordination first (behaviour), then read the content — catching campaigns even when each post looks harmless.
- **Built on:** the QUT Digital Observatory **coordination-network-toolkit** (published research methods, verified running on our laptop), **NetworkX**, **FastAPI**, **SQLite**, a **React** frontend (Vite, Tailwind, Cytoscape.js, SVG timeline), and **IBM Bob**. Step-by-step build instructions: [`execution-plan.md`](execution-plan.md).
- **Where Bob runs:** (1) the backend calls `bob run` with our **Bob API key** to classify each campaign and (2) write the brief's executive summary; (3) officers investigate in **Bob chat** through our **MCP server**; (4) the repo's `.bob/` folder holds the mode, rules (incl. the legal table) and skill; (5) Bob is our coding partner. Tested: ~0.025 coins and ~11 s per classification.
- **Data:** synthetic scenarios with planted campaigns (ground truth for measuring accuracy) plus real research datasets (X Information Operations archive, IRA troll tweets, CONSTRAINT-2021 Hindi hostility).

---

## 2. Project Context and Objectives

| Item | Specification |
|---|---|
| Target Users | State Police Cyber Cells, District Cyber Crime Stations, Law Enforcement Intelligence Branches |
| Core Deliverable | Production web application + FastMCP tool server + court-admissible Section 63 BSA brief generator |
| AI Integration | IBM Bob: `bob run` with an API key (runtime), Bob chat + FastMCP (investigation), `.bob/` rules/skills |
| Design Principles | High-contrast Case File design system, zero demographic profiling, deterministic coordination thresholds |
| Verification | Automated pytest test suite (31 tests) and end-to-end bundle validation |

### Judging rubric (100 points) and how we target it

| Criterion | Pts | How we score it |
|---|---|---|
| Technical Implementation Quality | 25 | Real engine built on published methods; clean modules; one runnable test; evidence verification in code |
| Innovation & Differentiation | 25 | Behaviour-first CIB detection + Bob semantics + "benign coordination" class — not a per-post toxicity classifier |
| Problem Depth & Vision | 15 | We understand that the problem is *coordination*, not bad words; law-enforcement workflow (escalation, evidence integrity, legal packaging) |
| Working Demo & Functionality | 15 | Runs locally with one command; planted campaigns visibly light up; brief prints |
| IBM Bob Integration | 10 | Bob is load-bearing: campaign classifier, brief summary, MCP investigation console, custom mode/rules/skill in `.bob/` |
| Documentation & Reproducibility | 10 | Setup guide tested on a clean machine; honest limitations; measured numbers |

---

## 3. The Problem

### Official statement (#06)

> Build a Bob-powered OSINT tool that ingests a batch of mock social media posts, detects coordinated inauthentic behavior signals, classifies threat type (incitement / targeted harassment / organized misinformation), maps to IPC/BNS provisions, and generates a time-stamped threat brief with recommended escalation steps for law enforcement.

**Real case cited:** the 2022 Nupur Sharma controversy and the 2020 Delhi riots — coordinated hashtag campaigns preceded communal violence in multiple cities, and police had no real-time tool to detect coordinated inauthentic behaviour or emerging offline threats.

### What the problem really is

1. **Volume:** during a crisis, far more posts appear than officers can read.
2. **Organic vs engineered:** keyword alerts fire on genuine public outrage and on bot campaigns alike; officers cannot tell them apart.
3. **No coordination signals:** cyber cells have no tooling to see that 40 new accounts posted the same text within 30 seconds.
4. **Legal packaging gap:** turning posts into a time-stamped, section-mapped brief that a Station House Officer (SHO) or prosecutor can act on takes hours of manual work.

### Who is affected

- State and district **cyber cells** (inspectors, analysts doing cyber patrolling).
- **SHOs, SPs/DCPs** deciding on deployments, preventive orders (Section 163 BNSS) and public advisories.
- **Prosecutors / legal officers** drafting takedown and blocking requests and FIRs.
- **Citizens and communities** put at risk when online campaigns turn into offline violence.

---

## 4. Why We Chose Problem #06

We reviewed all 12 problem statements for: availability of a solid existing base, demo strength, technical depth, likely competition, and one-day feasibility.

| # | Problem | Best existing base found | Verdict |
|---|---|---|---|
| 01 | Document forgery | Small ELA/CNN demo apps | Weak base; mostly an LLM report |
| 02 | Disaster victim ID | *Identify-Lost-InFlood* (AM↔PM ranking) | Runner-up; table-style demo |
| 03 | Evidence triage | Nothing solid | Easy → crowded and shallow |
| 04 | Deepfake | DeepfakeBench, many detectors | Crowded; heavy models; unreliable on real clips |
| 05 | Fraud network | Only per-transaction UPI classifiers | Build from scratch |
| **06** | **Social media threat** | **QUT coordination-network-toolkit (verified)** | **Chosen** |
| 07 | Missing person | Face-matching Streamlit app (641★) | Runner-up; well-known repo, weak matching |
| 08 | Trafficking | Scrapers, UN data standard | Mostly questionnaire + LLM |
| 09 | Child safety | Tiny classifiers | Sensitive content; avoid |
| 10 | FIR patterns | Large platform tied to Zoho | Hard to adapt in a day |
| 11 | Drug hotspots | Nothing | Build from scratch |
| 12 | Crime hotspots | Small map demos | Crowded |

**Why #06:**
- **A real engine exists and runs** — the QUT toolkit implements coordination-detection methods from peer-reviewed research; we installed it and ran it end-to-end on Windows. It is a *library*, so our work (the pipeline, scoring, Bob layer, UI) stays clearly ours.
- **Non-obvious angle** most teams will miss (Section 5).
- **Visual demo:** a bot ring lights up as a cluster on a graph; a timeline shows the burst.
- **Moderate competition** compared with deepfake, fraud and hotspot problems.

### Options we considered and rejected

| Option | Why not |
|---|---|
| Fork a full OSINT platform (e.g. ShadowHorn) | Solves a different problem (profiling one person, IOC lookups); we would delete most of it; judges would credit its authors |
| Streamlit UI | Team decision: we build our own frontend |
| watsonx.ai Granite as classifier | No access; IBM Bob does the job and makes Bob load-bearing |
| Neo4j / MongoDB | Extra services to install; SQLite + JSON is optimal for zero-dependency embedded forensic deployment |
| Training a GNN / ML model | No labelled Indian CIB data; not feasible in a day; explainable heuristics are better for officers |

---

## 5. The Key Insight: Behaviour First, Content Second

**Coordinated inauthentic behaviour** means many accounts acting together to fake the appearance of organic activity. The defining evidence is *how accounts behave together*, not the words in any single post.

Example: *"Everyone meet at the square at 6 PM"* — harmless alone. Posted by 50 accounts created last week, within 90 seconds, with the same hashtag — it is a mobilization signal.

So our pipeline:
1. **Behaviour:** find accounts that repeatedly do the same thing within seconds of each other.
2. **Group:** turn those links into campaigns.
3. **Score:** explain *why* each campaign is suspicious.
4. **Content:** only then have Bob read the campaign's posts and judge the threat — including saying *"this is benign coordination"* (fan clubs, news sharing, organic protest organizing).

This is both more accurate and cheaper: Bob reads a handful of campaigns, not thousands of posts.

---

## 6. Solution Overview

### What the officer does

1. Uploads a batch of posts (CSV/JSON) or picks a demo dataset.
2. Clicks **Analyze** → sees counts, a posts-per-minute timeline, and a ranked list of campaigns.
3. Opens the **network graph** → accounts coloured by campaign; clicks a campaign → "why flagged" bars and sample posts.
4. Clicks **Ask Bob** → threat type, target, severity, suggested legal sections, evidence post IDs, escalation level.
5. Clicks **Generate Brief** → a time-stamped, print-ready Police Threat Escalation Brief (Print → PDF).
6. Optionally investigates further in **Bob chat**: *"Which accounts started campaign 2?"* — Bob uses our MCP tools to fetch the evidence.

### What the system outputs

- Ranked campaigns with an explainable **CIB score (0–100)**.
- Per-campaign **Bob verdict** (JSON) with verified evidence IDs.
- **Escalation level:** MONITOR / ALERT / URGENT.
- **Threat brief** with SHA-256 hashes of the input batch and each evidence post.

---

## 7. System Architecture

```
       Browser: React app (Vite + Tailwind + Cytoscape.js + SVG timeline)
       dev: Vite server :5173 proxies /api → :8000 · demo: built into src/web/dist
                         │  fetch /api/...
                         ▼
   ┌──────────────────── FastAPI app (one Python process) ─────────────────────┐
   │  api/main.py ── engine/ (normalize → coordination → campaigns → score)    │
   │        │                          │                                       │
   │        │                          └─► toolkit SQLite db (per dataset)     │
   │        ├─► bob/client.py ── subprocess, prompt via stdin ──► `bob run`    │
   │        │        (BOB_API_KEY from src/.env; rules read from .bob/)       │
   │        └─► brief/render.py ──► HTML brief (browser prints it to PDF)      │
   │   results saved as JSON in  data/runs/<dataset_id>/                       │
   └───────────────────────────────────────────────────────────────────────────┘

   Bob chat (terminal, IBMid sign-in) ──MCP──► mcp_server/server.py ──► reads the same data/runs/ JSON
```

- **Two processes of our own:** the FastAPI app and the MCP server (started by Bob chat when needed).
- **Bob** is an external CLI we call; no API SDK or HTTP client needed.
- **No database server, no Docker** — fewer things to break on the day. The React app is built once (`npm run build`) and served by FastAPI, so the demo still runs as a single process.
- **Folders:** runtime output and downloaded datasets live in the repo-root `data/` folder, which the template's `.gitignore` ignores. Code that must be committed therefore never lives in a folder named `data/` — the generator is in `src/scenario/`, bundled samples and the pre-analysed demo run in `src/samples/`.

### 7.1 What we use and where

| Part | What we use | Where (file) | Notes |
|---|---|---|---|
| Load posts | Pydantic adapters | `src/engine/normalize.py`, `src/scenario/adapters/` | One `Post` schema for every dataset |
| Coordination detection | `coordination_network_toolkit` + SQLite | `src/engine/coordination.py` | Co-tweet, co-similarity, co-link, co-reply, co-retweet |
| Campaigns | NetworkX Louvain | `src/engine/campaigns.py` | Groups of ≥ 5 accounts |
| CIB score | Plain Python | `src/engine/scoring.py` | Six features, stored contributions |
| Threat analysis | **IBM Bob** `bob run` (API key) | `src/bob/client.py` | One call per campaign, cached |
| Legal suggestions | Fixed table (Markdown) | `.bob/rules-osint-analyst/01-legal-table.md` | Single source: Bob chooses IDs, code validates |
| Escalation | Rule table | `src/engine/escalation.py` | Deterministic MONITOR / ALERT / URGENT |
| Brief | HTML template + **IBM Bob** summary | `src/brief/render.py` | Bob writes the executive summary only |
| REST API + static files | FastAPI + Uvicorn | `src/api/main.py` | Serves the built React app from `src/web/dist/` |
| Frontend | React 19 + Vite, Tailwind CSS, Cytoscape.js, SVG timeline | `src/web/` | Built to `src/web/dist/`, served by FastAPI |
| Investigation console | **IBM Bob chat** + Python `mcp` SDK | `src/mcp_server/server.py`, `.bob/mcp.json` | Read-only tools |
| Bob behaviour | Custom mode, rules, skill | `.bob/` | Used by Bob chat; rules also embedded in `bob run` prompts |
| Demo data | Our generator | `src/scenario/generate_scenario.py` | `posts.csv` + `truth.json`; bundled copy + pre-analysed run in `src/samples/` |
| Proof | pytest + eval script | `src/tests/`, `src/eval/measure.py` | Numbers for the README |

### 7.2 Where IBM Bob is used

| # | Bob touchpoint | How it runs | Credential | When |
|---|---|---|---|---|
| 1 | **Campaign threat analysis** | Backend → `bob run --format json`, prompt via stdin | `BOB_API_KEY` in `src/.env` | "Ask Bob" button / analyze step |
| 2 | **Brief executive summary** | Backend → `bob run` once per brief | `BOB_API_KEY` | "Generate Brief" |
| 3 | **Investigation console** | Officer runs `bob chat` in the repo; Bob calls our MCP tools | IBMid sign-in | Deep-dive questions, demo |
| 4 | **Repo configuration** | `.bob/` mode, rules, skill, `mcp.json` | — | Loaded by Bob chat; rules reused in prompts |
| 5 | **Coding partner** | Bob Shell / IDE, Plan → Agent mode | IBMid sign-in | Building the project |

### 7.3 Keys and credentials

| Credential | Needed for | Stored where | Rule |
|---|---|---|---|
| Bob API key (**Inference** type recommended) | `bob run` (touchpoints 1–2) | `src/.env` (gitignored) | One key per member; never in chat, Discord or commits |
| IBMid sign-in | `bob chat`, coding with Bob | Bob Shell's own login | — |
| Anything else | — | — | **None:** no watsonx, no social media APIs, no cloud accounts |

Without a key the app still runs: detection, graph and scoring work, and Bob verdicts are served from the cache (`data/runs/<id>/bob/`).

---

## 8. The CIB Engine in Detail

### Stage 0 — Normalize (`engine/normalize.py`)

Every dataset is converted by a small adapter into one schema (`Post`, see Section 11). Everything downstream only sees this schema.

Adapters: `scenario_csv` (our generator), `io_archive` (X Information Operations CSV), `ira_csv` (FiveThirtyEight IRA tweets).

### Stage 1 — Coordination networks (`engine/coordination.py`)

Uses the QUT toolkit. For every pair of accounts it counts how often they performed the same action within a time window.

| Network | Meaning | Catches |
|---|---|---|
| `co_tweet` | identical text | copy-paste bot rings |
| `co_similar_tweet` | near-identical text (Jaccard similarity of word sets) | "paraphrase" rings |
| `co_link` | same URL | pushing a fake-news site |
| `co_reply` | replying to the same post | pile-on harassment |
| `co_retweet` | reposting the same post | amplification networks |

Parameters (from `.env`):
- `TIME_WINDOW_SECONDS = 60` — shorter windows are stronger evidence; under ~5 s suggests automation.
- `MIN_EDGE_WEIGHT = 2` — two accounts must coordinate at least twice, filtering coincidences.

Toolkit calls (verified against its source):

```python
from coordination_network_toolkit import preprocess, graph, compute_networks as cn

preprocess.preprocess_data(db_path, rows)   # rows: (message_id, user_id, username, repost_id, reply_id, message, timestamp, urls)
cn.compute_co_tweet_network(db_path, time_window=60, min_edge_weight=2)
g = graph.load_networkx_graph(db_path, "co_tweet")   # networkx DiGraph with weight + edge_type
```

All five networks are merged into one undirected weighted graph; each edge remembers which signals it came from.

### Stage 2 — Campaign discovery (`engine/campaigns.py`)

- Drop edges below the weight threshold.
- `nx.community.louvain_communities(G, weight="weight", seed=42)` (fixed seed → reproducible).
- Keep communities with **≥ 5 accounts** as candidate campaigns.

### Stage 3 — Explainable CIB score (`engine/scoring.py`)

Each feature is normalised to 0–1; the score is a weighted sum × 100. Every feature's contribution is stored so the UI can show *why*.

| Feature | Definition | Initial weight |
|---|---|---|
| Speed | 1 − (median seconds between coordinated posts ÷ time window) | 0.25 |
| Duplication | share of the campaign's posts that are exact or near duplicates | 0.25 |
| Multi-signal | (number of distinct coordination types − 1) ÷ 4 | 0.15 |
| Fresh accounts | share of accounts younger than 30 days at first post | 0.15 |
| Burst | peak posts/minute vs the dataset's median, capped at 1 | 0.10 |
| Concentration | share of posts using the campaign's top hashtag or URL | 0.10 |

Weights are hand-set and tuned on our scenario (documented as a limitation). Upgrade path: fit a logistic regression on labelled IO vs control accounts.

### Stage 4 — Bob threat analysis (Section 9)

For each campaign above the threshold (default score ≥ 50), Bob classifies the threat from the stats + ~10 representative posts. Legal suggestions are restricted to the IDs in our legal table (Section 15); anything else is dropped in code.

### Stage 5 — Escalation and brief (`engine/escalation.py`, `brief/render.py`)

Escalation is **deterministic** (predictable, auditable); Bob only explains it.

| Level | Rule |
|---|---|
| **URGENT** | `incitement` AND `offline_call_to_action`, OR score ≥ 80 with severity ≥ 4 |
| **ALERT** | `organized_misinformation` or `targeted_harassment` with score ≥ 60 |
| **MONITOR** | everything else, including `benign_coordination` |

Recommended actions per level (suggestions for the officer):
- **URGENT:** notify SHO / district control room; preserve evidence; request platform takedown through the platform's law-enforcement channel; consider preventive orders (Section 163 BNSS); issue public advisory.
- **ALERT:** cyber cell review; fact-check / counter-messaging; monitor the campaign's accounts.
- **MONITOR:** keep watching; no action.

Brief contents: generation time (IST); dataset SHA-256; **executive summary written by Bob**; per campaign — summary, timeline, account count, score breakdown, Bob verdict, evidence table (post ID, time, SHA-256 of text), legal suggestions (from the fixed table, marked for verification), escalation level and actions; limitations. Everything except the executive summary is filled in by code from stored data.

---

## 9. IBM Bob Integration

Bob is used in five places (see the table in Section 7.2). The two runtime calls go through `bob run` with our API key. The investigation console uses Bob chat with IBMid sign-in.

### 9.1 Headless campaign classifier (`src/bob/client.py`)

**Tested on 26 Sept with our API key (Bob Shell 2.0.5):**

| Finding | Result | Consequence |
|---|---|---|
| `bob run` + `BOB_API_KEY` (General key) | Works; **no `--team-id` needed** | Key goes in `src/.env` only |
| Signed-in Bob Shell without a key | `bob run` fails: "Bob API key is required" | Key is required for the backend |
| Cost of one campaign classification (8 posts + stats) | **~0.025 coins, ~11 s**, 0 tool calls | 40 coins ≈ 1,600 classifications — classification is cheap; coding sessions are the real coin spend |
| Long multi-line prompt as a CLI argument | **Hung on Windows** | **Always send the prompt through stdin** |
| JSON output | Valid JSON matching our schema | Pydantic validation works |
| Bob's free-form legal suggestions | **Partly wrong** (suggested BNS 152 for a local rumour; misdescribed BNS 197; stretched IT Act 66D) | **Bob must choose sections from our fixed table; code rejects anything else** |
| Direct HTTP inference API (`api.us-east.bob.ibm.com/inference/v1`) | Blocked by Cloudflare for non-Bob clients; undocumented | **Not used** — `bob run` is the official path |

```python
BOB = shutil.which("bob")   # on Windows resolves the npm shim — don't hardcode "bob"

out = subprocess.run([BOB, "run", "--accept-license", "--format", "json",
                      "--max-turns", "2", "--max-cost", MAX_COST,
                      "--disable-mcp", "--disable-subagents",
                      "Classify the campaign described on stdin. Follow its instructions exactly."],
                     input=prompt,                      # prompt via stdin, never as an argument
                     cwd=empty_work_dir,                # Bob sees no repo files
                     env={**os.environ, "BOB_API_KEY": key},
                     capture_output=True, text=True, timeout=120)
reply = json.loads(out.stdout)["last_message"]      # Bob's answer (our JSON)
verdict = BobVerdict.model_validate_json(extract_json(reply))
```

**How the prompt is built:** the code reads `.bob/rules-osint-analyst/*.md` (legal table, escalation rules, no-profiling rule) and puts them into the prompt, followed by the output schema, the campaign stats and ~10 representative posts. Because `bob run` runs in an empty working folder, it does not load the repo's `.bob/` mode by itself — embedding the rule files keeps **one source of truth** for both `bob run` and Bob chat.

Safeguards:
- **Schema validation** with Pydantic; invalid output → one retry, then an error (no guessed verdict is shown or cached).
- **Evidence check:** every cited post ID must belong to the campaign; others are dropped.
- **Legal whitelist:** Bob answers with section IDs from the legal table (e.g. `BNS-353`); any ID not in the table is dropped in code, and the code adds the official title and IPC equivalent.
- **Cache:** results saved to `data/runs/<id>/bob/<campaign>.json` — each campaign costs coins once; the demo replays from cache.
- **Coin cap:** `--max-cost` per call; `stats.session_costs` from the JSON output is logged.
- **Parallel calls:** campaigns are classified concurrently (~11 s each) with a spinner in the UI.
- **No key → no crash:** if `BOB_API_KEY` is missing, the classify route returns the cached verdict or a clear "Bob not configured" message.

### 9.2 Brief executive summary (`src/brief/render.py`)

One `bob run` call per brief (same client, same safeguards). Input: the verified verdicts, scores and escalation levels. Output: a 5–8 sentence executive summary for the SHO following the `threat-brief` skill's structure. All other brief sections come from stored data, so Bob cannot invent evidence in the brief. Cached per dataset.

### 9.3 Custom mode, rules and skill (`.bob/`)

- `custom_modes.yaml` → `osint-analyst` mode for Bob chat: role, cite only real post IDs, legal sections are suggestions from the table, never label people by religion, caste or community. Tool groups: `read` and `mcp` only (no editing or shell commands).
- `rules-osint-analyst/` → `01-legal-table.md` (Section 15, with IDs), `02-escalation.md` (Section 8), `03-no-profiling.md`. These files are also embedded into `bob run` prompts.
- `skills/threat-brief/SKILL.md` → structure and tone of the brief (used by Bob chat and mirrored in the summary prompt).
- `mcp.json` → registers our MCP server as `threat-intel`.

### 9.4 MCP investigation console (`src/mcp_server/server.py`)

A FastMCP server exposing read-only tools over the same results:

| Tool | Returns |
|---|---|
| `list_datasets()` | analysed datasets |
| `list_campaigns(dataset_id)` | campaigns sorted by score |
| `get_campaign(dataset_id, campaign_id)` | stats, features, verdict |
| `get_posts(dataset_id, campaign_id, limit)` | posts with timestamps, oldest first |
| `timeline(dataset_id, campaign_id)` | posts per minute |
| `account_profile(dataset_id, account_id)` | account age, post count, campaigns |

Registered in `.bob/mcp.json`. How it runs: open a terminal in the repo root → `bob chat` (IBMid sign-in) → `/mode osint-analyst` → `/mcp` shows `threat-intel`. An officer can ask *"Who posted first in campaign 2 and how fast did it spread?"* and Bob answers with cited post IDs. The MCP server only reads `data/runs/`, so it works after the web app has analysed a dataset.

### 9.5 AI coding partner

We use Bob (Plan mode → Agent mode) to plan and build the project, with our global skills (`/kickoff`, `/demo`, `/submit-check`).

### 9.6 API keys

- **Type:** create an **Inference** key (bob.ibm.com → your instance → API keys). It can only run inference, so a leak does less damage than a General key. Our test used a General key and needed no team ID.
- **Storage:** `src/.env` only (gitignored). `src/.env.example` documents the variable with an empty value.
- **Key Hygiene:** Any key that was ever pasted into chat or a commit is revoked immediately.
- **Check before every push:** `git grep -E "bob_prod_[A-Za-z0-9_-]{30,}"` must return nothing.
- **Deployment:** The setup guide explains that live Bob analysis needs an API key; pre-assessed cached datasets run without one.

### Cost & Resource Profile

- Measured: one classification ≈ **0.025 coins** — the application itself is highly cost-efficient to operate.
- Pre-classify demo campaigns once (cached); keep live inference for new incoming batches.
- Coding assistance: specific modular prompts with clean sessions per feature.

---

## 10. Tech Stack and Why

| Layer | Choice | Why | Alternatives rejected |
|---|---|---|---|
| Coordination detection | `coordination_network_toolkit` (QUT, MIT) | Published methods; parallelised; verified; returns NetworkX graphs | Writing our own pairwise comparisons (slow, unproven) |
| Graph analysis | NetworkX (Louvain) | Standard, pure Python, built into toolkit output | Neo4j (extra server), igraph (install friction) |
| Backend | FastAPI + Uvicorn + Pydantic | Fast to write; automatic validation; serves the static frontend | Flask (no validation), Django (too heavy) |
| Storage | Toolkit SQLite + JSON files | Nothing to install; easy to inspect and cache | MongoDB/Postgres (extra services) |
| AI | IBM Bob: `bob run` with an API key (runtime), Bob chat + MCP (console), `.bob/` mode/rules/skill | Primary AI reasoning engine; makes Bob load-bearing; tested cost ~0.025 coins per call | watsonx (no access), OpenAI (not IBM), Bob's undocumented HTTP inference API (blocked by Cloudflare for non-Bob clients) |
| MCP server | Python `mcp` SDK (FastMCP) | ~40 lines; same code as the engine | Custom JSON-RPC |
| Frontend | React 19 + Vite (JavaScript) | Team decision; components map cleanly to our 4 tabs and side panel; fast dev server with hot reload; `/api` proxy | Vanilla JS (harder to manage state), Streamlit (team decision), TypeScript (extra friction for a one-day build) |
| Styling | Tailwind CSS v4 (`@tailwindcss/vite`) | Fast to style without writing CSS files; print styles via `print:` variants | Component libraries (heavier, more to learn) |
| Graph UI | Cytoscape.js (used directly from a React effect) | Built for network graphs; click/zoom/layouts | D3 (more code), vis.js |
| Charts | Hand-drawn SVG | One line chart needs no chart library | Recharts, Chart.js |
| State & data | React `useState` + a small `api.js` fetch wrapper | Four tabs and one selected campaign — no need for a state library | Redux, React Query (unnecessary for this size) |
| PDF | `window.print()` + print CSS | Zero dependencies | ReportLab, WeasyPrint |
| Testing | pytest | One engine test proves the core works | — |

---

## 11. Data Model and API Contract

### Data model (`src/engine/schema.py`)

```python
class Post(BaseModel):
    post_id: str; account_id: str; username: str
    created_at: int                      # unix seconds
    text: str
    repost_of: str | None = None; reply_to: str | None = None
    urls: list[str] = []; hashtags: list[str] = []
    account_created_at: int | None = None

class Campaign(BaseModel):
    id: str; accounts: list[str]; post_ids: list[str]
    size: int; top_hashtag: str | None = None
    score: int                           # 0-100
    features: dict[str, int]             # contribution points per feature (sum = score) → "why flagged"
    signals: list[str]                   # e.g. ["co_tweet", "co_link"]
    first_seen: int; last_seen: int

class BobVerdict(BaseModel):
    threat_type: Literal["incitement", "targeted_harassment",
                         "organized_misinformation", "benign_coordination"]
    target: str; narrative: str
    severity: int                        # 1-5
    offline_call_to_action: bool
    legal_suggestions: list[LegalSuggestion]
    evidence_post_ids: list[str]

class LegalSuggestion(BaseModel):
    id: str                              # must exist in the legal table, e.g. "BNS-353"
    why: str                             # Bob's one-line reason
    # title and IPC equivalent are added by code from the legal table
```

### Storage layout

```
data/runs/<dataset_id>/
  posts.json          normalized posts
  toolkit.db          coordination-network-toolkit SQLite
  campaigns.json      Campaign[]
  graph.json          Cytoscape elements
  timeline.json       posts per minute
  bob/<campaign>.json cached BobVerdict
  bob/summary.json    cached executive summary
  brief.html          last generated brief
```

### REST API (agree first — the React app builds against mock JSON in these shapes; examples in `execution-plan.md`)

| Method & path | Returns |
|---|---|
| `POST /api/datasets` (CSV upload) | `{dataset_id, posts, accounts}` |
| `GET /api/datasets` | all datasets (bundled demo + uploads) with post/account counts |
| `GET /api/datasets/{id}/campaigns` | campaign list for an analysed dataset |
| `GET /api/datasets/{id}/campaigns/{cid}/verdict` | cached Bob verdict + escalation (404 if not classified; never calls Bob) |
| `POST /api/datasets/{id}/analyze` | `{campaigns: Campaign[]}` |
| `GET /api/datasets/{id}/graph` | `{nodes: [{data: {id, label, campaign}}], edges: [{data: {source, target, weight, signals}}]}` |
| `GET /api/datasets/{id}/timeline` | `{bucket_seconds, campaign_ids: [...], points: [{t, total, c1, c2, ...}]}` (drawn by the SVG timeline) |
| `GET /api/datasets/{id}/campaigns/{cid}` | `Campaign` + `sample_posts` |
| `POST /api/datasets/{id}/campaigns/{cid}/classify` | `{verdict: BobVerdict (legal IDs enriched with title + IPC), escalation: {level, actions}, cached: bool, cost}` |
| `GET /api/datasets/{id}/brief` | full printable HTML page (calls Bob once for the executive summary, then cached) |
| `GET /api/status` | `{bob_configured: bool}` — true only when `BOB_API_KEY` is set and the Bob Shell CLI is found; the header shows "IBM Bob ready" or "saved results only" |

---

## 12. Frontend

React 19 single-page app in `src/web/`, built with Vite. The visual language, tokens and page layout are defined in [`design-system.md`](design-system.md). Four pages; the current page and dataset are kept in the URL (`#/overview/demo`), so reload and Back work. The Overview leads with the planned offline gatherings, then an incident timeline, the campaign table, a district spread map and the detail panel.

| Page | Contents |
|---|---|
| **Datasets** | upload box (formats listed) and a table of all datasets with status (Not analysed / Analysing step n of 10 / Ready / Failed) and Open, Analyse, Delete |
| **Overview** | 4 key numbers (campaigns, urgent, alert, not assessed), activity timeline, campaign table with the selected campaign's detail beside it |
| **Network** | Cytoscape graph coloured by campaign (selected campaign highlighted and labelled) with the same detail panel |
| **Brief** | the printable brief in a frame, with Open in new tab and Print |

The campaign detail panel shows identity, the coordination score with plain-language "why flagged" bars, the IBM Bob assessment (or the **Ask IBM Bob** button) and the first posts, marking the ones Bob cited. A dataset that is not analysed or is being analysed shows a state card with the step list and elapsed time instead of results.

```
src/web/src/
  main.jsx  App.jsx (shell, routing, data loading, polling)  api.js  index.css (tokens)  ui.jsx (primitives)  labels.js (plain-language labels)
  views/       DatasetsView.jsx  OverviewView.jsx  NetworkView.jsx  BriefView.jsx
  components/  CampaignPanel.jsx  TimelineChart.jsx  NetworkGraph.jsx  AnalysisState.jsx
```

- **State:** `App.jsx` holds the dataset list, the current dataset's results and the selected campaign; the panel loads its own campaign details and cached verdict.
- **Analysis:** `POST /analyze` starts a background job; the app polls `/api/datasets` every 1.5 s while any job runs.
- **API layer:** `api.js` has one function per endpoint.
- **Dev:** `npm run dev` (port 5173) with a Vite proxy for `/api` → `http://127.0.0.1:8000`.
- **Demo / judges:** `npm run build` → `src/web/dist/`, served by FastAPI at `http://127.0.0.1:8000` (one process). `dist/` is gitignored, so the setup guide includes the build step.

---

## 13. Data Strategy

There is **no public dataset of Indian coordinated campaigns labelled account by account** — platforms do not release them and the X API is paid. So we use three layers.

### Layer 1 — Real coordinated campaigns (prove the detector works on real data)

| Dataset | What | Access |
|---|---|---|
| [X/Twitter Information Operations archive](https://archive.org/details/X_Twitter_Information_Operations) | Platform-confirmed state-linked accounts; has tweet time, retweet target, hashtags, URLs, account creation date. File begins with Bangladesh-linked accounts. | Public. File is 113 GB — download a slice: `curl -L -r 0-300000000 -o io_sample.csv https://archive.org/download/X_Twitter_Information_Operations/ioa_tweets.csv` |
| [FiveThirtyEight IRA tweets](https://github.com/fivethirtyeight/russian-troll-tweets) | ~3M tweets from Russia's Internet Research Agency, labelled by troll type (RightTroll, LeftTroll, HashtagGamer, …) | Direct CSV download. No retweet-target IDs, so co-retweet is unavailable |
| [Labeled IO datasets](https://zenodo.org/records/14188947) (Indiana Univ./USC) | 26 campaigns + control accounts using the same hashtags on the same days — ideal for precision/recall | **Restricted** — request access; may not arrive in time |

### Layer 2 — Real Indian text (test Bob's threat labels)

| Dataset | What | Access |
|---|---|---|
| [CONSTRAINT-2021 Hindi hostility](https://github.com/mohit19014/Hindi-Hostility-Detection-CONSTRAINT-2021) | 5,728 training posts labelled non-hostile 3,050 · fake 1,144 · hate 792 · offensive 742 · defamation 564 (counted by us) | Direct from GitHub |
| [HateXplain](https://github.com/hate-alert/HateXplain) | ~20k posts with target community and rationale words | GitHub |
| [HASOC](https://hasocfire.github.io/) | Hindi/English/Marathi hate and offensive posts | Registration form |
| Kaggle: [Delhi riots tweets](https://www.kaggle.com/datasets/hamzaafridi/delhi-riots-tweets), [Farmers protest tweets](https://www.kaggle.com/datasets/prathamsharma123/farmers-protest-tweets-dataset-csv) | Real organic Indian posts for background chatter | Kaggle login |

### Layer 3 — Demo scenario (our generator, `src/scenario/generate_scenario.py`)

- **Background:** ~800 accounts posting harmless text over 48 hours (non-hostile CONSTRAINT posts / Kaggle tweets), random realistic timing, realistic account ages.
- **Planted campaigns:**
  - **A — Rumour ring:** 40 new accounts post near-identical text with one hashtag in 30-second bursts (organized misinformation).
  - **B — Link ring:** 25 accounts share the same fake-news URL within 60 seconds.
  - **C — Harassment pile-on:** 30 accounts reply to one journalist's post with similar abusive text within minutes.
  - **D — Decoy:** a cricket fan-club hashtag storm — coordinated but benign; must score lower.
- **Fictional names only** (made-up town, groups, people) — never real communities.
- Outputs `posts.csv` + `truth.json` (which accounts belong to which planted campaign).

---

## 14. Evaluation Plan

Numbers for the README (judges value measured results):

| Metric | How |
|---|---|
| Campaign detection precision / recall | Compare detected campaigns with `truth.json` from the scenario |
| Decoy ranking | Decoy D scores below A, B, C |
| Real-data sanity | On the IO slice: coordinated clusters found; on IRA: cluster match against troll categories |
| Bob agreement | ~100 CONSTRAINT posts: Bob's label vs human label (mapped: fake → misinformation, hate → incitement/hate, offensive/defamation → harassment/defamation) |
| Runtime | Time to analyse the demo dataset |

`src/eval/measure.py` prints these; `src/tests/test_engine.py` asserts A, B, C are found and D ranks lowest.

---

## 15. Legal Reference Table

**All mappings are suggestions for verification by a legal officer.** The tool never states that an offence was committed.

This table is stored as `.bob/rules-osint-analyst/01-legal-table.md` — the **single source** used by Bob chat, embedded in `bob run` prompts, and parsed by code to validate Bob's answers.

**Why a fixed table:** in our 26 Sept test, Bob's free-form suggestions for a mock dam rumour included BNS 152 (acts endangering sovereignty — far too serious), misdescribed BNS 197, and stretched IT Act 66D. With a fixed table Bob can only choose from sections we have checked.

### Offence sections — Bob may suggest these (by ID)

| ID | Law & section | Old IPC | Covers | Typical threat type |
|---|---|---|---|---|
| `BNS-196` | BNS 196 | 153A | Promoting enmity between groups | incitement |
| `BNS-197` | BNS 197 | 153B | Imputations/assertions prejudicial to national integration | incitement |
| `BNS-351` | BNS 351 | 506 | Criminal intimidation (threats) | targeted_harassment |
| `BNS-353` | BNS 353 | 505 | Statements conducing to public mischief (rumours causing fear or alarm) | organized_misinformation |
| `BNS-356` | BNS 356 | 499/500 | Defamation | targeted_harassment |
| `BNS-79` | BNS 79 | 509 | Word, gesture or act intended to insult the modesty of a woman | targeted_harassment |
| `BNS-61` | BNS 61 | 120A/120B | Criminal conspiracy (coordination evidence) | any, with strong coordination |
| `ITA-66D` | IT Act 66D | — | Cheating by personation using a computer resource | impersonation accounts only |
| `ITA-67` | IT Act 67 | — | Publishing obscene material in electronic form | harassment with obscene content |

### Procedural references — used by escalation and the brief, never suggested as offences

| ID | Law & section | Old law | Used for |
|---|---|---|---|
| `ITA-69A` | IT Act 69A | — | Blocking of public access (Central Government power; police request through the proper channel) |
| `BNSS-163` | BNSS 163 | CrPC 144 | Preventive orders in urgent cases |
| `BSA-63` | BSA 63 | Evidence Act 65B | Electronic-record certificate — our SHA-256 hashes support it |

**Never used:** IT Act **66A** — struck down by the Supreme Court (Shreya Singhal v. Union of India, 2015).

---

## 16. Ethics, Safety and Limitations

- **Decision support, not a verdict.** Every output is a lead for a trained officer.
- **No profiling.** Classification uses behaviour and content only; Bob is instructed never to infer or label people by religion, caste or community.
- **Mock and research data only.** Fictional names in the scenario; no real private individuals.
- **Benign coordination** is an explicit class to reduce false alarms on fan groups, news sharing and legitimate protest organising.
- **Evidence integrity:** SHA-256 hashes of input and evidence.

**Known limitations (to state honestly in the README):**
- No live platform ingestion.
- Score weights are hand-set.
- Bob classification quality on Hindi/Hinglish and regional languages is not formally evaluated beyond the CONSTRAINT sample.
- Legal mapping is a reference table, not legal advice.

---

## 17. Repository Layout

```
.bob/
  custom_modes.yaml
  rules-osint-analyst/  01-legal-table.md  02-escalation.md  03-no-profiling.md
  skills/threat-brief/SKILL.md
  mcp.json
src/
  engine/   schema.py  normalize.py  coordination.py  campaigns.py  scoring.py  escalation.py  pipeline.py
  bob/      client.py
  brief/    render.py
  api/      main.py
  mcp_server/ server.py
  web/      React + Vite app (see Section 12); dist/ is build output (gitignored)
  scenario/ generate_scenario.py  adapters/  download_datasets.py
  samples/  packs/ (3 incident packs with ground truth)  demo_runs/ (their pre-analysed runs incl. cached Bob verdicts)
  eval/     measure.py
  tests/    test_engine.py
  requirements.txt  .env.example  README.md  main.py
data/       (gitignored) downloaded datasets + runtime output data/runs/<dataset_id>/
docs/  demo/  presentation/  submission.yaml  README.md
```

`src/main.py` starts the app (`uvicorn api.main:app`) and serves `src/web/dist/`. Large datasets stay out of git (`download_datasets.py` fetches them). `src/.env` (holds `BOB_API_KEY`) and the root `data/` folder are gitignored; the bundled `src/samples/demo_runs/` are committed so judges can see full results, including Bob verdicts, without a key. On first start the app copies each into `data/runs/<pack>`.

---

## 18. Build Plan

The step-by-step build order is in [`execution-plan.md`](execution-plan.md): setup → engine → API → Bob → frontend → brief and MCP → proof → submit.

Already done: `bob run` with an API key tested — works, ~0.025 coins and ~11 s per classification, prompt must go via stdin.

### Priority if time runs short (cut from the bottom)

1. Engine + graph + campaign list (must have)
2. Bob classification + escalation (must have — it is the Bob story)
3. Threat brief
4. MCP console in Bob chat
5. Real-dataset runs and evaluation numbers
6. UI polish

---

## 19. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Bob coins run out | Classification is cheap (~0.025/call, measured); the risk is coding sessions — `/compact`, fresh sessions, check `/status`; cache verdicts; `--max-cost` |
| Bob returns invalid JSON | Pydantic validation, extract the JSON object, one retry, then a clear error |
| Bob suggests wrong or excessive legal sections | Fixed legal table with IDs; code drops unknown IDs (seen in testing: BNS 152 for a rumour) |
| Bob refuses harsh mock content | Keep mock text mild and fictional; frame as analyst task |
| `bob run` hangs on Windows | Never pass the prompt as a command-line argument — always stdin; `timeout=120` |
| `bob` not found from Python on Windows | Use `shutil.which("bob")` (resolves the npm shim) |
| API key leaked | Keys only in gitignored `src/.env`; Inference keys; `git grep -E "bob_prod_[A-Za-z0-9_-]{30,}"` before every push; revoke after the event |
| No key on a judge's machine | App runs without a key; cached verdicts for the bundled demo run; setup guide explains |
| Node too old for Bob | Node 24 on every laptop |
| Toolkit slow on big data | Demo dataset ~5–10k posts; co-similarity only on demo sizes |
| Integration breaks late | Fixed API contract; test the full journey at each milestone; stop adding features well before the deadline |
| Frontend build fails on a judge's machine | Setup guide pins `npm ci` + `npm run build`; Node 24 already required for Bob; tested on a clean machine |
| Code accidentally gitignored | Never put code in a folder named `data/`, `build/` or `dist/`; check `git status` shows new files |
| Validator red | Run it early; fill `submission.yaml` completely; real video link |
| Wi-Fi at venue | Datasets and dependencies downloaded in advance; cached Bob results |
| Overclaiming in docs | Update README only with what actually works; keep limitations honest |

---

## 20. Demo Script (3–5 minute video)

1. **(0:00–0:30) Problem** — one slide: Delhi 2020 case; per-post tools miss coordination.
2. **(0:30–1:00) Start app, upload scenario** → Analyze.
3. **(1:00–2:00) Overview + Network** — timeline bursts; graph lights up campaigns A, B, C; decoy D scores low; open campaign A's "why flagged".
4. **(2:00–3:00) Ask Bob** — verdict: organized misinformation, target, severity, BNS 353 suggestion, evidence IDs; escalation ALERT/URGENT.
5. **(3:00–3:45) Brief** — print-ready brief with hashes and actions.
6. **(3:45–4:30) Bob chat** — *"Which accounts started campaign A?"* via MCP tools.
7. **(4:30–5:00) Numbers + honest limitation** — precision/recall on scenario, one limitation.

---

## 21. Submission Checklist

- [ ] `submission.yaml` — all required fields, all four members
- [ ] `README.md` — matches what the code actually does; numbers filled
- [ ] `docs/` — problem, solution, architecture, setup guide (tested by a teammate)
- [ ] `src/` — all code; `.env.example` complete; no `.env`, `.venv`, `node_modules`, datasets
- [ ] `git grep -E "bob_prod_[A-Za-z0-9_-]{30,}"` returns nothing (no API key anywhere in the repo or history)
- [ ] `.bob/` committed: mode, rules (legal table), skill, `mcp.json`
- [ ] `demo/demo-video-link.txt` — real unlisted YouTube / Loom / Drive link, "anyone with the link"
- [ ] `demo/live-demo-url.txt` — `NOT DEPLOYED`
- [ ] `demo/screenshots/` — at least 3 (`01-…png`, `02-…png`, `03-…png`)
- [ ] `presentation/slides.pdf`
- [ ] Repo public; **Validate Submission** green
- [ ] Form submitted at ibm.biz/bob-ai-nfsu between 12:00 and 19:00 with the correct repo URL
- [ ] README credits the QUT coordination-network-toolkit and datasets used

---

## 22. References

- QUT Digital Observatory — [coordination-network-toolkit](https://github.com/QUT-Digital-Observatory/coordination-network-toolkit)
- Keller, Schoch, Stier & Yang (2020). Political Astroturfing on Twitter: How to Coordinate a Disinformation Campaign. *Political Communication* 37(2).
- Giglietto, Righetti, Rossi & Marino (2020). It takes a village to manipulate the media: coordinated link sharing behavior during 2018 and 2019 Italian elections. *Information, Communication & Society*.
- Seckin et al. — [Labeled Datasets for Research on Information Operations](https://zenodo.org/records/14188947) (ICWSM 2025)
- Bhardwaj et al. (2020) — [Hostility Detection Dataset in Hindi](https://arxiv.org/abs/2011.03588) (CONSTRAINT-2021)
- IBM Bob Shell docs — [bob.ibm.com/docs/shell](https://bob.ibm.com/docs/shell), [non-interactive `bob run`](https://bob.ibm.com/docs/shell/getting-started/start-bobshell-non-interactive), [API keys](https://bob.ibm.com/docs/ide/account/api-keys), [MCP](https://bob.ibm.com/docs/shell/configuration/mcp/mcp-bobshell), [custom modes](https://bob.ibm.com/docs/shell/configuration/custom-modes-bobshell), [skills](https://bob.ibm.com/docs/shell/features/skills)
- NetworkX — [louvain_communities](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.louvain.louvain_communities.html)
