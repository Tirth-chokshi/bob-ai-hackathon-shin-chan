# 🛡️ Social Media Threat Intelligence Engine

> An AI-powered Open Source Intelligence (OSINT) and Coordinated Inauthentic Behavior (CIB) detection engine for Law Enforcement Cyber Cells, powered by **IBM Bob**.

---

## 👥 Team Shin-chan

| Role | Name | Email | Focus Area |
|---|---|---|---|
| **Lead / Forensics** | Tirth Chokshi | chokshitirth4@gmail.com | System Architecture, Coordination Engine & Pipeline |
| **Frontend Engineering** | Milind Pawar | — | React 19 UI, Cytoscape Graph & Interactive Timeline |
| **Bob Layer & MCP** | Jainik Devada | — | IBM Bob Integration, MCP Server, Legal Mapping |
| **Data & Benchmarking** | Jigar Jariwala | — | Scenario Synthesis, Real Data Adapters, Evaluation |

---

## 🎯 Problem Statement

**Problem #06 — Track 2: Cyber Forensics (IBM Bob AI Innovation Hackathon / INNOVAI)**

During sensitive incidents (such as communal tensions or civil protests), coordinated social media botnets and sock-puppet networks rapidly amplify rumours, incite physical violence, and coordinate harassment pile-ons. Current cyber cell workflows rely on manual post-by-post scanning, which fails because **individual posts often appear harmless in isolation** while working in concert to create dangerous offline mobilization.

Officers lack an automated system that detects synchronized coordination topologies, rates campaign risk, maps applicable legal sections under Indian law (**Bharatiya Nyaya Sanhita 2023** and the **Information Technology Act**), and generates tamper-evident briefs compliant with **Section 63 of the Bharatiya Sakshya Adhiniyam (BSA) 2023**.

---

## 💡 The Key Insight: Behaviour First, Content Second

Most conventional AI threat detectors classify posts individually. In contrast, our platform operates on a **two-phase architecture**:

1. **Phase 1 — Behavioral Coordination Detection (Deterministic & Structural):** Ingests posts and constructs a multi-signal coordination network using the QUT Digital Observatory method across 5 signal layers:
   - **Co-Tweet:** Accounts posting identical text within tight time windows (60s).
   - **Co-Similar-Tweet:** Accounts sharing paraphrased/mutated text (Jaccard similarity $\ge 0.8$).
   - **Co-Link:** Accounts sharing identical URLs within the time window.
   - **Co-Reply:** Accounts targeting the same victim handle within minutes.
   - **Co-Retweet:** Accounts amplifying identical sources in parallel.
   
   Identifies suspicious clusters using **NetworkX Louvain community detection** and computes an explainable **CIB Risk Score (0–100)** across 6 forensic features: temporal velocity, lexical duplication, multi-signal fusion, account freshness, burstiness ratio, and entity concentration.

2. **Phase 2 — Threat Synthesis & Legal Intelligence (IBM Bob AI):** **IBM Bob** (`bob run`) investigates each flagged campaign to determine the threat vector (Incitement, Misinformation, Harassment, or Benign Coordination), assesses target entities and physical mobilization risks, and suggests specific statutory sections from our verified Indian Cyber Forensics Legal Table.

---

## 📸 Interface & Workflow Screenshots

| Overview | Network |
|---|---|
| ![Overview](demo/screenshots/02-overview.png) | ![Network](demo/screenshots/03-network.png) |

| IBM Bob assessment (benign decoy) | Threat brief |
|---|---|
| ![IBM Bob assessment of the benign decoy](demo/screenshots/04-bob-assessment.png) | ![Threat Brief](demo/screenshots/05-threat-brief.png) |

*(Full gallery with descriptions available in [`demo/screenshots/README.md`](demo/screenshots/README.md))*

---

## 📊 Evaluation

Every number here comes from `python src/eval/measure.py`; the full output is in [`src/eval/results.md`](src/eval/results.md).

**Synthetic scenario:** 4,658 posts from 956 accounts. It contains three planted threat rings plus a benign decoy (cricket fans posting the same chants at three match moments).

| Ring | Planted | Accounts | Found | Cluster | CIB score | IBM Bob verdict | Escalation |
|---|---|---|---|---|---|---|---|
| **A** | Dam-flood rumour + 7 PM gathering call | 40 | 40 (100%) | `c2` | **89** | `incitement` (severity 5) | **URGENT** |
| **B** | Fake leaked-document links | 25 | 25 (100%) | `c1` | **92** | `organized_misinformation` (4) | **URGENT** |
| **C** | Harassment pile-on against a journalist | 30 | 30 (100%) | `c3` | **88** | `targeted_harassment` (4) | **URGENT** |
| **D** | Decoy: cricket fans chanting | 60 | 60 (100%) | `c4` | **72** | `benign_coordination` (1) | **MONITOR** |

- All four groups are found as separate clusters with no extra accounts, and no other campaigns are reported.
- The decoy *is* coordinated, so it is detected, but it scores lowest. IBM Bob labels it benign, and the rules escalate it only to MONITOR. This is the point of the design: behaviour first, content second.
- The full analysis takes about 18 s on a laptop.

**Real research datasets (no ground truth):**

| Dataset | Analysed | Campaigns found | CIB scores |
|---|---|---|---|
| FiveThirtyEight IRA tweets | 3,313 posts from 44 accounts (busiest 6 hours) | 4 campaigns, 43 accounts (shared links) | 35–37 |
| X/Twitter IO archive sample | 51,410 posts from 6,997 accounts (whole file) | 3 campaigns, 38 accounts (retweets, replies) | 59–62 |

Real campaigns score lower than the planted rings. The weights were set by hand on the synthetic scenario, and the IRA file has no account creation dates or retweet targets.

**IBM Bob cost:** about 0.026 Bobcoins and 10–20 s per classification (measured). Cached verdicts cost nothing.

---

## 🏛️ Indian Legal Framework (BNS 2023 & IT Act)

All statutory suggestions are filtered against our legal reference table (`.bob/rules-osint-analyst/01-legal-table.md`) and clearly marked for legal officer verification:

| Section Code | Law (2024) | Corresponding IPC | Forensic Scope |
|---|---|---|---|
| `BNS-353` | BNS Section 353 | IPC 505 | Statements conducing to public mischief (rumours causing fear or alarm) |
| `BNS-61` | BNS Section 61 | IPC 120A/120B | Criminal conspiracy (coordinated multi-account rings) |
| `BNS-196` | BNS Section 196 | IPC 153A | Promoting enmity between religious or regional groups |
| `BNS-351` | BNS Section 351 | IPC 506 | Criminal intimidation |
| `BNS-356` | BNS Section 356 | IPC 499/500 | Defamation and reputational attacks |
| `BNS-79` | BNS Section 79 | IPC 509 | Word, gesture or act insulting the modesty of a woman |
| `ITA-66D` | IT Act Section 66D | — | Cheating by personation using computer resources (sock puppets) |
| `ITA-69A` | IT Act Section 69A | — | Platform takedown requests through proper government channels |
| `BNSS-163` | BNSS Section 163 | CrPC 144 | Preventive public order directives |
| `BSA-63` | BSA Section 63 | Evidence Act 65B | Electronic record hash certificate (SHA-256 integrity chain) |

*Note: Banned/struck-down sections (e.g. IT Act Section 66A) are strictly blocked.*

---

## 🛠️ Tech Stack & Implementation Details

- **Coordination Detection:** `coordination_network_toolkit` (QUT Digital Observatory, MIT license)
- **Graph Clustering:** `NetworkX` (Louvain community modularity algorithm)
- **Backend Service:** `FastAPI`, `Uvicorn`, `Pydantic v2`, `python-dotenv`
- **Frontend Architecture:** `React 19`, `Vite`, `Tailwind CSS v4`, `Cytoscape.js`, `Lucide Icons`; design language in [`docs/design-system.md`](docs/design-system.md)
- **AI & Reasoning:** `IBM Bob Shell 2.0` (Headless CLI `bob run`, custom mode `osint-analyst`, FastMCP integration server)
- **Storage:** Local SQLite for multi-signal joins, JSON disk runs with SHA-256 tamper-evident logs

---

## ⚡ Quickstart & How to Run

### 1. Prerequisites
- Python 3.10+ and Node.js 24+
- IBM Bob Shell ([bob.ibm.com/download](https://bob.ibm.com/download)); see [`docs/setup-guide.md`](docs/setup-guide.md) for details

### 2. Setup
```bash
git clone https://github.com/Tirth-chokshi/bob-ai-hackathon-shin-chan.git
cd bob-ai-hackathon-shin-chan

# Install Python backend dependencies
python -m pip install -r src/requirements.txt

# Build the React frontend (src/web/dist is not committed)
cd src/web && npm ci && npm run build && cd ../..

# (Optional) Add your IBM Bob API key to src/.env for live classifications
cp src/.env.example src/.env
```

### 3. Launch Application
```bash
python src/main.py
```
Open **http://127.0.0.1:8000** in your browser. The pre-analysed demo dataset loads immediately with the coordination graph, activity timeline, explainable CIB scores and cached IBM Bob verdicts, so it works without an API key.

---

## 🔍 IBM Bob Chat & MCP Investigation Console

Investigate detected campaigns conversationally in Bob Chat:
1. In the repository root, start Bob Chat:
   ```bash
   bob chat
   ```
2. Switch to the OSINT Analyst mode:
   ```
   /mode osint-analyst
   ```
3. Ask investigative questions:
   - *"Which accounts started the dam flooding rumour in campaign c2?"*
   - *"List the top coordinated campaigns in dataset demo sorted by CIB risk."*
   - *"Show the first posts of campaign c3 and tell me which account posted first."*

Bob queries the read-only `threat-intel` FastMCP server (`src/mcp_server/server.py`) and cites post IDs from the analysed data.

---

## ⚖️ Ethics, Safety & Responsible AI

1. **Behavior First, Content Agnostic:** Detection focuses on inauthentic synchronization patterns rather than suppressing political speech.
2. **Strict Non-Profiling Guardrail:** The system enforces `.bob/rules-osint-analyst/03-no-profiling.md`—it never infers or labels religion, caste, community, or political affiliation.
3. **Decision Support, Not Verdicts:** All AI outputs are designated as leads for trained investigating officers and require legal verification before executive action.
