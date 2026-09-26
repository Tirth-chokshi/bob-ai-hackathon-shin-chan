# SHIN-CHAN Source Code Architecture

This directory houses the complete implementation of the **Social Media Threat Intelligence Engine (Track 2: Cyber Forensics)** for the IBM Bob AI Innovation Hackathon.

## Architecture & Directory Layout

```
src/
├── api/                  # FastAPI backend application
│   ├── __init__.py
│   └── main.py           # REST endpoints (/api/status, /datasets, /graph, /timeline, /campaigns, /classify, /brief)
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
│   ├── normalize.py      # Multi-source dataset normalizer & schema loader
│   ├── pipeline.py       # End-to-end analysis orchestrator (graph, timeline, JSON output)
│   ├── schema.py         # Pydantic data models (Post, Campaign, LegalSuggestion, BobVerdict)
│   └── scoring.py        # Explainable CIB risk scoring (0-100) with 6 forensic feature weights
├── eval/                 # System evaluation & benchmarking
│   ├── __init__.py
│   ├── measure.py        # Accuracy, recall, decoy discrimination & runtime benchmark
│   └── results.md        # Benchmarking outcomes and forensic metrics
├── mcp_server/           # Model Context Protocol (MCP) server
│   ├── __init__.py
│   └── server.py         # FastMCP tools (list_datasets, list_campaigns, get_campaign, get_posts, timeline, account_profile)
├── samples/              # Committed scenario data & demo bundle
│   ├── demo_run/         # Pre-analyzed demo bundle with cached Bob verdicts
│   ├── scenario_posts.csv# 4,538 synthetic Sundarpur posts
│   └── truth.json        # Ground-truth labels for planted campaigns
├── scenario/             # Dataset generation & format adapters
│   ├── __init__.py
│   ├── generate_scenario.py # Deterministic multi-ring scenario synthesizer
│   └── adapters/         # Adapters for X/Twitter IO archives and FiveThirtyEight IRA trolls
├── tests/                # Automated verification
│   ├── conftest.py
│   └── test_engine.py    # Pytest suite verifying graph, Louvain detection, and decoy ranking
├── web/                  # Production React 19 + Vite frontend
│   ├── dist/             # Production static bundle (served automatically by FastAPI)
│   ├── src/              # React components (Navbar, UploadPanel, NetworkGraph, TimelineChart, CampaignPanel, VerdictCard, BriefView)
│   └── package.json
├── config.py             # Centralized environment & path configuration
├── main.py               # Single entrypoint launching Uvicorn web server
└── requirements.txt      # Python dependencies
```

## Setup & Running

### 1. Python Environment Setup
```bash
pip install -r src/requirements.txt
```

### 2. Configure Environment
```bash
cp src/.env.example src/.env
# Add your IBM Bob API Key (optional for cached demo replay)
```

### 3. Run the Application
```bash
python src/main.py
```
Open **http://127.0.0.1:8000** in your browser. The pre-analyzed demo dataset loads immediately with multi-signal coordination graphs, interactive activity timeline, explainable CIB risk scores, and cached IBM Bob legal verdicts.

### 4. Run Automated Tests
```bash
pytest src/tests
```

### 5. Run Benchmarking & Evaluation
```bash
python src/eval/measure.py
```
