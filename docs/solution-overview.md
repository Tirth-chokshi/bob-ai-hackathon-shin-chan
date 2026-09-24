# Solution Overview: Social Media Threat Intelligence Engine

## What We Built

The **Social Media Threat Intelligence Engine** is a specialized, open-source intelligence (OSINT) and cyber-investigative system built specifically for law enforcement officers, cyber intelligence cells, and digital forensics examiners.

The engine automates the discovery of **Coordinated Inauthentic Behavior (CIB)** in high-velocity social streams, determines whether trending topics represent genuine citizen sentiment or an orchestrated astroturfing campaign, classifies the criminal threat profile (Incitement to Violence, Targeted Harassment, Organized Communal Disinformation), and automatically formats the evidence into a time-stamped **Police Threat Escalation Brief** aligned with the **Bharatiya Nyaya Sanhita (BNS) 2023** and **Information Technology Act 2000**.

Furthermore, it integrates natively with **IBM Bob** through the **Model Context Protocol (MCP)**, allowing an investigating officer to ask natural-language questions, trigger automated forensic audits, and execute incident runbooks directly within their workspace.

---

## How It Works

The platform operates through a 5-stage automated pipeline:

```
[Social Media Stream / Ingestion API]
                 │
                 ▼
[Stage 1: Multi-Signal CIB Forensic Engine]
   ├── Temporal Burst Synchronicity Analysis (Δt < 120s)
   ├── Lexical & Semantic Near-Duplicate Fingerprinting (Jaccard + Cosine)
   └── Account Anomaly & Bot Score Heuristics
                 │
                 ▼
[Stage 2: watsonx.ai Granite 3.0 Threat Classifier]
   ├── Zero-shot & Few-shot Criminal Threat Categorization
   ├── Threat Severity Rating (Critical / High / Medium / Low)
   └── Intent & Target Entity Extraction
                 │
                 ▼
[Stage 3: Indian Statutory Legal Mapping Engine]
   ├── BNS 2023 (Sec 196, 197, 353, 79)
   ├── IPC (Sec 153A, 153B, 505, 509)
   └── IT Act 2000 (Sec 66A, 67, 69A Emergency Blocking)
                 │
                 ▼
[Stage 4: IBM Bob MCP Server & AI Agent Interface]
   ├── Natural Language Codebase & Incident Querying
   ├── Automated Runbook Execution (e.g. hash preservation, IP trace request)
   └── Subagent-driven Evidence Compilation
                 │
                 ▼
[Stage 5: Police Command Dashboard & Evidentiary Brief]
   ├── Live Stream & CIB Coordination Radar
   ├── Account Network Graph Visualization
   └── Time-stamped, Court-Admissible Police Threat Brief Export (PDF/Print)
```

### Detailed Operational Steps

1. **Stream Ingestion & Normalization:** Ingests batches of social posts (Twitter/X, Telegram messages, public group forwards). Cleanses text, standardizes timestamps, extracts user metadata, handles, and hashtags.
2. **Coordinated Inauthentic Behavior (CIB) Detection:**
   - Computes **temporal synchronicity**: flags sudden surges where multiple distinct handles post identical or near-identical messages within short time windows (e.g., 50+ posts in 2 minutes).
   - Computes **semantic duplicate clustering**: uses n-gram Jaccard similarity and MinHash-style token overlapping to group sock-puppets spreading the same narrative with minor punctuation changes.
   - Evaluates **account metadata flags**: newly created accounts, generic alphanumeric handles, default avatar indicators, and abnormal posting cadence.
3. **Semantic Threat Classification via watsonx.ai Granite 3.0:**
   - Evaluates the cluster's messaging content against criminal offense taxonomies:
     - `INCITEMENT_TO_VIOLENCE`: Direct calls for street mobilization, rioting, weapons, or arson.
     - `COMMUNAL_MISINFORMATION`: Fabrication of inter-faith atrocities or desecration claims.
     - `TARGETED_HARASSMENT`: Doxxing, targeted online abuse of public servants or private citizens.
     - `BENIGN_ORGANIC`: Legitimate political discourse, news reporting, or citizen feedback.
4. **Statutory Penal Mapping (BNS 2023 & IT Act):**
   - Correlates the classified offense and evidence with actionable statutory sections:
     - **BNS Sec 196 (IPC 153A):** Promoting enmity between different groups on grounds of religion, race, place of birth, residence, language, etc.
     - **BNS Sec 197 (IPC 153B):** Imputations and assertions prejudicial to national integration.
     - **BNS Sec 353 (IPC 505):** Statements conducing to public mischief, especially with intent to incite riot.
     - **IT Act Sec 69A:** Directions for blocking public access to information through any computer resource in the interest of public order.
5. **Incident Packaging & Police Threat Brief Generation:**
   - Generates a formal, time-stamped **Threat Brief** ready for presentation to the Station House Officer (SHO) and District Cyber Cell incharge, complete with actionable escalation steps (e.g., recommend Sec 69A intermediary blocking notice, deploy anti-riot beat patrols to specific geolocations, issue fact-check rejoinder).

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **FastAPI Backend + Modular Architecture** | Provides sub-millisecond asynchronous JSON request processing, native OpenAPI documentation, and effortless integration with machine learning pipelines. |
| **Multi-Signal CIB Scoring over Single-Metric Thresholds** | Single metrics (like post count) yield false positives during breaking news events. Combining temporal velocity, text duplication, and account age flags ensures high precision. |
| **Dual BNS 2023 & IPC Cross-Mapping** | India enacted the Bharatiya Nyaya Sanhita (BNS) in 2023 (effective July 2024) to replace the IPC. Police officers and prosecutors are actively transitioning; providing both statutory references is essential for legal validity. |
| **Model Context Protocol (MCP) for IBM Bob** | Implementing an MCP server enables IBM Bob to directly act as an AI cyber forensic assistant, allowing officers to interrogate data and execute runbooks via natural language inside their IDE/environment. |
| **Zero-Dependency Lightweight Fallback Engine** | Ensures that even in offline field environments or if cloud API credentials are temporarily restricted, the platform remains fully functional and reliable for evaluators and officers. |

---

## IBM Technologies Used

### 1. IBM Bob (AI SDLC Partner & MCP Agent)
- **Codebase Development & Architecture:** IBM Bob guided the architecture, refactoring, and test suite implementation of the threat intelligence engine.
- **Model Context Protocol (MCP) Integration:** Bob connects directly to our custom MCP server (`src/backend/bob_mcp.py`), exposing tools such as `analyze_threat_batch`, `generate_police_brief`, and `query_suspect_network`. An investigator chatting with Bob can ask: *"Bob, run a CIB scan on the latest batch and draft a Section 69A blocking brief for the SHO."*

### 2. watsonx.ai Granite 3.0
- **Granite 3.0 8B Instruct:** Employed for nuanced zero-shot semantic threat classification and intent extraction. Granite 3.0 provides superior reasoning capabilities on multilingual and code-mixed vernacular (such as Hinglish) commonly found in Indian social media discourse.
- **Structured JSON Generation:** Granite outputs structured forensic JSON containing threat severity, targeted groups, detected mobilization rhetoric, and confidence levels.
