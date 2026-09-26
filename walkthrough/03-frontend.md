# 03 — Frontend Walkthrough

## Stack

| Library | Version | Role |
|---|---|---|
| React | 19 | UI framework |
| Vite | 6 | Dev server & bundler |
| Tailwind CSS | v4 | Utility-first styling |
| Cytoscape.js | — | Interactive force-directed graph |
| Lucide React | — | Icon set |

**Entry:** `src/web/src/main.jsx` → renders `<App />` into `#root`

The built output at `src/web/dist/` is served by the FastAPI backend's static file mount at `/`.

---

## API Client: `src/web/src/api.js`

A thin `fetch` wrapper. All calls target `/api/*` on the **same origin** (no hardcoded host/port). This works because the React app is served from the same FastAPI server.

```js
export const api = {
  status:    ()         => req('GET',  '/status'),
  datasets:  ()         => req('GET',  '/datasets/demo'),   // ← hardcoded "demo"
  upload:    (file)     => req('POST', '/datasets', formData),
  analyze:   (id)       => req('POST', `/datasets/${id}/analyze`),
  graph:     (id)       => req('GET',  `/datasets/${id}/graph`),
  timeline:  (id)       => req('GET',  `/datasets/${id}/timeline`),
  campaign:  (id, cid)  => req('GET',  `/datasets/${id}/campaigns/${cid}`),
  classify:  (id, cid)  => req('POST', `/datasets/${id}/campaigns/${cid}/classify`),
  briefUrl:  (id)       =>             `/api/datasets/${id}/brief`,
}
```

> **Hardcoded note:** `api.datasets()` always fetches `/datasets/demo`. This is the only hardcoded dataset name in the API client. See [`04-hardcoded-values.md`](./04-hardcoded-values.md) for the full list.

---

## Root Component: `src/web/src/App.jsx`

All application state lives here. There are **4 tabs**:

| Tab key | What it shows |
|---|---|
| `overview` | StatTiles + TimelineChart + CampaignList |
| `network` | NetworkGraph (Cytoscape) + CampaignPanel |
| `brief` | Embedded BriefView (iframe-like) |
| `upload` | UploadPanel (file upload + dataset selector) |

### State Variables

| State | Type | Description |
|---|---|---|
| `activeTab` | string | Currently visible tab |
| `bobConfigured` | bool | Whether the Bob API key is set (from `/api/status`) |
| `datasets` | array | List of known datasets (currently always `[demo]`) |
| `currentDatasetId` | string | Active dataset ID (starts as `"demo"`) |
| `analyzing` | bool | Analysis spinner flag |
| `analysisResult` | object | Response from `/analyze` call |
| `graphData` | object | `{nodes, edges}` from `/graph` |
| `timelineData` | object | `{bucket_seconds, campaign_ids, points}` from `/timeline` |
| `campaigns` | array | Campaign list extracted from `analysisResult` |
| `selectedCampaignId` | string | Currently selected campaign ID (e.g. `"c1"`) |
| `selectedCampaignDetails` | object | Full campaign object with `sample_posts` |
| `verdicts` | object | Map of `{cid: verdictData}` (cached after Bob classify) |
| `verdictLoading` | bool | Loading spinner for Bob classification |
| `errorBanner` | string | Error message shown at the top (dismissible) |

### Initialization Flow (`useEffect` on mount)

1. `GET /api/status` → sets `bobConfigured`
2. `GET /api/datasets/demo` → sets `datasets`, picks `defaultId = datasets[0].id`
3. Calls `loadDatasetArtifacts(defaultId)` → loads graph + timeline

### `loadDatasetArtifacts(dsId)`

Parallel fetches `graph` and `timeline`. If the demo dataset is marked `analyzed`, silently pre-fetches campaign `c1` and auto-selects it.

### `handleSelectCampaign(cid)`

1. Fetches full campaign details (with `sample_posts`) from `/campaigns/:cid`
2. Silently calls `/classify` to retrieve cached Bob verdict if not already in state

### `activeCampaignList` — The Key Derived Value

```js
const activeCampaignList = analysisResult?.campaigns || (graphData ? [
  { id: 'c1', size: 25, score: 92, top_hashtag: '#SundarpurExposed', signals: ['co_link', ...] },
  { id: 'c2', size: 40, score: 89, top_hashtag: '#SundarpurAlert',   signals: ['co_similar_tweet', ...] },
  { id: 'c3', size: 30, score: 88, top_hashtag: '#FakeNewsExposed',  signals: ['co_reply', ...] }
] : [])
```

> **⚠️ HARDCODED FALLBACK:** If `analysisResult` is null but `graphData` is loaded (which is the case on first load of the demo), the campaign list is built from these three hardcoded objects. They match the demo dataset exactly but **will not reflect any other dataset**. See [`04-hardcoded-values.md`](./04-hardcoded-values.md).

---

## Components

### `Navbar.jsx`
Renders the top navigation bar with 4 tab buttons and a Bob status indicator. Props: `activeTab`, `setActiveTab`, `bobConfigured`, `selectedDataset`.

### `StatTiles.jsx`
4 summary tiles: Ingested Posts, Monitored Accounts, Coordinated Rings, Peak CIB Risk Score. All values are passed as props from `App.jsx` — no hardcoding here.

### `TimelineChart.jsx`
SVG-based area chart showing per-minute post activity with per-campaign colored overlays. Accepts `timelineData` from the backend. Handles no-data gracefully.

### `CampaignList.jsx`
Renders one card per campaign with: campaign ID badge, top hashtag, account count, median age, signal badges, CIB score, "Inspect" button. Score color bands:
- **Red** (`bg-red-500`) — score ≥ 80
- **Amber** — score ≥ 60
- **Green** — below 60

### `NetworkGraph.jsx`
Renders the Cytoscape.js force-directed graph.

**Hardcoded elements:**
- `CAMPAIGN_COLORS` — fixed color mapping for `c1`–`c5`
- Graph legend labels: "Campaign C1 (Link Ring)", "Campaign C2 (Rumour Ring)", "Campaign C3 (Harassment Pile-on)"

These labels are specific to the demo Sundarpur scenario. See [`04-hardcoded-values.md`](./04-hardcoded-values.md).

### `CampaignPanel.jsx`
Side panel showing: CIB risk score, account count, top hashtag, median age, feature contribution bars (with fixed `max` values matching `WEIGHTS` in the backend), `VerdictCard`, and sample evidence posts.

`featureLabels` maps backend keys to human labels and max point values — these match `WEIGHTS` in `src/engine/scoring.py` exactly.

### `VerdictCard.jsx`
Renders the Bob verdict. Three states:
1. **Loading** — spinner with pulsing animation
2. **Empty** — prompt to "Ask IBM Bob" with a button
3. **Verdict** — threat type, severity, target, narrative, offline CTA alert, legal sections (BNS/IPC), escalation level & actions, cited evidence post IDs

### `UploadPanel.jsx`
File upload dropzone and dataset selector. Calls `api.upload()` and `api.analyze()`.

### `BriefView.jsx`
Embeds the HTML brief from `GET /api/datasets/:id/brief`. Opens in a new tab or renders inline.
