# Design System: "Case File"

The Command Center is a work tool for a cyber cell officer. It is used under time pressure, often on a projector or in a briefing, and what it shows may end up as evidence. The design language follows from that.

## Principles

1. **Calm by default, loud only for risk.** The interface is neutral grey. Colour is reserved for two things: how urgent something is (severity), and which campaign a point or account belongs to. If everything is highlighted, nothing is.
2. **Plain words.** "Posted within seconds of each other", not "temporal velocity". Technical names (co-tweet, Louvain) appear only in tooltips and docs.
3. **Evidence first.** Every claim links to the posts behind it. IDs, hashes, times and counts use a monospace font so they can be read out and copied exactly.
4. **Always say what the system is doing.** Loading, empty, running (with the current step), failed (with the reason and what to do next). The screen is never blank or silently stuck.
5. **One obvious next action per screen.** There is at most one primary (filled) button in view.
6. **Decision support, not verdicts.** AI output is labelled as IBM Bob's assessment, and legal sections always say "verify with a legal officer".

## Tokens

All colours are CSS variables in `src/web/src/index.css`, with a light and a dark value. The first visit follows the operating system setting; the sun/moon button in the header switches theme and the choice is remembered. Components use only these tokens, never raw colours.

| Token | Use | Light | Dark |
|---|---|---|---|
| `bg` | page background | `#f6f7f9` | `#0d1015` |
| `surface` | cards, header | `#ffffff` | `#151a21` |
| `subtle` | hover, table header, inset areas | `#f0f2f5` | `#1c222b` |
| `line` | borders, dividers | `#e2e5ea` | `#29303b` |
| `ink` | main text | `#15181d` | `#e7e9ec` |
| `muted` | secondary text | `#5c6470` | `#9aa3ae` |
| `faint` | captions, placeholders, background graph nodes | `#8b929c` | `#687180` |
| `accent` | primary buttons, links, focus, selection | `#2456d6` | `#7ea3ff` |

**Severity** is the only loud colour. Each level has a text/foreground colour and a soft background.

| Level | Meaning | Colour |
|---|---|---|
| `urgent` | Act now (incitement with a call to gather, or high score and severity) | red |
| `alert` | Log and monitor closely | amber |
| `monitor` | Routine watch | blue-grey |
| `benign` | Assessed as harmless | green |
| pending | Not assessed by IBM Bob yet | neutral, dashed outline |

**Campaign colours** are the Okabe–Ito colour-blind-safe set, in rank order: c1 `#0072B2`, c2 `#D55E00`, c3 `#009E73`, c4 `#CC79A7`, c5 `#E69F00`, c6 `#56B4E9`, c7 `#8C564B`, c8+ `#7F7F7F`. The same campaign has the same colour in the table, timeline and graph.

## Type

- UI font: IBM Plex Sans (with Plex Sans Devanagari for Hindi) and IBM Plex Mono, bundled with the app through @fontsource, so the tool still works offline.
- Mono: `ui-monospace, "Cascadia Mono", Consolas, monospace` for IDs, hashes, times and numbers in tables.
- Sizes: 12 px captions and labels, 14 px body, 16 px card titles, 20 px page titles, 28 px key numbers.
- Weights: 400 body, 500 labels, 600 titles. No all-caps paragraphs; small caps-style labels (12 px, 500, letter-spaced) only for section labels.

## Shape and space

- 4 px grid. Card padding 16 px (20 px on wide screens), gaps of 16 or 24 px.
- Radius: 8 px for cards, 6 px for buttons and inputs, full for pills.
- 1 px `line` borders separate things. Shadows only on things that float (menus).
- Content width up to 1440 px.

## Layout: what goes where

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ▣ Social-Threat Intel Engine  Datasets Overview Network Brief  [dataset ▾] ● IBM Bob ☾ │  header
├──────────────────────────────────────────────────────────────────────────┤
│ Page title + one-line context                         [primary action]  │
│                                                                          │
│ page content                                                             │
└──────────────────────────────────────────────────────────────────────────┘
```

| Page | Purpose | Content |
|---|---|---|
| **Datasets** | Bring data in, see what is ready | Upload box (X API v2 JSON only, with an example response to download) and Search X box (left); table of datasets with posts, accounts, ingestion warnings, status (Not analysed / Analysing step n of 9 / Ready / Failed) and actions |
| **Overview** | Triage: what needs attention | One summary paragraph written from the data (what the dataset is, what was found, what to do next) → emerging offline threats (where, when, time left, flagged how early) → incident timeline → campaign table and "Where it spread" map (left) with the selected campaign's detail (right) |
| **Network** | See who coordinates with whom | Graph (left) with legend and zoom controls, the same campaign detail panel (right) |
| **Posts** | Check the evidence yourself | Drawn like x.com, in X's own palette (light, and Dim in the dark theme): search filters (post type, campaign, platform, language, location) · timeline with Top / Latest / Oldest tabs · search, trends and most active accounts. Each post: avatar, name, verified, @handle, time, "… reposted" and "Coordinated campaign C1" lines above, "Replying to @x", links and hashtags in X blue, quoted-post card, media markers, reply/repost/like/views bar. Opening a post shows the conversation above it and its replies, reposts and quotes. Counts are the platform's when the source has them, otherwise those found in the dataset (the tooltip says which); none are ever estimated. Profile photos are not fetched; a letter stands in |
| **Brief** | Hand over | Toolbar (open, print) and the printable brief |

A dataset that is not analysed, or is being analysed, shows the same state card on Overview, Network and Brief: the reason, the progress, and the one action to take.

**Campaign detail panel** (identical on Overview and Network), top to bottom:
1. Identity: colour dot, campaign ID, main hashtag, level; accounts, posts, active period; platform and language chips.
2. Call to gather (if IBM Bob found one): place, day and time, and the words the posts used.
3. How it spread: platform stepper and town stepper with times; spread speed, share of new accounts, when it was flagged.
4. Who started it: seed account cards (platform, time, town, account age); most connected accounts.
5. Why it was flagged: the score bars in plain words.
6. IBM Bob assessment: escalation level first, then threat type, target, narrative, place- and time-specific actions, legal suggestions (marked for verification). If not assessed yet: an explanation and the **Ask IBM Bob** button.
7. Posts sampled across the campaign, oldest first, with platform, town and language; posts Bob cited are marked.

**Times and languages.** Every time is shown in the dataset's clock (`labels.js: setDisplayZone`), with the zone named once per view ("times in IST"). Timeline buckets are sizes a person would pick (5 minutes, an hour, a day) and ticks fall on round local hours or days; marker labels add the date when the data spans days. Languages are shown by name (`langLabel`, the browser's own language names for anything beyond हिंदी / Hinglish / English). Sections a dataset has no data for are left out or reduced to one line saying so, never shown empty.

**Visual story components** (`src/web/src/components/`): `Summary` (the paragraph at the top of the Overview), `ThreatCards` (the hero: one card per planned gathering), `IncidentTimeline` (stacked activity by campaign with ● first post, ▲ flagged, ■ peak, ⚑ gathering and a lead-time bracket), `SpreadPath` (platform/town stepper), `SpreadMap` (stylised district map: towns numbered in the order reached, ⚑ at the gathering), `Chips` (WA / X / FB / TG / IG and हिंदी / Hinglish / English). The same campaign colour and severity colours are used in all of them.

## Components

`Button` (primary / secondary / ghost / danger), `Card`, `Badge` (severity and status), `Stat`, `StateCard` (empty, running with steps, error), `Banner` (page-level error), `ScoreBar`. They live in `src/web/src/ui.jsx`.

## Copy

- Sentence case everywhere ("Ask IBM Bob", not "ASK IBM BOB").
- Say what happens and how long: "Analysing… step 4 of 10: similar text. Large files take several minutes."
- Errors say what went wrong and what to do: "IBM Bob is not configured. Add BOB_API_KEY to src/.env and restart the app."
- Numbers are formatted with separators (243,891) and units (posts, accounts).
