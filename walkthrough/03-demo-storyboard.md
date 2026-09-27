# Live Demo Storyboard

Target duration: 4 to 6 minutes.

The demo should tell one story: an analyst starts with a large post batch, finds an emerging coordinated campaign, checks the evidence, asks Bob for interpretation, and creates a reviewable brief.

## Before the Demo

1. Start the application with `python src/main.py`.
2. Open `http://127.0.0.1:8000`.
3. Confirm that the bundled `demo` dataset is visible.
4. Confirm that the pre-analyzed campaign results and cached Bob verdicts are available.
5. Keep the network, overview, Bob assessment, and brief screenshots available as a backup.

## Scene 1: Dataset Overview

**Action:** Open the Datasets or Overview page.

**Point out:**

- Number of posts and accounts.
- Analysis status.
- Timeline of activity.
- Campaign list and risk scores.

**Say:**

"This is the analyst's starting point. Instead of manually scanning thousands of posts, the system has reduced the dataset to a small number of account clusters that require attention."

## Scene 2: Show the Benign Decoy

**Action:** Open the campaign representing coordinated cricket-fan activity.

**Point out:**

- It is coordinated.
- Its score is not zero.
- IBM Bob classifies it as benign coordination.
- It remains at `MONITOR`.

**Say:**

"Coordination alone is not criminality. This decoy demonstrates that the system keeps a strong behavioral pattern separate from the question of whether the content is threatening."

## Scene 3: Show the Highest-Risk Campaign

**Action:** Open the rumour or gathering-call campaign.

**Point out:**

- Connected accounts in the network graph.
- Repeated or similar text.
- Shared hashtag or URL.
- Tight posting times.
- New-account or burst signals when available.

**Say:**

"The graph shows the relationship between accounts. The timeline shows the burst. The score breakdown explains why this campaign was prioritized."

## Scene 4: Ask Bob for Threat Interpretation

**Action:** Open the Bob assessment or select `Ask Bob` if the environment has a configured key.

**Point out:**

- Threat category.
- Severity.
- Narrative.
- Possible offline call to action.
- Evidence post IDs.
- Legal suggestions marked for review.

**Say:**

"IBM Bob is used after the behavioral filter. It interprets the representative evidence, but the application validates its post IDs and legal IDs before displaying the result."

## Scene 5: Explain Escalation

**Action:** Show the escalation panel.

**Point out:**

- `URGENT` is triggered by the documented rule combination.
- Recommended actions include preserving evidence and notifying the appropriate control room.
- These are recommendations, not automatic orders.

**Say:**

"The escalation level comes from deterministic rules using the coordination score and validated threat fields. An authorized officer still decides what action is appropriate."

## Scene 6: Generate the Brief

**Action:** Open the threat brief.

**Point out:**

- Generation timestamp.
- Dataset hash.
- Campaign summary.
- Evidence table.
- SHA-256 evidence hashes.
- Legal provisions to check.
- Recommended actions.
- Limitations and review language.

**Say:**

"The brief turns analysis into an artifact that a supervisor or legal reviewer can inspect. It preserves the evidence references and shows how the recommendation was reached."

## Closing Statement

"SHIN-CHAN does not claim to predict violence or automatically identify criminals. Its value is earlier, explainable triage: finding coordinated campaigns, organizing evidence, and helping trained personnel decide what to verify next."

## Demo Recovery Lines

### If Bob is unavailable

"The behavioral detection, graph, timeline, scoring, and cached demo verdicts continue to work locally. Live Bob classification requires the Bob CLI and API key."

### If the audience asks whether this is real data

"The bundled scenario is fictional and designed for safe demonstration. The repository also includes adapters for research datasets, but real-world calibration requires labeled data and appropriate privacy and licensing review."

### If the audience asks whether the system identifies bots

"No. It detects coordination patterns. A coordination score is a lead for investigation, not proof that an account is automated or inauthentic."
