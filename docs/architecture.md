# System Architecture: Social Media Threat Intelligence Engine

## High-Level Architecture

The **Social Media Threat Intelligence Engine** is a pipeline with five parts: an ingestion layer, a coordination-detection and campaign-scoring engine, an IBM Bob threat-analysis layer, a rule-based escalation and brief generator, and two officer interfaces (a web Command Center and Bob chat via MCP).

```mermaid
graph TD
    subgraph Ingestion_Layer ["1. Ingestion"]
        A1[Synthetic post batch] --> B[Normalizer: common schema]
        A2[Research datasets CSV/JSON] --> B
    end

    subgraph Forensic_Pipeline ["2. CIB Engine"]
        B --> C[Coordination networks: co-tweet, co-similarity, co-link, co-reply, co-retweet]
        C --> D[Campaign discovery: NetworkX Louvain]
        D --> E[Explainable CIB score 0-100]
    end

    subgraph Intelligence_Core ["3. Analysis & Escalation"]
        E --> G[IBM Bob threat analysis via bob run]
        G -->|Threat type, severity, evidence IDs| H[Evidence check + legal suggestions]
        H --> I[Escalation rules + Threat Brief generator]
    end

    subgraph Integration_Layer ["4. Officer Interfaces"]
        I --> L[FastAPI REST API]
        L --> M[Command Center Web UI]
        M --> N[Print-ready Threat Brief]
        E --> J[MCP server]
        J <-->|MCP tools| K[IBM Bob chat]
    end
```

---

## Component Details

| Component | Technology | Responsibility |
|---|---|---|
| **API Server** | FastAPI / Uvicorn (Python 3.10+) | Endpoints for dataset upload, analysis, campaigns, graph data, Bob classification, and brief export; serves the static frontend. |
| **Coordination Detection** | coordination-network-toolkit (QUT, MIT) + SQLite | Builds account-to-account coordination networks within configurable time windows. |
| **Campaign Discovery & Scoring** | NetworkX, Python | Community detection on the merged graph; explainable per-feature CIB score. |
| **Threat Analysis** | IBM Bob (`bob run --mode osint-analyst --format json`) | Classifies each campaign, extracts target and narrative, suggests legal sections, cites evidence post IDs. Results cached in SQLite. |
| **Legal Reference & Escalation** | Python rule tables | BNS 2023 / IPC / IT Act reference table and deterministic escalation matrix (MONITOR / ALERT / URGENT). |
| **IBM Bob MCP Server** | Python MCP SDK | Exposes `list_campaigns`, `get_campaign`, `get_posts`, `timeline` so officers can investigate from Bob chat. |
| **Command Center UI** | HTML, CSS, JavaScript, Cytoscape.js, Chart.js | Upload, overview dashboard, posts-per-minute timeline, network graph coloured by campaign, "why flagged" panel, brief preview. |
| **Threat Brief** | Markdown/HTML + print CSS | Time-stamped brief with SHA-256 hashes, timeline, evidence table, legal suggestions, recommended actions. |

---

## End-to-End Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor Officer as Cyber Cell Officer / Duty SHO
    participant UI as Command Center UI
    participant API as FastAPI Backend
    participant CIB as CIB Engine
    participant Bob as IBM Bob

    Officer->>UI: Uploads a post batch
    UI->>API: POST /api/datasets, POST /api/datasets/{id}/analyze
    API->>CIB: Build coordination networks, find campaigns, score them
    CIB-->>API: Campaigns with scores and feature breakdown
    API-->>UI: Campaign list, timeline and graph data
    Officer->>UI: Clicks "Ask Bob" on a campaign
    UI->>API: POST /api/campaigns/{id}/classify
    API->>Bob: bob run (campaign stats + representative posts)
    Bob-->>API: JSON: threat type, severity, legal suggestions, evidence IDs
    API->>API: Verify evidence IDs, apply escalation rules, cache result
    API-->>UI: Classification + escalation level
    Officer->>UI: Clicks "Generate Threat Brief"
    UI->>Officer: Print-ready, time-stamped brief

    opt Investigation from Bob chat
        Officer->>Bob: "Which accounts started campaign 2?"
        Bob->>API: MCP tools: get_campaign, timeline, get_posts
        Bob-->>Officer: Answer with cited post IDs
    end
```

---

## Security Considerations

1. **Offline core:** Coordination detection, scoring, and legal/escalation rules run locally without cloud calls; only the Bob analysis step needs a connection, and its results are cached.
2. **Credential handling:** Keys (e.g., `BOB_API_KEY`) are read only from environment variables; `.env` is excluded by `.gitignore`.
3. **Evidence integrity:** Every input batch and evidence post is hashed with SHA-256 and the hashes are printed in the brief, supporting a tamper-evident record for a Section 63 Bharatiya Sakshya Adhiniyam (BSA) 2023 electronic-evidence certificate.
4. **No profiling:** Classification is based on behaviour and content; rules instruct Bob never to infer or label people by religion, caste, or community.
5. **Mock data:** The demo uses fictional places and groups only.

---

## Scalability Notes

- **Coordination computation:** The toolkit is parallelised and processes millions of posts on one machine for the simpler network types; co-similarity is the most CPU-intensive.
- **Horizontal scaling:** The stateless FastAPI service can be scaled behind a load balancer; long analyses can move to a background job queue.
- **LLM cost control:** The CIB engine acts as a filter — only high-scoring campaigns (not individual posts) are sent to Bob, and results are cached.
