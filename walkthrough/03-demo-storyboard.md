# Live Demo Storyboard

> **Note (28 Sep 2026):** the bundled demo incidents were removed; the app now starts empty. Replace the scenes below with the dataset you demo.

Target duration: 4 to 6 minutes.

The demo tells one story: a child-kidnapping rumour spreads across WhatsApp, X, Facebook and Telegram in Navgarh district and calls a crowd to Rajpura bus stand at 6 PM. The analyst sees where and when, how early it was caught, how it spread and who started it, checks the evidence, and prints a reviewable brief.

For a live baseline-to-burst stream using fictional posts, follow [`../demo/stream-demo.md`](../demo/stream-demo.md). The stream endpoints return provisional coordination alerts; IBM Bob interpretation remains a separate action on analysed campaigns.

## Before the Demo

1. Start the application with `python src/main.py`.
2. Open `http://127.0.0.1:8000`.
3. Confirm the three bundled incident packs are listed on **Datasets** (kidnapping rumour, procession rumour, paper-leak scam).
4. Confirm the kidnapping pack opens with cached IBM Bob verdicts (no key needed).
5. Keep the screenshots in `demo/screenshots/` as a backup.

## Scene 1: The Threat at a Glance

**Action:** Open **Overview** for the Navgarh kidnapping rumour.

**Point out:**

- **Emerging offline threats** card: Rajpura bus stand, 18:00, time left after the last post.
- "Flagged 7 h 12 m before the gathering": the lead time.
- Five numbers: campaigns, urgent, accounts involved, platforms, towns.

**Say:**

"Instead of reading 3,000 posts in three languages, the officer sees one line: a crowd is being called to Rajpura bus stand at 6 PM, and the network behind it was detected seven hours earlier."

## Scene 2: How It Unfolded

**Action:** Point along the **incident timeline**, then the **Where it spread** map.

**Point out:**

- ● first post, ▲ flagged, ■ peak, ⚑ planned gathering, and the lead-time bracket.
- Grey background is ordinary posts; coloured bands are the campaigns.
- Towns numbered in the order the rumour reached them, flag at the gathering place.

**Say:**

"The coordinated accounts spike together, which is the behavioural signal. It started in one town and reached four before the evening."

## Scene 3: Who Started It and Why It Was Flagged

**Action:** Select the gathering-call campaign in the table; scroll the detail panel.

**Point out:**

- How it spread: WhatsApp → X → Facebook → Telegram with times.
- Who started it: first posters and their account age; the most connected amplifiers.
- Why flagged: the score bars (same text within seconds, new accounts, shared link).
- Posts in Hindi, Hinglish and English with platform and town chips.

**Say:**

"A single post looks harmless. Forty accounts, most created days ago, posting the same forward within seconds is not."

## Scene 4: IBM Bob's Assessment

**Action:** Show the IBM Bob section (cached), or press **Ask IBM Bob** if a key is configured.

**Point out:**

- Threat type, severity, target and narrative.
- Planned gathering: place and time. The place must be quoted from a post and the time must be plausible, or the code drops it.
- Legal provisions only from the fixed BNS / IT Act table, marked for legal verification.
- Cited posts are marked in the post list; Bob can only cite posts it was shown.

**Say:**

"IBM Bob reads Hindi and Hinglish and pulls out the where and when. The code checks every field before it is shown."

## Scene 5: Escalation

**Point out:**

- `URGENT`, `ALERT` and `MONITOR` come from fixed rules, never from the AI alone.
- With a planned gathering, actions name the place and time: deploy police before 17:00, issue a public advisory in Hindi and English.
- Actions are recommendations for the SHO to verify, not automatic orders.

## Scene 6: The Benign Decoy

**Action:** Select the cricket-fans campaign.

**Point out:**

- It is coordinated, so it is detected, but it has the lowest score.
- IBM Bob labels it benign coordination; it stays at `MONITOR`.

**Say:**

"Coordination alone is not a crime. The system keeps coordination strength and threat meaning separate."

## Scene 7: The Brief

**Action:** Open **Brief** → **Print or save as PDF**.

**Point out:**

- The planned gathering and lead time at the top.
- Generation timestamp, dataset SHA-256 and per-post evidence hashes.
- How each campaign spread, legal provisions to check, recommended actions, limitations.

**Say:**

"This is what goes to the SHO. Hashes help detect changes, but do not by themselves establish chain of custody or admissibility."

## Closing Statement

"SHIN-CHAN does not predict violence or identify criminals. It gives a cyber cell hours of warning: which coordinated campaign is calling people where, and when, with the evidence to verify it."

## Demo Recovery Lines

### If Bob is unavailable

"Detection, the timeline, the map, scoring and the cached verdicts all work locally. Live classification needs the Bob CLI and API key."

### If the audience asks whether this is real data

"The everyday background posts are real Hindi and English posts from the CONSTRAINT-2021 dataset with made-up accounts and times. The incidents are fictional and use fictional places. We also ran the engine on real research archives (IRA tweets and an X information-operations archive)."

### If the audience asks whether this is real-time

"Uploads are analysed in seconds, and posts can be sent one at a time to the stream API, which re-checks the last 3 hours after each request and raises a provisional alert when a network forms. Replaying the kidnapping pack in 10-minute batches, it raises the rumour network at 11:40, more than six hours before the gathering."

### If the audience asks whether the system identifies bots

"No. It detects coordination patterns. A coordination score is a lead for investigation, not proof that an account is automated or inauthentic."
