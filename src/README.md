# SHIN-CHAN Source Code Architecture

This directory houses the complete implementation of the **Social Media Threat Intelligence Engine (Track 2: Cyber Forensics)** for the IBM Bob AI Innovation Hackathon.

## Architecture & Directory Layout

```
src/
├── api/                  # FastAPI backend application
│   ├── __init__.py
│   └── main.py           # REST endpoints (datasets, background analysis jobs, campaigns, verdict, classify, brief)
├── bob/                  # IBM Bob integration & legal reasoning
│   ├── __init__.py
│   ├── client.py         # Headless CLI invocation (`bob run`), JSON schema parsing & validation
│   └── legal.py          # BNS 2023 & IT Act statutory table parser and section filter
├── brief/                # Police operational threat briefs
│   ├── __init__.py
│   └── render.py         # Section 63 BSA-compliant HTML/PDF brief generator with SHA-256 evidence chain
├── engine/               # Behavioral Coordination Detection (CIB)
│   ├── __init__.py
│   ├── campaigns.py      # Louvain community clustering & campaign aggregation
│   ├── coordination.py   # Multi-signal network construction (coordination-network-toolkit + NetworkX)
│   ├── normalize.py      # Language detection and time parsing for X posts
│   ├── explore.py        # Posts view search/filters and the "at a glance" dataset numbers
│   ├── incident.py       # Spread profile: seeds, amplifiers, platform/town paths, speed, detection time
│   ├── pipeline.py       # End-to-end analysis orchestrator (graph, timeline, JSON output)
│   ├── schema.py         # Pydantic data models (Post, Campaign, LegalSuggestion, BobVerdict)
│   ├── scoring.py        # Explainable CIB risk scoring (0-100) with 6 forensic feature weights
│   ├── streaming.py      # SQLite store for the rolling-window stream API (event-time retention, idempotent posts)
│   ├── xstore.py         # X API v2 JSON in: checks it, stores it in x.db (one table per X object), posts view
│   └── zones.py          # Each dataset's display clock (IST or UTC) and local-time text
├── eval/                 # System evaluation & benchmarking
│   ├── __init__.py
│   ├── measure.py        # Accuracy, recall, decoy discrimination & runtime benchmark
│   └── results.md        # Benchmarking outcomes and forensic metrics
├── mcp_server/           # Model Context Protocol (MCP) server
│   ├── __init__.py
│   └── server.py         # FastMCP tools (list_datasets, list_campaigns, get_campaign, get_posts, timeline, account_profile)
├── connectors/
│   └── x_search.py       # X recent search (needs X_BEARER_TOKEN): response pages stored like an upload
├── tests/                # Automated verification
│   ├── conftest.py
│   ├── fixtures.py       # Test data as X API v2 responses (built at test time)
│   ├── test_engine.py    # Planted rings in an X API response: found, nothing else clustered
│   ├── test_incident.py  # Spread profile and detection time on a hand-made campaign
│   ├── test_bob_validation.py # Bob answers: legal-table whitelist, evidence IDs, schema rejection
│   ├── test_streaming.py # Stream store: duplicates, out-of-order posts, retention, close
│   ├── test_xstore.py    # X API v2 mapping, database tables, refusals and warnings, stream lines, X search paging
│   └── test_api.py       # Upload → background analysis → campaigns → delete, and the stream API
├── web/                  # Production React 19 + Vite frontend
│   ├── dist/             # Built by `npm run build` (gitignored), served by FastAPI
│   ├── src/              # App shell, views/ (Datasets, Overview, Network, Posts, Brief), components/, ui.jsx, design tokens (docs/design-system.md)
│   └── package.json
├── config.py             # Centralized environment & path configuration
├── main.py               # Single entrypoint launching Uvicorn web server
└── requirements.txt      # Python dependencies
```

## Setup & Running

### 1. Install
```bash
pip install -r src/requirements.txt
cd src/web && npm ci && npm run build && cd ../..
```

### 2. Configure Environment
```bash
cp src/.env.example src/.env
# Add your IBM Bob API key (needed for new IBM Bob assessments) and, optionally, X_BEARER_TOKEN
```

### 3. Run the Application
```bash
python src/main.py
```
Open **http://127.0.0.1:8000** in your browser. It starts empty: upload an export or search X on the **Datasets** page.

### 4. Run Automated Tests
```bash
pytest src/tests
```

### 5. Run Benchmarking & Evaluation
```bash
python src/eval/measure.py
```
