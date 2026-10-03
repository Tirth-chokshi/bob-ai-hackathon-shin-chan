# Alignment Walkthrough: Social Media Threat Intelligence Engine

> **Status (27 Sep 2026).** Done: rolling-window stream API (`/api/streams`); structured offline-threat extraction (IBM Bob's planned gathering: place quoted from a post, time checked); evidence limited to posts Bob was shown; brief wording no longer claims BSA compliance or admissibility; realistic mock incidents (three incident packs). Not done: per-record provenance and run manifests, review states and audit logs, versioned legal metadata, score calibration on labeled real data. The sections below are the original proposal.

This walkthrough explains the changes that would move Social Media Threat Intelligence Engine closer to the problem statement: detecting coordinated online campaigns, identifying possible offline threats, mapping findings for legal review, and producing an actionable, time-stamped brief for a cyber cell.

The project is already a strong batch-analysis prototype. The changes below focus on making its claims, workflow, evidence handling, and evaluation match the operational problem more closely without presenting automated output as a final police or legal decision.

## Current Position

The existing pipeline already provides:

- CSV and JSON ingestion with normalization.
- Coordination signals for copied or similar text, shared links, replies, and reposts.
- Campaign discovery with a NetworkX graph.
- An explainable CIB score.
- IBM Bob classification for incitement, targeted harassment, organized misinformation, and benign coordination.
- A fixed legal-reference table with validation.
- Deterministic `MONITOR`, `ALERT`, and `URGENT` escalation levels.
- A time-stamped HTML brief with evidence hashes.

The main gaps are that analysis is batch-only, scores are tuned primarily on synthetic data, source provenance is limited, the legal output needs stronger review boundaries, and the demonstration should show an end-to-end emerging-threat workflow rather than only a completed analysis.

## Priority Plan

| Priority | Change | Why it matters |
|---|---|---|
| P0 | Add a streaming or rolling-window analysis mode | The problem statement emphasizes early warning and real-time forensic signals. |
| P0 | Preserve source provenance and evidence chain | A threat brief must show where each post came from and whether the record changed. |
| P0 | Add explicit uncertainty and human-review states | Coordination is not proof of inauthenticity, criminal intent, or imminent violence. |
| P1 | Calibrate and evaluate scores on labeled and benign data | Hand-tuned synthetic scores are not enough to support operational confidence. |
| P1 | Improve offline-threat extraction and location/time fields | Escalation depends on whether a campaign points to a place, time, target, or action. |
| P1 | Make legal references reviewable and versioned | Statutory mappings change and must not be treated as automatic charges. |
| P2 | Add role-based workflow, audit logs, and case lifecycle | Cyber-cell users need repeatable triage, assignment, review, and closure. |
| P2 | Add a realistic mock incident walkthrough | The demo should prove the problem statement in a few minutes. |

## P0: Add Rolling-Window Detection

### What to change

Add an analysis mode that accepts posts incrementally and recalculates coordination signals over a configurable recent window, such as 5 minutes, 15 minutes, or 1 hour. Keep the existing batch pipeline for uploaded files and historical investigations.

Suggested API surface:

```text
POST /api/streams/{stream_id}/posts
GET  /api/streams/{stream_id}/alerts
GET  /api/streams/{stream_id}/timeline
POST /api/streams/{stream_id}/close
```

A submitted post should be normalized immediately. The engine should update the relevant coordination edges and return a provisional alert when a campaign crosses a threshold.

### Why it matters

The problem is not only discovering a campaign after an event. It is giving a cyber cell an early-warning window while a burst is forming. A rolling window lets the demo show accounts coordinating within seconds or minutes and allows an officer to act before the campaign has finished spreading.

### How to implement

1. Extract the reusable parts of `engine.normalize.load_rows` so one row can be normalized without pretending that the entire file is complete.
2. Add a stream store keyed by `stream_id` and a bounded retention period. SQLite is sufficient for the prototype.
3. Reuse `engine.coordination.build_graph` for periodic recomputation first. Optimize to incremental edges only after the behavior is correct.
4. Add a `window_started_at`, `window_ended_at`, and `last_updated_at` to alert responses.
5. Keep alert status provisional until a human reviews the evidence.
6. Add tests for posts arriving out of order, duplicate post IDs, late posts, and a campaign that falls below the threshold as the window expires.

The first implementation can poll every 15 to 60 seconds. It does not need a full message queue to demonstrate early warning.

## P0: Strengthen Provenance and Evidence Integrity

### What to change

Store provenance for every normalized post and every generated result:

- Dataset or stream identifier.
- Original source filename or source connector.
- Original row number.
- Ingestion timestamp in UTC.
- Original record hash.
- Normalized record hash.
- Source platform and post URL when available.
- Whether a field was supplied, inferred, defaulted, or extracted from text.

Add a manifest such as `manifest.json` to each run containing the input hash, schema version, configuration values, software version, and analysis start/end times.

### Why it matters

The problem statement asks for a time-stamped evidentiary brief. The current SHA-256 hashes help, but hashing only normalized output does not fully prove which source record produced it. Provenance makes the evidence chain auditable and helps an investigator reproduce the finding.

### How to implement

1. Extend `engine.schema.Post` with optional provenance fields, or store provenance in a companion record if keeping the public post shape stable is important.
2. Hash the exact input bytes at upload time before parsing.
3. Hash the original row representation with stable JSON serialization.
4. Write the manifest during upload and update it when analysis completes.
5. Include a compact provenance column in the brief and expose full details through the API.
6. Add a verification command that recomputes hashes and reports mismatches.

Do not describe the output as legally admissible by default. Describe it as an evidence-preservation aid that still requires the applicable certification and chain-of-custody process.

## P0: Add Uncertainty and Human Review States

### What to change

Separate these concepts in the data model and UI:

- `coordination_score`: behavioral similarity or coordination strength.
- `threat_assessment`: semantic classification from Bob.
- `confidence`: confidence or evidence completeness, not a claim of factual truth.
- `review_status`: `unreviewed`, `analyst_review`, `supervisor_review`, `closed`.
- `assessment_status`: `pending`, `classified`, `classification_failed`, `insufficient_evidence`.
- `false_positive_reason`: optional analyst explanation.

Show language such as `Possible coordinated campaign` and `Requires analyst verification`, especially for high scores with benign or incomplete content.

### Why it matters

Fan groups, breaking-news users, emergency coordinators, and legitimate activists can coordinate without being inauthentic or threatening. A score must prioritize human review, not automatically label people, communities, or accounts as criminals.

### How to implement

1. Add fields to `Campaign` and `BobVerdict` in `engine/schema.py`.
2. Update `engine.escalation.escalate` so actions are recommendations and the final state remains pending review.
3. Add a review endpoint and persist reviewer, timestamp, decision, and reason.
4. Add a visible warning to the dashboard and brief: automated decision support only.
5. Add tests proving that a high CIB score alone cannot produce an `URGENT` threat without the required threat assessment and review state.
6. Keep the existing benign-coordination class and add more benign decoys to testing.

## P1: Improve Offline-Threat Extraction

### What to change

Extend the Bob verdict and brief to capture structured indicators:

```json
{
  "offline_call_to_action": true,
  "action_type": "gathering",
  "locations": ["Central Market"],
  "event_times": ["2026-09-27T19:00:00+05:30"],
  "targeted_groups": ["unverified target description"],
  "urgency_reason": "repeated gathering instruction across 18 accounts",
  "evidence_post_ids": ["p1", "p2"]
}
```

Treat location, time, and target as extracted claims requiring verification, not facts.

### Why it matters

The problem statement is specifically about online patterns that may precede offline harm. A generic threat label is less useful to a duty officer than a structured answer to: what action, where, when, and directed at whom?

### How to implement

1. Extend the Pydantic output schema and Bob prompt in `bob/client.py`.
2. Validate timestamps, locations, and evidence IDs. Reject unsupported or malformed values.
3. Add deterministic checks for repeated location/time phrases where practical.
4. Add a timeline marker for an extracted event time, clearly labeled `reported in posts`.
5. Add a separate `verification_required` flag to every extracted indicator.
6. Update escalation rules so an offline call to action is stronger when supported by multiple independent evidence posts, not only one model field.

Do not infer a person's religion, caste, ethnicity, or political affiliation from a post or account.

## P1: Calibrate Detection and Threat Evaluation

### What to change

Expand evaluation beyond one synthetic scenario:

- Multiple synthetic campaigns with different posting speeds and paraphrases.
- Benign coordination such as sports fans, emergency information sharing, and public-event announcements.
- Labeled research datasets where licensing and privacy requirements permit.
- Human-reviewed examples for each threat type.
- Stress tests for missing fields, time zones, duplicate rows, and unrelated viral events.

Report precision, recall, false-positive rate, time to detection, evidence completeness, and runtime. Report results separately for coordination detection and threat classification.

### Why it matters

The current project can demonstrate that planted rings are detected and that a benign decoy scores lower. It cannot yet establish that the same thresholds work for real incidents. Separating evaluation layers prevents a good network score from being mistaken for accurate threat classification.

### How to implement

1. Add a versioned evaluation fixture format with ground-truth campaign IDs and threat labels.
2. Run repeated seeds for synthetic generation rather than relying on one seed.
3. Measure detection at several rolling-window sizes.
4. Calibrate score thresholds on a held-out set, not the data used to tune weights.
5. Record Bob model/configuration versions and prompt versions with every result.
6. Add a regression test that fails when a benign decoy becomes an `URGENT` campaign without supporting evidence.

Keep the limitations visible in `src/eval/results.md` and in every demo brief.

## P1: Version and Review Legal References

### What to change

Turn the fixed legal table into a versioned legal-reference dataset with:

- Provision identifier.
- Current statute and section.
- Historical IPC cross-reference where relevant.
- Plain-language description.
- Offence or procedural classification.
- Effective date.
- Source and last legal review date.
- Required disclaimer.

### Why it matters

The legal table is useful for narrowing Bob's suggestions, but a whitelist does not prove that a provision applies to a particular post. Statutory language, procedural requirements, and jurisdictional practice require legal review.

### How to implement

1. Keep parsing in `bob/legal.py`, but add schema validation for version, source, and review date.
2. Display legal suggestions as `provisions to check`, not charges or conclusions.
3. Separate offence provisions from procedural actions such as blocking requests, preventive orders, and electronic-record certification.
4. Add a reviewer acknowledgement field before a brief can be marked final.
5. Add tests ensuring procedural IDs cannot appear in the offence list.
6. Have a qualified legal reviewer verify every table entry before using the tool outside a mock scenario.

## P2: Add a Case and Audit Workflow

### What to change

Add a lightweight case lifecycle:

```text
New dataset -> Analyzed -> Campaign selected -> Analyst reviewed ->
Supervisor reviewed -> Brief issued -> Closed
```

Record every meaningful action:

- User or role.
- Action and case ID.
- Timestamp in UTC.
- Previous and new status.
- Reason or note.
- Model, prompt, rules, and score versions where applicable.

### Why it matters

The problem statement describes an operational tool for cyber cells, not only an analytics screen. A case workflow makes it possible to assign work, document decisions, and explain how an alert became a brief.

### How to implement

1. Add case metadata beside each dataset run.
2. Use SQLite for the prototype and keep the API layer independent of storage details.
3. Add analyst and supervisor actions to the web UI.
4. Make audit records append-only from the application layer.
5. Include the case ID and review status in the generated brief.
6. Add API tests for unauthorized transitions and immutable audit entries.

## P2: Build the Demonstration Around an Emerging Incident

### What to change

Create a scripted mock scenario with three phases:

1. **Normal baseline:** benign posts and ordinary public discussion.
2. **Emergence:** several accounts repeat a narrative, URL, hashtag, or gathering instruction in a short window.
3. **Escalation:** the rolling detector raises an alert, Bob summarizes the threat, and an analyst reviews evidence before generating the brief.

Use fictional locations, groups, and identities. Do not recreate real victims, communities, or unverified claims from the Delhi riots or the Nupur Sharma controversy.

### Why it matters

This demonstrates the problem statement without implying that the system has analyzed real events or can predict violence. It also makes the early-warning value visible to judges: the system identifies behavior, surfaces evidence, and recommends a review path.

### How to implement

1. Extend `scenario/generate_scenario.py` with timestamps and a baseline-to-burst sequence.
2. Add expected detection time and expected alert state to `truth.json`.
3. Add a walkthrough script or UI fixture that advances the scenario phase by phase.
4. Show the graph, timeline, evidence posts, threat assessment, legal references, and escalation actions in that order.
5. End the demo with an analyst acknowledgement and the limitations panel.
6. Add the exact demo commands and expected outputs to `demo/stream-demo.md`.

## Suggested Implementation Order

1. Add review and uncertainty fields while preserving the existing batch workflow.
2. Add provenance fields, input manifests, and hash verification.
3. Add structured offline-threat indicators and evidence-completeness checks.
4. Add rolling-window ingestion using periodic recomputation.
5. Expand synthetic and benign evaluation fixtures.
6. Version the legal-reference table and add reviewer acknowledgement.
7. Add case lifecycle, audit logs, and the scripted walkthrough.
8. Re-run Python tests, frontend build, evaluation, and a clean end-to-end demo.

## Definition of Done

The project is better aligned when it can demonstrate all of the following:

- A mock post stream produces a provisional campaign alert before the scenario ends.
- The alert explains which coordination signals caused it and shows the relevant time window.
- Bob classifies the campaign only from supplied evidence and returns validated evidence IDs.
- Offline action, reported location, reported time, and target are shown as claims requiring verification.
- The legal section is labeled for legal review and distinguishes offences from procedures.
- A reviewer can accept, downgrade, or reject an alert with a recorded reason.
- The final brief contains source hashes, provenance, timestamps, configuration versions, limitations, and reviewer status.
- Evaluation reports false positives on benign coordination, not only detection of planted threat rings.
- The demo uses fictional data and clearly states that the system is decision support, not an autonomous enforcement tool.

## Files to Touch First

- `src/engine/schema.py`: review state, provenance, uncertainty, and structured indicators.
- `src/engine/normalize.py`: row-level normalization and provenance capture.
- `src/engine/pipeline.py`: manifest creation and versioned analysis metadata.
- `src/engine/escalation.py`: evidence-aware recommendations and review boundaries.
- `src/bob/client.py`: structured offline-threat extraction and validation.
- `src/bob/legal.py`: versioned legal-reference validation.
- `src/brief/render.py`: provenance, review status, disclaimers, and extracted indicators.
- `src/api/main.py`: rolling ingestion, review actions, and audit endpoints.
- `src/scenario/generate_scenario.py`: baseline-to-emergence mock incident.
- `src/tests/`: rolling-window, provenance, benign-decoy, legal-table, and review-workflow tests.
- `demo/stream-demo.md`: judge-facing walkthrough and limitations.

## Safety and Scope Boundary

This project should remain a human-reviewed intelligence and evidence-organization tool. It should not automatically identify protected communities, infer personal identity or affiliation, declare an account a bot, recommend force, or create a criminal charge. Its output should help a trained analyst decide what to verify next, preserve relevant records, and escalate through established legal and organizational procedures.
