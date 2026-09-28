# 🛡️ Social Media Threat Intelligence Engine

> An AI-powered Open Source Intelligence (OSINT) and Coordinated Inauthentic Behavior (CIB) detection engine for Law Enforcement Cyber Cells, powered by **IBM Bob**.

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | Shin-chan |
| **Track** | AI (Track 2: Cyber Forensics) |
| **Team Lead** | Tirth Chokshi — [chokshitirth4@gmail.com](mailto:chokshitirth4@gmail.com) |
| **Members** | Tirth Chokshi, Milind Pawar, Jainik Devada, Jigar Jariwala |

### Team Roles & Focus Areas
| Member | Role | Focus Area |
|---|---|---|
| **Tirth Chokshi** | Team Lead & Forensics Architect | System Architecture, Coordination Engine & Pipeline |
| **Milind Pawar** | Frontend Engineering Lead | React 19 UI, Cytoscape Graph & Interactive Timeline |
| **Jainik Devada** | Bob Layer & MCP Engineer | IBM Bob Integration, MCP Server, Legal Mapping |
| **Jigar Jariwala** | Data & Evaluation Engineer | Scenario Synthesis, Real Data Adapters, Evaluation |

---

## 🎯 Problem Statement

> In 2–3 sentences: What problem does your project solve? Who experiences this problem?

During sensitive public flashpoints (such as communal tensions, civil protests, or disaster events), coordinated botnets and sock-puppet networks rapidly amplify inflammatory rumors, incite physical violence, and coordinate harassment pile-ons faster than State Police Cyber Cells can manually review. Individual posts often appear harmless in isolation while working in locked synchrony to spark dangerous offline mobilization. Cyber patrol officers and Station House Officers (SHOs) lack automated tools to detect coordinated inauthentic behavior (CIB) topologies and translate digital signals into court-admissible, BNS 2023-mapped evidentiary briefs before offline violence erupts.

---

## 💡 Solution

> In 2–3 sentences: What did you build? How does it solve the problem above?

We built the **Social Media Threat Intelligence Engine**, an automated OSINT and cyber-forensics platform that prioritizes *behavior first, content second*. It ingests raw X API v2 data, builds multi-signal coordination networks across 60-second sliding windows, and applies Louvain community clustering with an explainable 0–100 CIB risk score. It then leverages **IBM Bob** to classify threat severity, extract planned physical gathering coordinates (what, where, when), map offenses to the **Bharatiya Nyaya Sanhita (BNS) 2023** and **IT Act 2000**, and generate print-ready Section 63 BSA legal escalation briefs with SHA-256 cryptographic chain of custody.

---

## ✨ Key Features

- **Behavior-First CIB Detection:** Detects coordinated inauthentic behavior across 5 orthogonal networks (co-tweet, co-similarity, co-link, co-retweet, co-reply) within configurable 60-second windows using the QUT coordination-network-toolkit and Louvain community detection.
- **Offline Threat & Early Warning Extraction:** IBM Bob extracts physical gathering locations and timings directly quoted from posts, calculating the critical lead time between digital coordination and planned offline assembly.
- **X API v2 Native Relational Normalization:** Ingests native X API v2 JSON (search, user timelines, filtered stream), stores it in a per-dataset SQLite relational schema (`x.db`), and provides forensic exploration of posts, quotes, and threads.
- **Statutory Indian Legal Mapping:** Automatically suggests validated legal sections from a strict BNS 2023 (Sections 196, 197, 351, 353, 356, 79) and IT Act 2000 (Sections 66D, 69A) reference table for legal officer review.
- **Section 63 BSA Court-Admissible Dossier:** Generates time-stamped, print-ready Police Threat Escalation Briefs with SHA-256 cryptographic hashes of the entire dataset and every cited evidence post for judicial scrutiny.
- **Conversational Investigation via IBM Bob MCP:** Features a dedicated Model Context Protocol (FastMCP) server allowing duty officers to investigate campaigns conversationally directly inside Bob Chat.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python 3.10+, JavaScript (ES2024) |
| **Frameworks** | FastAPI, Uvicorn, Pydantic v2, React 19, Vite |
| **IBM Technologies** | IBM Bob Shell (Headless `bob run`), IBM Bob Model Context Protocol (MCP) |
| **Databases** | SQLite (Embedded per-dataset relational store `x.db`) |
| **Forensics & Graph** | coordination-network-toolkit (QUT), NetworkX (Louvain Community Modularity), Cytoscape.js |
| **Styling & UI** | Tailwind CSS v4, Lucide React, IBM Plex Sans & IBM Plex Mono |
| **Other** | Docker, GitHub Actions (`validate.yml`), pytest |

---

## 📁 Repository Structure

```
├── src/                  # All source code
│   ├── api/              # FastAPI REST endpoints & background analysis jobs
│   ├── bob/              # IBM Bob headless client, prompt builder & legal table parser
│   ├── brief/            # Section 63 BSA-compliant printable HTML/PDF threat brief renderer
│   ├── engine/           # CIB detection, Louvain clustering, CIB scoring & xstore
│   ├── mcp_server/       # FastMCP server for conversational Bob Chat investigation
│   ├── web/              # React 19 + Vite + Tailwind CSS frontend
│   ├── tests/            # Automated test suite (31 tests passing)
│   ├── .env.example      # Environment variable template
│   └── README.md         # Source code architecture documentation
├── docs/                 # Comprehensive documentation
│   ├── problem-statement.md   # Problem background, affected users, and urgency
│   ├── solution-overview.md   # System concepts, pipeline stages, and operational flow
│   ├── architecture.md        # Technical architecture, Mermaid diagrams, and data flow
│   ├── setup-guide.md         # Exact reproduction instructions and environment details
│   ├── design-system.md       # "Case File" UI design language and color tokens
│   └── data-model.md          # X API v2 relational database schema
├── demo/                 # Demo artifacts
│   ├── demo-video-link.txt    # URL to walkthrough demo video
│   ├── live-demo-url.txt      # Live deployment URL / local reproduction status
│   └── screenshots/           # Application screenshots gallery (01 to 06)
├── presentation/         # Hackathon pitch presentation
│   ├── slides.pdf             # Slide deck in PDF format
│   └── slides.pptx            # Editable presentation deck
├── submission.yaml       # Structured submission metadata (validated by CI)
└── README.md             # Human-readable project overview
```

---

## ⚡ How to Run

> **Copy these exact steps from our [`docs/setup-guide.md`](docs/setup-guide.md)**

### 1. Prerequisites
- Python 3.10+ and Node.js 24+
- IBM Bob Shell ([bob.ibm.com/download](https://bob.ibm.com/download)); run `bob` once to authenticate with IBMid

### 2. Setup
```bash
# 1. Clone the repo
git clone https://github.com/Tirth-chokshi/bob-ai-hackathon-shin-chan.git
cd bob-ai-hackathon-shin-chan

# 2. Install dependencies
python -m pip install -r src/requirements.txt
cd src/web && npm ci && npm run build && cd ../..

# 3. Configure environment
cp src/.env.example src/.env
# Edit src/.env with your BOB_API_KEY (optional for pre-assessed cached datasets)

# 4. Run the project
python src/main.py
```

Open **http://127.0.0.1:8000** in your browser. On the **Datasets** page, upload X API v2 JSON (`.json` / `.jsonl`) or search X, and analysis executes automatically.

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 **Demo Video** | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 **Live Demo** | [See demo/live-demo-url.txt](demo/live-demo-url.txt) (Local: http://localhost:8000) |
| 🖼️ **Screenshots** | [See demo/screenshots/](demo/screenshots/) |
| 📊 **Presentation** | [See presentation/slides.pdf](presentation/slides.pdf) |

---

## ⚠️ Known Limitations

> Transparent disclosure of project scope, boundaries, and evaluation considerations:

- **Input Format Scope:** The engine currently ingests X API v2 JSON format (`.json`/`.jsonl`). Ingestion adapters for Telegram export JSON and WhatsApp export text are architecturally mapped in `docs/data-format.md` but not yet integrated into the live UI.
- **Evaluation on Ground-Truth Public Archives:** Public Indian communal flare-up archives do not provide pre-existing ground-truth campaign labels, and text-only benchmark datasets (e.g. CONSTRAINT-2021) lack user IDs and microsecond timestamps required for temporal coordination forensics.
- **Live X Search Access:** Live querying through Datasets → Search X requires a paid X API developer bearer token (`X_BEARER_TOKEN`). For evaluation without an X API token, file uploads of X API v2 JSON work completely offline with zero external credentials.
- **Human-in-the-Loop Safeguard:** CIB scores and IBM Bob legal classifications serve as investigator decision-support leads. All suggested BNS 2023 / IT Act sections require formal confirmation by a certified police legal advisor before filing an FIR.

---

## 🏅 What We're Most Proud Of

- **Behavior-First Forensic Topology:** Flagging coordinated syndicates that act in lockstep within seconds, uncovering operations even when individual messages appear completely innocuous.
- **Bridging AI Signals to Statutory Law:** Translating raw social media telemetry directly into court-admissible, BNS 2023-mapped Station House Officer intelligence briefs with Section 63 BSA cryptographic integrity verification.
- **Real-World Case Study Verification:** Successfully validating the pipeline against actual 2020 Delhi Riots forensic data (uncovering the Bulandshahr recycled video disinformation campaign and bot amplification network).

---

## 📸 Interface & Workflow Screenshots

| Overview: threat, timeline, spread | Network: who coordinated with whom |
|---|---|
| ![Overview](demo/screenshots/02-overview.png) | ![Network](demo/screenshots/03-network.png) |

| IBM Bob assessment and spread detail | Threat brief |
|---|---|
| ![IBM Bob assessment](demo/screenshots/04-bob-assessment.png) | ![Threat Brief](demo/screenshots/05-threat-brief.png) |

*(Full gallery in [`demo/screenshots/README.md`](demo/screenshots/README.md).)*

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

*Note: Banned or struck-down sections (e.g. IT Act Section 66A) are strictly blocked.*

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
   - *"List my datasets and the campaigns in the newest one."*
   - *"Which accounts started campaign c1, on which platform, and does any campaign call a gathering?"*
   - *"Show the first posts of campaign c3 and tell me which account posted first."*

Bob queries the read-only `threat-intel` FastMCP server (`src/mcp_server/server.py`) and cites post IDs from the analysed data.

---

## ⚖️ Ethics, Safety & Responsible AI

1. **Behavior First, Content Agnostic:** Detection focuses on inauthentic synchronization patterns rather than suppressing political speech.
2. **Strict Non-Profiling Guardrail:** The system enforces `.bob/rules-osint-analyst/03-no-profiling.md`—it never infers or labels religion, caste, community, or political affiliation.
3. **Decision Support, Not Verdicts:** All AI outputs are designated as leads for trained investigating officers and require legal verification before executive action.
