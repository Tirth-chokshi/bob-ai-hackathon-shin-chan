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

All colours are CSS variables in `src/web/src/index.css`, with a light and a dark value. The dark values follow the operating system setting. Components use only these tokens, never raw colours.

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

- UI font: the system font stack (no web fonts: the tool must work offline).
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
│ ▣ Threat Intel Engine   Datasets  Overview  Network  Brief    [dataset ▾]  ● IBM Bob │  header
├──────────────────────────────────────────────────────────────────────────┤
│ Page title + one-line context                         [primary action]  │
│                                                                          │
│ page content                                                             │
└──────────────────────────────────────────────────────────────────────────┘
```

| Page | Purpose | Content |
|---|---|---|
| **Datasets** | Bring data in, see what is ready | Upload box (formats listed), table of datasets with posts, accounts, status (Not analysed / Analysing step n of 10 / Ready / Failed) and actions (Open, Analyse, Delete) |
| **Overview** | Triage: what needs attention | 4 key numbers → activity timeline → campaign table (left) with the selected campaign's detail (right) |
| **Network** | See who coordinates with whom | Graph (left) with legend and zoom controls, the same campaign detail panel (right) |
| **Brief** | Hand over | Toolbar (open, print) and the printable brief |

A dataset that is not analysed, or is being analysed, shows the same state card on Overview, Network and Brief: the reason, the progress, and the one action to take.

**Campaign detail panel** (identical on Overview and Network), top to bottom:
1. Identity: colour dot, campaign ID, main hashtag; accounts, posts, active period.
2. Coordination score with the "why flagged" bars in plain words.
3. IBM Bob assessment: escalation level first, then threat type, target, narrative, call-to-gather warning, recommended actions, legal suggestions (marked for verification), cited evidence. If not assessed yet: an explanation and the **Ask IBM Bob** button.
4. First posts, oldest first; posts Bob cited are marked.

## Components

`Button` (primary / secondary / ghost / danger), `Card`, `Badge` (severity and status), `Stat`, `StateCard` (empty, running with steps, error), `Banner` (page-level error), `ScoreBar`. They live in `src/web/src/ui.jsx`.

## Copy

- Sentence case everywhere ("Ask IBM Bob", not "ASK IBM BOB").
- Say what happens and how long: "Analysing… step 4 of 10: similar text. Large files take several minutes."
- Errors say what went wrong and what to do: "IBM Bob is not configured. Add BOB_API_KEY to src/.env and restart the app."
- Numbers are formatted with separators (243,891) and units (posts, accounts).
