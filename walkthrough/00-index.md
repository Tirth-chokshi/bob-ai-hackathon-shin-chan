All done. Here's the full breakdown:

---

## What This Project Does

This is a **Social Media Threat Intelligence Engine** — an AI-powered OSINT platform for Indian police cyber cells. It detects coordinated inauthentic behavior (CIB) on social media — bot rings, sock-puppet networks — and generates legally-compliant escalation briefs under Indian law (BNS 2023, IT Act, BSA Section 63).

It works in two phases:
1. **Phase 1 (Deterministic):** Ingests raw posts → builds a 5-signal coordination graph → runs Louvain community detection → scores each cluster 0–100 using 6 forensic features (speed, duplication, multi-signal, fresh accounts, burst, entity concentration)
2. **Phase 2 (IBM Bob AI):** Sends each flagged cluster to `bob run` (headless) → gets back a threat type, severity, narrative, legal sections, and offline CTA flag → determines URGENT/ALERT/MONITOR escalation level → renders a print-ready HTML brief with SHA-256 evidence hashes

---

## Walkthrough Created: `walkthrough/` folder

| File | Contents |
|---|---|
| [`walkthrough/README.md`](walkthrough/README.md) | Index + quickstart |
| [`walkthrough/01-overview.md`](walkthrough/01-overview.md) | Full architecture, data flow diagram, directory map |
| [`walkthrough/02-backend.md`](walkthrough/02-backend.md) | Every Python module explained: API routes, pipeline, scoring, Bob client, escalation, brief renderer |
| [`walkthrough/03-frontend.md`](walkthrough/03-frontend.md) | All React components, state variables, API client, tab routing |
| [`walkthrough/04-hardcoded-values.md`](walkthrough/04-hardcoded-values.md) | **All 7 hardcoded values with exact file/line, why they exist, and the fix for each** |
| [`walkthrough/05-how-to-add-data.md`](walkthrough/05-how-to-add-data.md) | Step-by-step guide for new CSV datasets via UI, curl, or Python |

---

## The 7 Hardcoded Values in the Frontend (Quick Reference)

| # | File | Line | Value | What breaks |
|---|---|---|---|---|
| 1 | [`App.jsx`](src/web/src/App.jsx:166) | 166–169 | Campaign objects (ids, sizes, hashtags) | Wrong campaigns for any non-demo dataset |
| 2 | [`App.jsx`](src/web/src/App.jsx:171) | 171 | `4538` posts, `956` accounts | Wrong stat tile counts momentarily |
| 3 | [`App.jsx`](src/web/src/App.jsx:173) | 173 | `92` (max score fallback) | Wrong score when no campaigns loaded |
| 4 | [`api.js`](src/web/src/api.js:26) | 26 | `'/datasets/demo'` | Uploaded datasets don't appear in the list |
| 5 | [`NetworkGraph.jsx`](src/web/src/components/NetworkGraph.jsx:194) | 194–211 | Legend labels (Link Ring, Rumour Ring, etc.) | Wrong names for any other dataset |
| 6 | [`NetworkGraph.jsx`](src/web/src/components/NetworkGraph.jsx:5) | 5–11 | Color map only covers c1–c5 | 6+ campaign datasets get same color |
| 7 | [`App.jsx`](src/web/src/App.jsx:70) | 70–77 | `'c1'` hardcoded auto-selection | Minor — works since engine always names top campaign c1 |

The most impactful fix is **#1 + #4**: adding a `GET /api/datasets` endpoint and a `GET /api/datasets/:id/campaigns` endpoint to the backend so the frontend can populate itself dynamically without any fallback objects.