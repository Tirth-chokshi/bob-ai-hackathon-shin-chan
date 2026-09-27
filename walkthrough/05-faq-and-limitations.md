# FAQ and Limitations

## Is this a real-time system?

Currently, the main workflow analyzes uploaded batches. It is designed to support a future rolling-window or streaming mode. In a presentation, describe the current product as a batch decision-support prototype with a clear path to early-warning operation.

## Does it prove that an account is a bot?

No. It identifies coordination patterns such as synchronized posting, repeated text, shared links, replies, or reposts. Those patterns can justify review, but they do not prove automation or inauthenticity.

## Does it predict violence?

No. It highlights possible offline calls to action and coordinated threat indicators in the supplied posts. It cannot predict whether violence will occur. A trained analyst must verify the content, context, location, timing, and credibility.

## Does IBM Bob make the final decision?

No. Bob helps interpret campaign content. The application validates Bob's structured output and uses deterministic escalation rules. Human analysts and supervisors remain responsible for decisions.

## Why is benign coordination important?

Many legitimate groups coordinate online: sports fans, emergency responders, journalists, community organizers, and public-event participants. The system includes benign coordination to reduce the risk of treating every coordinated group as harmful.

## What data does the system need?

At minimum, each post needs an account identifier, timestamp, and text. Links, hashtags, reply targets, repost targets, account creation dates, and source URLs improve the analysis.

## Can it analyze the actual Nupur Sharma controversy or the 2020 Delhi riots?

The bundled demo uses fictional data and does not claim to analyze those real events. Researching real incidents would require lawful access, appropriate data licensing, privacy safeguards, verified sources, and careful historical validation.

## Are the legal sections automatically correct?

No. The project restricts suggestions to a controlled reference table to reduce hallucinated citations. The suggestions still require review by a qualified legal officer because applicability depends on facts, jurisdiction, evidence, and current law.

## Is a high CIB score a criminal finding?

No. It is a behavioral coordination score. It should be described as a prioritization signal, never as proof of criminal conduct.

## What happens if IBM Bob is unavailable?

The local graph, timeline, normalization, campaign discovery, and scoring pipeline can still operate. Cached verdicts can support the bundled demo. A live classification requires the Bob CLI and configured credentials.

## What is the strongest current result?

In the bundled synthetic scenario, three planted threat rings and one benign coordinated decoy are detected as separate groups. The threat rings receive high scores, while the decoy is classified as benign coordination and remains at monitor level.

## What is the biggest current limitation?

The scoring thresholds are hand-tuned mainly on synthetic data, and the primary workflow is batch-based. More labeled real-world and benign data is needed before making operational performance claims.

## What should be added next?

The highest-value improvements are:

1. Rolling-window ingestion for emerging campaigns.
2. Stronger source provenance and evidence manifests.
3. Explicit uncertainty and human-review states.
4. Structured location, time, and action extraction.
5. Calibration on held-out datasets.
6. Case management and audit logs.

## What should we say about safety?

Use this sentence:

> SHIN-CHAN is a human-reviewed intelligence and evidence-organization tool. It does not infer protected identity, automatically label people as criminals, recommend force, or replace established legal and organizational procedures.

## What should we avoid saying?

Avoid these claims:

- "The system predicts riots."
- "The system proves these are bots."
- "IBM Bob decides which law applies."
- "The brief is automatically legally admissible."
- "The project analyzed the real Delhi riots or Nupur Sharma case."

Use these alternatives:

- "The system identifies patterns associated with coordinated behavior."
- "The system prioritizes campaigns for human review."
- "Bob provides a constrained, evidence-based assessment."
- "The brief supports evidence preservation and legal review."
- "The demo uses fictional data inspired by the problem context."
