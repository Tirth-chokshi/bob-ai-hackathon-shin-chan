# 🛡️ Social Media Threat Intelligence Engine

> An AI-powered Open Source Intelligence (OSINT) and Coordinated Inauthentic Behavior (CIB) detection platform tailored for Law Enforcement Cyber Cells, powered by IBM Bob.

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | Shin-chan |
| **Track** | AI (Cyber Forensics / Problem Statement 06) |
| **Team Lead** | Tirth Chokshi — chokshitirth4@gmail.com |
| **Members** |  |

---

## 🎯 Problem Statement

Coordinated hashtag and messaging campaigns (such as during the 2020 Delhi riots and 2022 communal flare-ups) spread incitement, targeted harassment, and violent misinformation faster than cyber cell officers can manually review. In modern information warfare, malicious actors leverage synchronized botnets and sock-puppet networks across X/Twitter, Telegram, and messaging channels to manipulate public perception and mobilize street violence.

Cyber cells and intelligence branches currently lack automated forensic tools to detect Coordinated Inauthentic Behavior (CIB), extract campaign topologies, and translate fleeting social media chatter into evidence-ready, BNS/IPC-mapped briefs before offline violence erupts.

---

## 💡 Solution

The **Social Media Threat Intelligence Engine** ingests a batch of social media posts and looks at **behaviour first, content second**. It finds groups of accounts that post the same or near-identical text, share the same links, or reply to the same post within seconds of each other (co-tweet, co-similarity, co-link, co-reply and co-retweet networks), groups them into campaigns, and gives each campaign an explainable CIB score.

**IBM Bob** then reads each flagged campaign's posts and classifies the threat (Incitement, Targeted Harassment, Organized Misinformation, or Benign Coordination), suggests relevant sections of the Bharatiya Nyaya Sanhita 2023 and IT Act 2000 for legal review, and drafts a time-stamped Police Threat Escalation Brief with recommended actions (e.g., takedown request, preventive orders under Section 163 BNSS, public fact-check).

---

## ✨ Key Features

- **Multi-Signal CIB Detection Engine:** Builds coordination networks (co-tweet, co-similarity, co-link, co-reply, co-retweet) within short time windows, finds campaigns with community detection, and scores them on speed, duplication, account age and burstiness — with a "why flagged" breakdown for every score.
- **IBM Bob Threat Classifier:** Bob classifies each campaign (Incitement, Harassment, Misinformation, Benign Coordination), rates severity, and cites the exact post IDs it relied on; citations are checked in code.
- **BNS 2023 & IT Act Legal Suggestions:** Suggests relevant sections (BNS 196/197/351/353/356/79, with IPC equivalents 153A/153B/506/505/499/509, and IT Act 66D/67/69A) — clearly marked for legal verification.
- **IBM Bob MCP Investigation Console:** Our MCP server lets an officer ask Bob questions like "who started this rumour?" and Bob pulls campaigns, posts and timelines itself.
- **Police Threat Brief Generator:** Time-stamped, print-ready escalation brief with SHA-256 hashes of the input batch and every evidence post for integrity.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python 3.10+, JavaScript, HTML5, CSS3 |
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **Analysis** | [coordination-network-toolkit](https://github.com/QUT-Digital-Observatory/coordination-network-toolkit) (QUT Digital Observatory, MIT), NetworkX |
| **Frontend** | Vanilla HTML/CSS/JS, Cytoscape.js (network graph), Chart.js (timeline) |
| **IBM Technologies** | IBM Bob (threat classifier via `bob run`, MCP investigation console, custom mode & skills, AI coding partner) |
| **Database** | SQLite |
| **Other** | GitHub Actions |

---

## 📁 Repository Structure

```
├── src/                               # All source code
│   ├── main.py                        # Application entrypoint
│   ├── requirements.txt               # Dependencies
│   ├── .env.example                   # Environment variable template
│   └── README.md                      # Source documentation
├── docs/                              # Written project documentation
│   ├── problem-statement.md           # Problem analysis & context
│   ├── solution-overview.md           # Operational mechanics & IBM tech
│   ├── architecture.md                # System diagrams & architecture
│   └── setup-guide.md                 # Setup & execution instructions
├── demo/                              # Demo artifacts
│   ├── screenshots/                   # Application screenshots
│   │   └── README.md
│   ├── demo-video-link.txt            # Link to demo video walkthrough
│   └── live-demo-url.txt              # Live deployment or local execution status
├── presentation/                      # Pitch presentation slides
│   └── README.md
├── submission.yaml                    # Structured hackathon evaluation metadata
└── .github/workflows/validate.yml     # Automated submission validator workflow
```

---

## ⚡ How to Run

> Follow the steps below or see [`docs/setup-guide.md`](docs/setup-guide.md) for full details.

```bash
# 1. Clone the repository
git clone https://github.com/Tirth-chokshi/bob-ai-hackathon-shin-chan.git
cd bob-ai-hackathon-shin-chan

# 2. Configure environment
cp src/.env.example src/.env

# 3. Install dependencies
pip install -r src/requirements.txt

# 4. Run the project
python src/main.py
```

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/](presentation/) |

---

## ⚠️ Known Limitations

- **Mock and research data only:** The demo uses a synthetic post batch with planted campaigns (fictional places and groups) plus public research datasets. No live platform ingestion — that needs platform API access.
- **Decision support, not a verdict:** Scores and Bob's classifications are leads for a trained officer. Legal sections are suggestions that must be verified by a legal officer.
- **Language coverage:** Coordination detection is language-independent; threat classification quality on Hindi/Hinglish and regional languages has not been formally evaluated yet.
- **Heuristic scoring:** CIB score weights are hand-set, not trained on labelled data.

---

## 🏅 What We're Most Proud Of

We are most proud of building a seamless, end-to-end operational pipeline that connects mathematical signal forensics (Coordinated Inauthentic Behavior detection) with the real-world demands of Indian criminal jurisprudence. 

Instead of generating generic "toxic comment" alerts that overwhelm on-call police personnel, the Social Media Threat Intelligence Engine isolates coordinated account networks — catching campaigns even when each individual post looks harmless — and packages the findings into a time-stamped, BNS-mapped Threat Brief. With **IBM Bob MCP integration**, officers can ask Bob to trace which accounts started a campaign and draft the escalation brief.
