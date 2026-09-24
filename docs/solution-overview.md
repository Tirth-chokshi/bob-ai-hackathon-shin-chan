# Solution Overview: Social Media Threat Intelligence Engine

## What We Built

The **Social Media Threat Intelligence Engine** is an open-source intelligence (OSINT) and cyber-investigative tool for law enforcement officers, cyber cells, and digital forensics examiners.

It automates the discovery of **Coordinated Inauthentic Behavior (CIB)** in a batch of social media posts, separates engineered campaigns from organic outrage, classifies the threat (Incitement, Targeted Harassment, Organized Misinformation, or Benign Coordination), and packages the evidence into a time-stamped **Police Threat Escalation Brief** with suggested **Bharatiya Nyaya Sanhita (BNS) 2023** and **Information Technology Act 2000** sections for legal review.

It integrates with **IBM Bob** in two ways: Bob is the threat classifier and brief writer behind the web app, and through our **Model Context Protocol (MCP)** server an investigating officer can question the data in natural language from Bob chat.

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
5. **IBM Bob Threat Analysis:** For each top campaign, the backend sends Bob the campaign statistics and representative posts. Bob returns structured JSON:
     - `INCITEMENT`: calls for mobilization, violence, or arson.
     - `ORGANIZED_MISINFORMATION`: fabricated claims pushed by the network.
     - `TARGETED_HARASSMENT`: coordinated abuse of a person or group.
     - `BENIGN_COORDINATION`: fan clubs, news sharing, organic protest organizing — coordination that is not a threat.

   Every post ID Bob cites is checked in code against the campaign; unverified output is flagged.
6. **Legal Suggestions (for verification):**
     - **BNS 196 (IPC 153A):** Promoting enmity between groups.
     - **BNS 197 (IPC 153B):** Imputations prejudicial to national integration.
     - **BNS 351 (IPC 506):** Criminal intimidation.
     - **BNS 353 (IPC 505):** Statements conducing to public mischief.
     - **BNS 356 (IPC 499):** Defamation.
     - **BNS 79 (IPC 509):** Insulting the modesty of a woman.
     - **IT Act 66D:** Cheating by personation using a computer resource (impersonation accounts).
     - **IT Act 69A:** Blocking of public access to information in the interest of public order.
7. **Escalation & Brief:** Deterministic rules set the escalation level (e.g., incitement plus a real-world call to action → URGENT), Bob explains it, and the engine renders a time-stamped brief for the SHO / District Cyber Cell with the timeline, campaign table, evidence list with SHA-256 hashes, legal suggestions, recommended actions, and limitations.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Behaviour-first detection** | Per-post toxicity classifiers miss campaigns where each post looks harmless. Coordination between accounts is the defining signal of CIB. |
| **Published coordination methods** | We build on the QUT Digital Observatory toolkit, which implements coordination-network methods from peer-reviewed research, instead of inventing thresholds from scratch. |
| **Multi-signal, explainable score** | Single metrics (like post count) give false positives during breaking news. Combining signals — and showing each one — lets an officer check the reasoning. |
| **Benign coordination as a class** | Fan groups and news sharing also coordinate. Explicitly recognising them reduces false alarms. |
| **Bob for semantics, rules for escalation** | Bob handles language understanding; escalation levels come from fixed rules so the decision is predictable and auditable. |
| **Dual BNS 2023 & IPC references** | BNS replaced the IPC in July 2024; officers and prosecutors still cross-reference both. |
| **Cached Bob results** | Classifications are cached per campaign, so re-opening a case costs nothing and the demo works offline once analysed. |

---

## IBM Technologies Used

### IBM Bob
- **Threat classifier and brief writer:** The backend calls Bob headless (`bob run --format json`) with our custom `osint-analyst` mode to classify campaigns and draft briefs.
- **MCP investigation console:** Our MCP server exposes tools such as `list_campaigns`, `get_campaign`, `get_posts`, and `timeline`. An officer chatting with Bob can ask *"Which accounts started the rumour in campaign 2?"* and Bob gathers the evidence itself.
- **Custom mode, rules and skills:** The repository's `.bob/` folder holds the `osint-analyst` mode, rules (legal reference table, escalation matrix, no-profiling rule), and a `threat-brief` skill.
- **AI coding partner:** Bob was used to plan and build the project.
