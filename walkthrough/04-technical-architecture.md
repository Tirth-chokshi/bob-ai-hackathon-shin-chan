# Technical Architecture Walkthrough

## End-to-End Flow

```text
CSV or JSON upload
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
Explainable CIB score: 0-100
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

The loader accepts CSV and JSON files. It supports alternate field names and converts records into the common `Post` model:

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

## 5. IBM Bob Analysis

Primary code: `src/bob/client.py`

Bob receives campaign statistics and representative posts. It returns structured fields for:

- Threat type.
- Target.
- Narrative.
- Severity from 1 to 5.
- Offline call-to-action flag.
- Legal suggestion IDs.
- Evidence post IDs.

The application validates the response with Pydantic. Evidence IDs must belong to the campaign. Legal IDs must be present in the approved legal reference table and must be offence entries when used as offence suggestions.

## 6. Escalation Rules

Primary code: `src/engine/escalation.py`

The current rules are deterministic:

- `URGENT`: incitement plus an offline call to action, or very high score plus high severity.
- `ALERT`: organized misinformation or targeted harassment with a sufficiently high score.
- `MONITOR`: other cases, including benign coordination.

The recommended actions are operational suggestions. They require analyst and supervisor review.

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

The FastAPI backend provides dataset upload, analysis, campaign, graph, timeline, classification, and brief endpoints. The React frontend presents the data as a command center. The MCP server provides read-only investigation tools for Bob Chat.

## 9. Current Technical Boundaries

- Analysis is primarily batch-oriented rather than a live stream.
- Bob classification requires the Bob CLI and API key unless cached results are available.
- Score weights are hand-tuned for the synthetic scenario.
- Real datasets do not provide complete ground truth for campaign or threat labels.
- Legal references are restricted suggestions and require qualified review.

## 10. Recommended Technical Evolution

1. Add rolling-window ingestion while retaining batch mode.
2. Capture original row number, input hash, source URL, and ingestion timestamp.
3. Add review status and append-only audit events.
4. Add structured extraction for reported locations, event times, and action types.
5. Calibrate thresholds on held-out benign and threat datasets.
6. Add model, prompt, rule, and configuration versions to every result.
