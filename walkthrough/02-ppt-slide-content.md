# PPT Slide Content

This is a ready-to-use 8-slide structure. Keep each slide visual and move detailed explanation into speaker notes.

## Slide 1: Title

**Title:** SHIN-CHAN: Social Media Threat Intelligence Engine

**Subtitle:** Detecting coordinated online campaigns before they become offline risks

**Include:**

- Team Shin-chan
- IBM Bob AI Innovation Hackathon
- Track 2: Cyber Forensics
- One screenshot of the command center

**Speaker note:**

"We built a decision-support tool for cyber-cell analysts who need to identify coordinated social-media campaigns quickly and prepare evidence for human review."

## Slide 2: The Problem

**Headline:** Dangerous patterns are difficult to see one post at a time

**Show:** A visual contrast between many separate posts and one connected campaign.

**Points:**

- Sensitive incidents can produce very high post volumes.
- Manual review is slow and mostly post-by-post.
- Coordinated behavior can be hidden behind harmless-looking messages.
- Officers need evidence, context, and escalation guidance in one place.

**Speaker note:**

"The important signal is often not one sentence. It is many accounts repeating, linking, replying, or amplifying within a short time window."

## Slide 3: Our Core Idea

**Headline:** Behavior first, content second

**Show:** A two-step diagram:

```text
Posts -> Coordination patterns -> Campaigns -> Threat interpretation -> Human review
```

**Points:**

- First detect synchronized behavior.
- Then understand the content and possible intent.
- Keep benign coordination visible so it is not treated as a threat automatically.

**Speaker note:**

"A sports-fan group can coordinate strongly without being dangerous. The system therefore separates coordination strength from threat meaning."

## Slide 4: How It Works

**Show:** Five numbered stages:

1. Upload posts: CSV/JSON, WhatsApp chat export or Telegram export (Hindi, Hinglish, English).
2. Build coordination networks from five signals.
3. Find account communities, calculate a 0-100 score, and trace how each spread (platforms, towns, first posters).
4. Ask IBM Bob to classify the campaign and extract any planned gathering (place and time).
5. Generate a time-stamped threat brief.

**Five signals:**

- Same text
- Similar text
- Same link
- Same reply target
- Same repost target

**Speaker note:**

"The output is explainable. Analysts can see which signals and score components caused a campaign to be highlighted."

## Slide 5: IBM Bob and Legal Intelligence

**Headline:** IBM Bob turns patterns into an analyst-readable assessment

**Show:** A sample verdict panel or Bob assessment screenshot.

**Bob provides:**

- Threat category
- Severity
- Narrative and target
- Planned offline gathering: place and time
- Evidence post IDs
- Legal provisions to check

**Guardrails:**

- Evidence IDs must be posts Bob was shown.
- The gathering place must be quoted from a post and its time must be plausible.
- Legal suggestions are restricted to a reference table.
- Legal output is marked for qualified review.

**Speaker note:**

"Bob handles language understanding. Deterministic code controls validation and escalation so the model does not make the final operational decision."

## Slide 6: Command Center and Threat Brief

**Show:** Two screenshots: the Overview (threat card, incident timeline, spread map) and the generated brief.

**Points:**

- Threat card: where and when a crowd is called, and how early it was flagged.
- Incident timeline: first post, flagged, peak, planned gathering.
- Spread: platform by platform and town by town; campaign graph shows who coordinated with whom.
- Brief includes timestamps, evidence posts, hashes, legal references, and recommended actions.
- Escalation levels are `MONITOR`, `ALERT`, and `URGENT`.

**Speaker note:**

"The goal is to reduce the time from raw posts to a structured case for analyst and supervisor review."

## Slide 7: Results and Impact

**Show:** A small table or four metric cards.

**Three incident packs** (about 3,000 posts each, five platforms, three languages):

- Flagged 7 h 12 m, 3 h 54 m and 11 h 49 m before the planned gathering
- All 10 planted networks found, no wrong accounts mixed in
- 0 of 144 ordinary "is this true?" posters clustered
- Each benign decoy scores lowest and stays at MONITOR
- IBM Bob extracted all 3 gatherings (place and time) correctly
- 11–16 seconds per pack on a laptop

**Important qualification:**

Incidents are generated (fictional districts) over real CONSTRAINT-2021 background posts. Real archives (IRA, X information operations) score 35–63; thresholds need calibration on labeled real data.

**Speaker note:**

"The decoy matters: the system detects coordination but does not automatically call every coordinated group harmful."

## Slide 8: Impact, Boundaries, and Next Steps

**Headline:** From post overload to explainable human review

**Current value:**

- Faster triage
- Explainable coordination signals
- Structured evidence preservation
- Bob-assisted threat summaries
- Reviewable legal references

**Next steps:**

- Live platform connectors and incremental stream detection
- Source provenance per record
- More benign and real-world evaluation data
- Case workflow and audit logs

**Boundary:**

"This is decision support, not an autonomous enforcement or legal system."

**Closing line:**

"SHIN-CHAN helps analysts see the campaign behind the posts, verify the evidence, and act through established procedures."

## Presentation Design Notes

- Use one idea per slide.
- Use screenshots and arrows instead of paragraphs.
- Keep body text large enough to read from a distance.
- Use the fictional incident packs; do not imply that the system analyzed real victims or real events.
- Put technical details, legal disclaimers, and benchmark limitations in speaker notes or the appendix.
