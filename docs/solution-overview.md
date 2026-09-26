# Solution Overview: Social Media Threat Intelligence Engine

## What We Built

The **Social Media Threat Intelligence Engine** is an open-source intelligence (OSINT) and cyber-investigative tool for law enforcement officers, cyber cells, and digital forensics examiners.

It automates the discovery of **Coordinated Inauthentic Behavior (CIB)** in a batch of social media posts, separates engineered campaigns from organic outrage, classifies the threat (Incitement, Targeted Harassment, Organized Misinformation, or Benign Coordination), and packages the evidence into a time-stamped **Police Threat Escalation Brief** with suggested **Bharatiya Nyaya Sanhita (BNS) 2023** and **Information Technology Act 2000** sections for legal review.

It integrates with **IBM Bob** in two ways: behind the web app, Bob (called headless with our Bob API key) classifies each campaign and writes the brief's executive summary; and through our **Model Context Protocol (MCP)** server an investigating officer can question the data in natural language from Bob chat.

The core idea is **behaviour first, content second**: we first find accounts that act together, then read what they are saying.

---

## How It Works

```
[Post batch: CSV / JSON]
                 │
                 ▼
[Stage 0: Normalize]  common schema: post_id, account_id, created_at, text, repost_of, reply_to, urls, hashtags, account_created_at
                 │
                 ▼
[Stage 1: Coordination Networks]  (QUT coordination-network-toolkit)
   ├── co-tweet / co-similarity   same or near-identical text (Jaccard) within a time window
   ├── co-link                     same URL shared within a time window
   └── co-reply / co-retweet       replying to / reposting the same post within a time window
                 │
                 ▼
[Stage 2: Campaign Discovery]  (NetworkX Louvain community detection on the merged, weighted graph)
                 │
                 ▼
[Stage 3: Explainable CIB Score 0–100]  speed · duplication · multi-signal · account age · burstiness · hashtag/URL concentration
                 │
                 ▼
[Stage 4: IBM Bob Threat Analysis]  threat type · target · severity · real-world call to action · legal suggestions · evidence post IDs
                 │
                 ▼
[Stage 5: Escalation Rules + Police Threat Brief]  MONITOR / ALERT / URGENT · SHA-256 evidence hashes · print-ready
```

### Detailed Operational Steps

1. **Ingestion & Normalization:** Loads a batch of posts and converts it into one common schema, so the rest of the pipeline works the same for synthetic data and research datasets.
2. **Coordination Detection:** For every pair of accounts, counts how often they performed the same action within a short time window (60 seconds by default). A minimum edge weight of 2 filters out one-off coincidences. Output is an account-to-account graph.
3. **Campaign Discovery:** Merges all coordination types into one weighted graph, drops weak edges, and runs community detection. Each community of 5+ accounts becomes a candidate campaign.
4. **Explainable CIB Scoring:** Each campaign gets a 0–100 score from transparent features — median seconds between coordinated posts, share of near-duplicate posts, number of coordination types, median account age, peak posts per minute, and hashtag/URL concentration. Each feature's contribution is stored so the UI can show *why* a campaign was flagged.
5. **IBM Bob Threat Analysis:** For each top campaign, the backend runs IBM Bob headless (`bob run --format json`, authenticated with our Bob API key, prompt sent through stdin) with the campaign statistics, ~10 representative posts, and our rule files (legal table, escalation rules, no-profiling rule). Bob returns structured JSON:
     - `INCITEMENT`: calls for mobilization, violence, or arson.
     - `ORGANIZED_MISINFORMATION`: fabricated claims pushed by the network.
     - `TARGETED_HARASSMENT`: coordinated abuse of a person or group.
     - `BENIGN_COORDINATION`: fan clubs, news sharing, organic protest organizing — coordination that is not a threat.

   Every post ID Bob cites is checked in code against the campaign; output that fails validation twice is rejected with an error; nothing is guessed or cached. Results are cached, so each campaign is analysed once.
6. **Legal Suggestions (for verification):** Bob may only choose from a fixed, checked table of sections, by ID; any other section is dropped in code. In testing, free-form answers included over-serious or misdescribed sections, which is why the table is fixed.
     - **BNS 196 (IPC 153A):** Promoting enmity between groups.
     - **BNS 197 (IPC 153B):** Imputations prejudicial to national integration.
     - **BNS 351 (IPC 506):** Criminal intimidation.
     - **BNS 353 (IPC 505):** Statements conducing to public mischief.
     - **BNS 356 (IPC 499/500):** Defamation.
     - **BNS 79 (IPC 509):** Insulting the modesty of a woman.
     - **BNS 61 (IPC 120A/B):** Criminal conspiracy.
     - **IT Act 66D:** Cheating by personation using a computer resource (impersonation accounts).
     - **IT Act 67:** Publishing obscene material in electronic form.

   Procedural references used in escalation and the brief (not offences): **IT Act 69A** (blocking, Central Government power), **BNSS 163** (preventive orders), **BSA 63** (electronic-record certificate).
7. **Escalation & Brief:** Deterministic rules set the escalation level (e.g., incitement plus a real-world call to action → URGENT). The engine renders a time-stamped brief for the SHO / District Cyber Cell with the timeline, campaign table, evidence list with SHA-256 hashes, legal suggestions, recommended actions, and limitations. Bob writes only the executive summary; every other section is filled from stored, verified data.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Behaviour-first detection** | Per-post toxicity classifiers miss campaigns where each post looks harmless. Coordination between accounts is the defining signal of CIB. |
| **Published coordination methods** | We build on the QUT Digital Observatory toolkit, which implements coordination-network methods from peer-reviewed research, instead of inventing thresholds from scratch. |
| **Multi-signal, explainable score** | Single metrics (like post count) give false positives during breaking news. Combining signals — and showing each one — lets an officer check the reasoning. |
| **Benign coordination as a class** | Fan groups and news sharing also coordinate. Explicitly recognising them reduces false alarms. |
| **Bob for semantics, rules for escalation** | Bob handles language understanding; escalation levels come from fixed rules so the decision is predictable and auditable. |
| **Fixed legal table, validated in code** | Keeps legal suggestions within sections we have checked; one Markdown file is used by Bob chat, embedded in `bob run` prompts, and parsed by the validator. |
| **Official `bob run` path** | Documented, works with an API key, and cheap (~0.025 Bobcoins and ~11 s per campaign in our test). Prompts go through stdin, which is reliable on Windows. |
| **Dual BNS 2023 & IPC references** | BNS replaced the IPC in July 2024; officers and prosecutors still cross-reference both. |
| **Cached Bob results** | Classifications are cached per campaign, so re-opening a case costs nothing and the demo works offline once analysed. |

---

## IBM Technologies Used

### IBM Bob — where it is used

| # | Where | How | Credential |
|---|---|---|---|
| 1 | **Campaign threat analysis** | Backend runs `bob run --format json` (prompt via stdin) for each flagged campaign; output validated, cached | Bob API key (`BOB_API_KEY` in `src/.env`) |
| 2 | **Brief executive summary** | One `bob run` call per brief | Bob API key |
| 3 | **MCP investigation console** | Officer runs `bob chat` in the repo; Bob calls our read-only MCP tools (`list_campaigns`, `get_campaign`, `get_posts`, `timeline`, `account_profile`) and answers with cited post IDs | IBMid sign-in |
| 4 | **Repo configuration** | `.bob/` holds the `osint-analyst` mode, rules (legal table, escalation matrix, no-profiling), the `threat-brief` skill, and `mcp.json` | — |
| 5 | **AI coding partner** | Bob Plan → Agent mode used to plan and build the project | IBMid sign-in |

Example console question: *"Which accounts started the rumour in campaign 2, and how fast did it spread?"*

No other AI service or API is used — no watsonx, no social media APIs, no cloud accounts.
