# Project Submission Document

**Project Title:** Social Media Threat Intelligence Engine  
**Team Name:** Team Shin-chan  
**Hackathon Track:** Problem #06 — Track 2: Cyber Forensics (IBM Bob AI Innovation Hackathon / INNOVAI)  
**Repository:** [github.com/Tirth-chokshi/bob-ai-hackathon-shin-chan](https://github.com/Tirth-chokshi/bob-ai-hackathon-shin-chan)  
**Submission Date:** September 2026  

---

## 1. Executive Summary & Proposed Solution

During sensitive public incidents (such as communal tensions, civil protests, or natural disasters), malicious actors, hyper-partisan networks, and bot rings deploy **Coordinated Inauthentic Behavior (CIB)** to rapidly amplify inflammatory rumors, manipulate public opinion, and coordinate offline violence. 

Existing cyber cell monitoring workflows rely on manual post-by-post scanning or simple keyword alerts. This approach consistently fails because **individual posts often appear harmless in isolation**, while working in synchronized concert to spark dangerous real-world unrest.

### The Solution
We have built the **Social Media Threat Intelligence Engine**, an automated, AI-powered cyber-forensics platform that:
1. **Prioritizes Behavior Over Content:** Ingests raw social media data (standard X API v2 format) and mathematically identifies accounts acting in locked temporal synchrony within 60-second windows across 5 orthogonal coordination vectors (same text, similar text, shared links, co-retweets, and reply pile-ons).
2. **Pinpoints Originators & Amplifiers:** Uncovers the exact seed accounts that ignited viral campaigns (e.g., recycling years-old out-of-state violent footage with false local tags) and traces propagation through high-degree amplifier hubs.
3. **Extracts Real-World Physical Threats with IBM Bob:** Uses IBM Bob (Granite LLM) to detect explicit offline gathering calls (*"assemble at Maujpur Chowk at 5:00 PM with sticks"*), estimates threat severity, and automatically maps observed violations to specific Indian legal statutes (**Bharatiya Nyaya Sanhita / BNS 2023** and the **IT Act**).
4. **Delivers Actionable Police Dossiers:** Automatically drafts a Station House Officer (SHO) intelligence memorandum complete with SHA-256 evidence hashing for court admissibility under **Section 63 of the Bharatiya Sakshya Adhiniyam (BSA 2023)**.

---

## 2. Technical Architecture & Approach

The system follows a modular, 5-stage pipeline designed for speed, reproducibility, and explainability:

```
[ Raw X API v2 JSON Stream ]
            │
            ▼
┌───────────────────────────────────────┐
│ 1. Ingestion & Relational Storage     │ ➔ SQLite (`x.db`) relational normalization
│    (`engine/xstore.py`)               │    Unified SQL view (`posts`)
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│ 2. Multi-Signal Graph Fusion          │ ➔ 5 Temporal networks (Δt ≤ 60s)
│    (`engine/coordination.py`)         │    Repeat-edge thresholding (min_weight ≥ 2)
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│ 3. Campaign Clustering & Scoring      │ ➔ Deterministic Louvain Modularity (seed=42)
│    (`engine/campaigns.py`, `scoring`) │    6-Factor CIB Risk Score (0–100)
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│ 4. IBM Bob Threat Intelligence Layer  │ ➔ Headless CLI (`bob run --format json`)
│    (`src/bob/client.py`, `legal.py`)  │    Physical event extraction + BNS sections
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│ 5. Dissemination & Operational UI     │ ➔ React 19 + Cytoscape.js interactive graph
│    (`src/web/`, `brief/render.py`)    │    Print-ready SHO Dossier (HTML / PDF)
└───────────────────────────────────────┘
```

### Key Technical Phases
* **Phase 1: Ingestion & Relational Normalization:** Strict validation of X API v2 responses into an embedded SQLite database (`x.db`), normalizing posts, user profiles, place geolocations, and media attachments into a clean `posts` relational view.
* **Phase 2: Multi-Signal Coordination Detection:** Evaluates pairwise account synchrony within 60-second sliding windows across 5 networks (`co_tweet`, `co_similar_tweet`, `co_link`, `co_retweet`, and `co_reply`). Multi-signal edges are accumulated into an undirected graph, filtering out organic coincidences.
* **Phase 3: Louvain Community Partitioning & CIB Scoring:** Applies deterministic Louvain modularity to group coordinated accounts into discrete campaigns ($c_1, c_2, \dots$). Each campaign receives an explainable 0–100 CIB score based on Speed (25%), Text Duplication (25%), Multi-Signal Diversity (15%), Fresh Account Share (15%), Burst Volume (10%), and Target Concentration (10%).
* **Phase 4: IBM Bob Reasoning & Legal Mapping:** A representative spread sample of posts is passed to IBM Bob via headless CLI. Bob classifies threat type, determines severity (1–5), extracts planned offline gathering parameters (`where`, `at`, `what`), and maps offenses to validated statutory tables (BNS 196, BNS 353, IT Act 66D).
* **Phase 5: Visual Investigation & Brief Generation:** Renders an interactive Cytoscape network graph, a 3-stage propagation flow (*Origin Seeds* $\to$ *Amplification Hubs* $\to$ *Public Impact*), an authentic Twitter/X forensic feed, and a single-click print-ready intelligence dossier.

---

## 3. Key Tools, Technologies & Sources

| Component / Layer | Technology / Tool | Version / Source | Purpose & Role |
|---|---|---|---|
| **AI Reasoning & LLM** | **IBM Bob Shell 2.0** (Granite LLM) | IBM Innovation Hackathon (`npm/bobshell`, headless CLI `bob run`) | Autonomous qualitative threat classification, offline physical event extraction, and legal section mapping. |
| **Agent Tool Protocol** | **FastMCP** | GitHub / PyPI (`fastmcp`) | Model Context Protocol server exposing graph queries, post evidence, and campaign data to Bob. |
| **Coordination Engine** | **Coordination Network Toolkit** | QUT Digital Observatory (Queensland University of Technology, PyPI / GitHub, MIT License) | Core algorithms for detecting temporal co-occurrences (co-tweet, co-retweet, co-link, co-reply). |
| **Graph Algorithms** | **NetworkX** | PyPI (`networkx`) | Louvain community modularity optimization, graph construction, and degree centrality calculation. |
| **Backend Framework** | **FastAPI & Uvicorn** | PyPI (`fastapi`, `uvicorn`) | High-performance asynchronous Python REST API serving datasets, graphs, and live analysis streams. |
| **Data Validation** | **Pydantic v2** | PyPI (`pydantic`) | Strict data typing and schema validation for API inputs, outputs, and Bob structured verdicts. |
| **Local Relational Storage** | **SQLite 3** | Python Standard Library | Zero-dependency, embedded relational database (`x.db`) for storing ingested X API v2 records. |
| **Frontend Framework** | **React 19 & Vite** | npm (`react`, `react-dom`, `vite`) | Fast, reactive Single Page Application (SPA) dashboard architecture. |
| **Network Visualization** | **Cytoscape.js** | npm (`cytoscape`) | High-performance, GPU-accelerated interactive network graph canvas with dynamic layouts. |
| **Styling & Design System** | **Tailwind CSS v4 & Lucide Icons** | npm (`tailwindcss`, `lucide-react`) | Responsive, high-contrast cyber-forensic design system adhering to strict accessibility standards. |

---

## 4. Key Results & Forensic Impact

* **Actionable Lead Time:** Detects coordinated bot mobilization hours before physical crowds converge, giving field police actionable warning.
* **Explainable AI Guardrails:** 100% transparent CIB score breakdown; every legal section and physical gathering quote extracted by IBM Bob is verified in code against database rows, eliminating LLM hallucinations.
* **Court-Admissible Evidence:** Implements SHA-256 evidence hashing for strict compliance with Section 63 of the **Bharatiya Sakshya Adhiniyam (BSA 2023)**.
* **Operational Efficiency:** Processes thousands of posts into a structured Station House Officer briefing dossier in under 60 seconds at a minimal cost of ~0.03–0.04 Bobcoins.

---

## 5. Team Shin-chan

* **Tirth Chokshi** (Lead / Forensics) — System architecture, 5-signal coordination engine, and CIB scoring pipeline.
* **Milind Pawar** (Frontend Engineering) — React 19 UI, Cytoscape network graph, and 3-stage propagation flow.
* **Jainik Devada** (Bob Layer & MCP) — IBM Bob CLI orchestration, FastMCP server, and BNS legal mapping.
* **Jigar Jariwala** (Data & Benchmarking) — X API v2 ingestion adapters, historical riot benchmarks, and evaluation.
