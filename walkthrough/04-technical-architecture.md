# Technical Architecture Walkthrough

## End-to-End Flow

```text
CSV / JSON / WhatsApp / Telegram upload  (or one post at a time: stream API)
        |
        v
Normalization into Post records
        |
        v
Five coordination networks
        |
        v
Merged account graph
        |
        v
Louvain campaign discovery
        |
        v
Explainable CIB score: 0-100 + spread profile (seeds, amplifiers, platform/town paths, detection time)
        |
        v
IBM Bob threat classification
        |
        v
Validation and deterministic escalation
        |
        v
Time-stamped HTML threat brief
```

## 1. Ingestion and Normalization

Primary code: `src/engine/normalize.py`

The loader accepts CSV and JSON files, WhatsApp chat exports (`.txt`) and Telegram Desktop exports (`result.json`). It supports alternate field names and converts records into the common `Post` model:

- `post_id`
- `account_id`
- `username`
- `created_at`
- `text`
- `urls`
- `hashtags`
- `reply_to`
- `repost_of`
- `account_created_at`
- `platform`, `city`, `language` (language is detected from the text when missing: Devanagari → Hindi, Hindi words in Roman script → Hinglish)

It parses ISO dates, Unix seconds, Unix milliseconds, and common social-media export formats. Rows without a usable account or timestamp are skipped. Missing required columns cause the upload to be rejected.

## 2. Coordination Detection

Primary code: `src/engine/coordination.py`

The project builds multiple account-to-account networks:

| Signal | Meaning |
|---|---|
| Co-tweet | Same text within a time window |
| Co-similar-tweet | Near-duplicate or paraphrased text |
| Co-link | Same URL within a time window |
| Co-reply | Same reply target within a time window |
| Co-retweet | Same repost target within a time window |

The networks are merged into one weighted graph. Edge metadata retains the signals that created the relationship.

## 3. Campaign Discovery

Primary code: `src/engine/campaigns.py`

NetworkX Louvain community detection finds groups of connected accounts. Communities below the minimum campaign size are ignored. Campaign records retain account IDs, post IDs, time range, signals, hashtags, and score components.

## 4. Explainable Scoring

Primary code: `src/engine/scoring.py`

The score combines six behavioral features:

- Speed of coordinated activity.
- Duplicate or near-duplicate text.
- Number of coordination signals.
- Fresh-account proportion.
- Burst intensity.
- Hashtag or URL concentration.

The result is a 0-100 coordination score. It measures how strongly a group behaves in a coordinated way. It does not by itself measure criminality, identity, or intent.

## 4a. Spread Profile

Primary code: `src/engine/incident.py`

For each campaign: the first posters (seeds), the most connected accounts (amplifiers), the order of platforms and towns reached with times, the share of new accounts, and `detected_at`, the earliest time at least 5 of its accounts were linked by 2 or more co-actions. Compared with the planned gathering, this gives the lead time.

## 5. IBM Bob Analysis

Primary code: `src/bob/client.py`

Bob receives campaign statistics and representative posts. It returns structured fields for:

- Threat type.
- Target.
- Narrative.
- Severity from 1 to 5.
- Offline call-to-action flag and any planned gathering (what, where, a quote of the place from a post, when).
- Legal suggestion IDs.
- Evidence post IDs.

The application validates the response with Pydantic. Evidence IDs must be posts Bob was shown. The gathering is kept only if its place is quoted from a post and its time falls between a day before the first post and three days after the last. Legal IDs must be present in the approved legal reference table and must be offence entries when used as offence suggestions.

## 6. Escalation Rules

Primary code: `src/engine/escalation.py`

The current rules are deterministic:

- `URGENT`: incitement plus an offline call to action, or very high score plus high severity.
- `ALERT`: organized misinformation or targeted harassment with a sufficiently high score.
- `MONITOR`: other cases, including benign coordination.

When a planned gathering exists, actions name its place and time (deploy police before the gathering, issue a public advisory in Hindi and English). The recommended actions are operational suggestions. They require analyst and supervisor review.

## 7. Threat Brief

Primary code: `src/brief/render.py`

The brief contains:

- Generation timestamp in IST.
- Dataset SHA-256 hash.
- Executive summary.
- Campaign score and feature breakdown.
- Bob assessment.
- Evidence post IDs and timestamps.
- Evidence text hashes.
- Legal references to check.
- Recommended escalation actions.
- Limitations.

## 8. APIs and Interfaces

Primary code: `src/api/main.py`

The FastAPI backend provides dataset upload, analysis, campaign, graph, timeline, classification, and brief endpoints, plus a rolling-window stream API (`/api/streams/{id}/posts`, `/alerts`, `/timeline`, `/close`) that stores posts in SQLite and re-runs detection on the last 3 hours of event time after each request (one post or a list). The React frontend presents the data as a command center. The MCP server provides read-only investigation tools for Bob Chat.

## 9. Current Technical Boundaries

- There is no live platform connector; the stream API rebuilds the graph on every post and suits a demonstration only.
- Bob classification requires the Bob CLI and API key unless cached results are available.
- Score weights are hand-set; the incident packs are generated.
- Real datasets do not provide complete ground truth for campaign or threat labels.
- Legal references are restricted suggestions and require qualified review.

## 10. Recommended Technical Evolution

1. Incremental edge updates for the stream instead of a full rebuild per post.
2. Capture original row number, input hash, source URL, and ingestion timestamp.
3. Add review status and append-only audit events.
4. Calibrate thresholds on held-out benign and threat datasets.
5. Add model, prompt, rule, and configuration versions to every result.
