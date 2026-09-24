# 🛡️ Social Media Threat Intelligence Engine

> An AI-powered Open Source Intelligence (OSINT) and Coordinated Inauthentic Behavior (CIB) detection platform tailored for Law Enforcement Cyber Cells, built with IBM Bob and watsonx.ai Granite 3.0.

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | Shin-chan |
| **Track** | AI (Cyber Forensics / Problem Statement 06) |
| **Team Lead** | Tirth Chokshi — chokshitirth4@gmail.com |
| **Members** | Tirth Chokshi (Team Lead & Full-Stack / AI Engineer) |

---

## 🎯 Problem Statement

Coordinated hashtag and messaging campaigns (such as during the 2020 Delhi riots and 2022 communal flare-ups) spread incitement, targeted harassment, and violent misinformation faster than cyber cell officers can manually review. In modern information warfare, malicious actors leverage synchronized botnets and sock-puppet networks across X/Twitter, Telegram, and messaging channels to manipulate public perception and mobilize street violence.

Cyber cells and intelligence branches currently lack automated forensic tools to detect Coordinated Inauthentic Behavior (CIB), extract campaign topologies, and translate fleeting social media chatter into court-admissible, BNS/IPC-mapped evidentiary briefs before offline violence erupts.

---

## 💡 Solution

The **Social Media Threat Intelligence Engine** ingests multi-platform social streams and applies automated statistical and semantic Coordinated Inauthentic Behavior (CIB) detection across account networks. It isolates burst posting velocities, temporal synchronicity clusters, and semantic duplication patterns to identify botnets and astro-turfing operations.

Powered by **watsonx.ai Granite 3.0** and **IBM Bob**, the platform classifies threat severity (Incitement to Violence, Targeted Harassment, Organized Communal Misinformation), maps digital evidence directly to Indian criminal jurisprudence (Bharatiya Nyaya Sanhita 2023, Indian Penal Code, and IT Act 2000), and auto-generates time-stamped, FIR-ready Police Threat Escalation Briefs with actionable tactical intervention steps (e.g., IT Act Section 69A blocking, Section 144 BNSS preventive orders).

---

## ✨ Key Features

- **Multi-Signal CIB Detection Engine:** Detects sub-second burst velocities, temporal clustering, account age anomalies, and semantic text duplication using Jaccard fingerprinting and cosine similarity.
- **watsonx.ai Granite 3.0 Threat Classifier:** Categorizes posts into threat categories (Incitement, Harassment, Misinformation, Benign) with calibrated confidence scoring and threat severity ratings.
- **BNS 2023 & IT Act Statutory Mapping:** Automatically maps detected behavior to actionable penal sections (BNS Sec 196/197/353/79, IPC 153A/153B/505/509, and IT Act Sec 66A/67/69A).
- **IBM Bob MCP Investigation Tools:** Exposes Model Context Protocol (MCP) endpoints for IBM Bob agents to inspect threat clusters, query suspect networks, and trigger automated incident response workflows.
- **Tactical Police Threat Brief Generator:** Exports time-stamped, court-admissible forensic briefs formatted for Senior Police Officers (DCP/SP) and Cyber Cell forensic examiners with 1-click PDF/print-ready documentation.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python 3.10+, JavaScript, HTML5, CSS3 |
| **Frameworks** | FastAPI / Python Standard Library |
| **IBM Technologies** | IBM Bob (AI Coding Partner & MCP Agent), watsonx.ai Granite 3.0, IBM Cloud |
| **Databases & Cache** | In-Memory Graph Index, SQLite, Vector Cache |
| **Other** | GitHub Actions CI/CD |

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

- **Synthetic OSINT Ingestion Feed:** For the purpose of hackathon reproducibility and offline reliability, the application ships with a pre-seeded multi-platform synthetic batch stream simulating Twitter/X, Telegram, and WhatsApp forwards. Live Firehose ingestion requires active social network API keys.
- **Language Localization:** The primary semantic classifier is fine-tuned for English and Hinglish vernacular (the predominant medium for communal disinformation campaigns in India). Regional Dravidian languages are supported via transliteration.
- **Static Legal Jurisdiction:** The statutory mapping engine is calibrated against Indian Federal Law (Bharatiya Nyaya Sanhita 2023, IT Act 2000). Cross-border or international jurisdictions require modular rule additions.

---

## 🏅 What We're Most Proud Of

We are most proud of building a seamless, end-to-end operational pipeline that connects mathematical signal forensics (Coordinated Inauthentic Behavior detection) with the real-world demands of Indian criminal jurisprudence. 

Instead of generating generic "toxic comment" alerts that overwhelm on-call police personnel, the Social Media Threat Intelligence Engine isolates coordinated bot networks and automatically packages the findings into a time-stamped, BNS 2023-compliant Threat Brief. Coupled with native **IBM Bob MCP integration**, law enforcement officers can prompt Bob to conduct deep forensic audits, trace kingpin-mule coordination, and draft actionable Section 69A blocking requests in seconds.
