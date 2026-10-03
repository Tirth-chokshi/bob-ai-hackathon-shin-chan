# FAQ and Limitations

## Is this a real-time system?

The main workflow analyses an uploaded batch in seconds (11–16 s for a 3,000-post incident pack) and shows how early each network could have been flagged: 4–12 hours before the planned gathering in the demo incidents. Posts can also be sent one at a time to the rolling-window stream API, which returns a provisional alert after each post. It rebuilds the graph from the window every time, so it suits a demonstration, not production volumes. There is no live platform connector.

## Does it prove that an account is a bot?

No. It identifies coordination patterns such as synchronized posting, repeated text, shared links, replies, or reposts. Those patterns can justify review, but they do not prove automation or inauthenticity.

## Does it predict violence?

No. It highlights possible offline calls to action and coordinated threat indicators in the supplied posts. It cannot predict whether violence will occur. A trained analyst must verify the content, context, location, timing, and credibility.

## Does IBM Bob make the final decision?

No. Bob helps interpret campaign content. The application validates Bob's structured output and uses deterministic escalation rules. Human analysts and supervisors remain responsible for decisions.

## Why is benign coordination important?

Many legitimate groups coordinate online: sports fans, emergency responders, journalists, community organizers, and public-event participants. The system includes benign coordination to reduce the risk of treating every coordinated group as harmful.

## What data does the system need?

At minimum, each post needs an account identifier, timestamp, and text. Links, hashtags, reply targets, repost targets, account creation dates, platform and town improve the analysis. CSV/JSON files, WhatsApp chat exports and Telegram Desktop exports are accepted as they are.

## Can it analyze the actual Nupur Sharma controversy or the 2020 Delhi riots?

The bundled incidents are fictional (fictional districts and towns) over real, non-hostile CONSTRAINT-2021 background posts, and do not claim to analyze those real events. Researching real incidents would require lawful access, appropriate data licensing, privacy safeguards, verified sources, and careful historical validation.

## Are the legal sections automatically correct?

No. The project restricts suggestions to a controlled reference table to reduce hallucinated citations. The suggestions still require review by a qualified legal officer because applicability depends on facts, jurisdiction, evidence, and current law.

## Is a high CIB score a criminal finding?

No. It is a behavioral coordination score. It should be described as a prioritization signal, never as proof of criminal conduct.

## What happens if IBM Bob is unavailable?

The local graph, timeline, normalization, campaign discovery, and scoring pipeline can still operate. Cached verdicts can support the bundled demo. A live classification requires the Bob CLI and configured credentials.

## What is the strongest current result?

Across the three incident packs, all 10 planted networks are found with no wrong accounts mixed in, none of the 144 ordinary "is this true?" posters is clustered, each benign decoy scores lowest and stays at MONITOR, and the calling network is flagged 7 h 12 m, 3 h 54 m and 11 h 49 m before the planned gathering. IBM Bob extracted all three gatherings (place and time) correctly.

## What is the biggest current limitation?

The scoring weights are hand-set, and the ground truth comes from generated incidents. Real archives (IRA, X information operations) score 35–63. More labeled real-world and benign data is needed before making operational performance claims.

## What should be added next?

The highest-value improvements are:

1. Live platform connectors and incremental (not full-rebuild) stream detection.
2. Source provenance per record and an evidence manifest per run.
3. Review states, case management and audit logs.
4. Calibration on held-out real and benign datasets.
5. Benchmarking IBM Bob's labels on more campaigns.

## What should we say about safety?

Use this sentence:

> Social Media Threat Intelligence Engine is a human-reviewed intelligence and evidence-organization tool. It does not infer protected identity, automatically label people as criminals, recommend force, or replace established legal and organizational procedures.

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
