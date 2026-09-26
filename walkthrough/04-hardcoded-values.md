# 04 — Hardcoded Values in the Frontend (What to Change)

This document lists **every hardcoded value** in the frontend that is specific to the demo "Sundarpur" dataset. When you load a different dataset these values will either show stale demo data or break the display. Each entry tells you exactly where the value is and what to change.

---

## 1. Hardcoded Campaign Fallback List

**File:** [`src/web/src/App.jsx`](../src/web/src/App.jsx) — **line 166**

```js
const activeCampaignList = analysisResult?.campaigns || (graphData ? [
  { id: 'c1', size: 25, score: 92, top_hashtag: '#SundarpurExposed', signals: ['co_link', 'co_similar_tweet', 'co_tweet'] },
  { id: 'c2', size: 40, score: 89, top_hashtag: '#SundarpurAlert',   signals: ['co_similar_tweet', 'co_tweet'] },
  { id: 'c3', size: 30, score: 88, top_hashtag: '#FakeNewsExposed',  signals: ['co_reply', 'co_similar_tweet', 'co_tweet'] }
] : [])
```

**Why it's there:** On first load the demo dataset is pre-analyzed and `graphData` arrives before `analysisResult` is populated (no `/analyze` call has been made). This fallback gives the UI something to render in `CampaignList` immediately.

**Problem:** For any non-demo dataset this fallback shows the wrong campaigns (Sundarpur hashtags/sizes).

**Fix:** Load campaigns from the backend when a dataset is selected. The `/api/datasets/:id/analyze` endpoint already returns the campaigns array. The cleaner solution is to also expose the campaigns list from `GET /api/datasets/:id/campaigns` (or read it from `campaigns.json` via a new route) so the fallback is populated from real data:

```js
// In loadDatasetArtifacts(), add:
const campsData = await api.campaigns(dsId).catch(() => null)
if (campsData) setCampaigns(campsData)

// In api.js, add:
campaigns: (id) => req('GET', `/datasets/${id}/campaigns`),
```

And in the backend (`src/api/main.py`), add:
```python
@app.get("/api/datasets/{dataset_id}/campaigns")
def list_campaigns(dataset_id: str):
    path = RUNS / dataset_id / "campaigns.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Not analyzed yet")
    with open(path, encoding="utf-8") as f:
        return json.load(f)
```

Then replace the hardcoded fallback in `App.jsx` with:
```js
const activeCampaignList = analysisResult?.campaigns || campaigns
```

---

## 2. Hardcoded Default Post Count Fallback

**File:** [`src/web/src/App.jsx`](../src/web/src/App.jsx) — **line 171**

```js
const postsTotal    = analysisResult?.posts    || (datasets[0]?.posts    || 4538)
const accountsTotal = analysisResult?.accounts || (datasets[0]?.accounts || 956)
```

**Why it's there:** `4538` and `956` are the exact post/account counts of the Sundarpur demo dataset. If `datasets[0]` hasn't loaded yet, these hardcoded numbers appear in `StatTiles`.

**Problem:** Any other dataset will momentarily flash the demo counts before the real API response loads.

**Fix:** Default to `0` instead:

```js
const postsTotal    = analysisResult?.posts    || datasets[0]?.posts    || 0
const accountsTotal = analysisResult?.accounts || datasets[0]?.accounts || 0
```

---

## 3. Hardcoded Default CIB Score Fallback

**File:** [`src/web/src/App.jsx`](../src/web/src/App.jsx) — **line 173**

```js
const maxScore = activeCampaignList.length > 0
  ? Math.max(...activeCampaignList.map((c) => c.score))
  : 92
```

**Why it's there:** `92` is the top CIB score in the Sundarpur demo. If `activeCampaignList` is empty the stat tile would show `0`, which looks broken. The hardcoded `92` prevents that.

**Problem:** When `activeCampaignList` is genuinely empty (e.g. a new unanalyzed dataset), the score tile shows `92` instead of `0`.

**Fix:** After fixing issue #1 (so `activeCampaignList` is populated from the backend), this fallback is no longer needed. Change to:

```js
const maxScore = activeCampaignList.length > 0
  ? Math.max(...activeCampaignList.map((c) => c.score))
  : 0
```

---

## 4. Hardcoded `"demo"` Dataset in API Client

**File:** [`src/web/src/api.js`](../src/web/src/api.js) — **line 26**

```js
datasets: () => req('GET', '/datasets/demo'),
```

**Why it's there:** The backend currently has a single hardcoded demo route `GET /api/datasets/demo`. Supporting multiple datasets would require `GET /api/datasets` (list all).

**Problem:** `api.datasets()` always fetches the demo metadata. After a user uploads a new dataset, calling `api.datasets()` won't include it in the returned list.

**Fix:** Add a `GET /api/datasets` route to the backend that returns all runs:

```python
# In src/api/main.py
@app.get("/api/datasets")
def list_all_datasets():
    datasets = []
    if RUNS.exists():
        for run_dir in sorted(RUNS.iterdir()):
            if run_dir.is_dir():
                campaigns_exist = (run_dir / "campaigns.json").exists()
                posts_path = run_dir / "posts.json"
                post_count, acc_count = 0, 0
                if posts_path.exists():
                    try:
                        data = json.loads(posts_path.read_text("utf-8"))
                        post_count = len(data)
                        acc_count = len({p["account_id"] for p in data})
                    except Exception:
                        pass
                datasets.append({
                    "id": run_dir.name,
                    "name": run_dir.name,
                    "posts": post_count,
                    "accounts": acc_count,
                    "analyzed": campaigns_exist,
                })
    return datasets
```

Then update `api.js`:
```js
datasets: () => req('GET', '/datasets'),
```

---

## 5. Hardcoded Campaign Graph Legend Labels

**File:** [`src/web/src/components/NetworkGraph.jsx`](../src/web/src/components/NetworkGraph.jsx) — **lines 194–211**

```jsx
<div className="flex items-center gap-2 text-slate-300">
  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CAMPAIGN_COLORS.c1 }}></span>
  Campaign C1 (Link Ring)
</div>
<div className="flex items-center gap-2 text-slate-300">
  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CAMPAIGN_COLORS.c2 }}></span>
  Campaign C2 (Rumour Ring)
</div>
<div className="flex items-center gap-2 text-slate-300">
  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CAMPAIGN_COLORS.c3 }}></span>
  Campaign C3 (Harassment Pile-on)
</div>
```

**Why it's there:** Labels are manually written to match the Sundarpur demo campaigns.

**Problem:** These descriptions are wrong for any other dataset. A dataset with 5 campaigns won't show C4/C5 in the legend either.

**Fix:** Generate the legend dynamically from `activeCampaignList` passed as a prop:

```jsx
// Add prop: campaigns
export function NetworkGraph({ graphData, selectedCampaignId, onSelectCampaign, campaigns = [] }) {
  // ...

  // In the legend section replace the hardcoded items with:
  {campaigns.map((camp) => (
    <div key={camp.id} className="flex items-center gap-2 text-slate-300">
      <span
        className="w-2.5 h-2.5 rounded-full"
        style={{ backgroundColor: CAMPAIGN_COLORS[camp.id] || '#6366f1' }}
      />
      Campaign {camp.id.toUpperCase()} {camp.top_hashtag ? `(${camp.top_hashtag})` : ''}
    </div>
  ))}
  <div className="flex items-center gap-2 text-slate-400">
    <span className="w-2.5 h-2.5 rounded-full bg-slate-600" />
    Background Noise
  </div>
```

And pass the prop in `App.jsx`:
```jsx
<NetworkGraph
  graphData={graphData}
  selectedCampaignId={selectedCampaignId}
  onSelectCampaign={(cid) => handleSelectCampaign(cid)}
  campaigns={activeCampaignList}   {/* ← add this */}
/>
```

---

## 6. Hardcoded Campaign Color Map (Only 5 Entries)

**File:** [`src/web/src/components/NetworkGraph.jsx`](../src/web/src/components/NetworkGraph.jsx) — **lines 5–11**

```js
const CAMPAIGN_COLORS = {
  c1: '#8b5cf6',
  c2: '#ec4899',
  c3: '#f59e0b',
  c4: '#10b981',
  c5: '#06b6d4',
}
```

**Problem:** A dataset with more than 5 campaigns will render all extra clusters in the default `#6366f1` indigo color with no legend entry.

**Fix:** Extend the list (add more colors) or generate colors programmatically:

```js
const BASE_COLORS = ['#8b5cf6','#ec4899','#f59e0b','#10b981','#06b6d4','#f87171','#34d399','#60a5fa','#a78bfa','#fb923c']

// Utility to get color for any campaign ID
function getCampaignColor(campId) {
  // c1 → index 0, c2 → index 1, etc.
  const match = campId.match(/\d+$/)
  const idx = match ? (parseInt(match[0], 10) - 1) : 0
  return BASE_COLORS[idx % BASE_COLORS.length]
}
```

---

## 7. Auto-Selection of Campaign `"c1"` on Demo Load

**File:** [`src/web/src/App.jsx`](../src/web/src/App.jsx) — **lines 70–77**

```js
api.campaign(dsId, 'c1')
  .then((camp1) => {
    if (camp1) {
      setSelectedCampaignId('c1')
      setSelectedCampaignDetails(camp1)
    }
  })
  .catch(() => {})
```

**Why it's there:** Auto-selects the highest-risk campaign when the demo loads so the UI is immediately populated.

**Problem:** For a non-demo dataset that has been analyzed, this still tries to fetch `c1`. This works only if the new dataset also has a campaign named `c1` (which it will, since campaigns are always named c1, c2, ... by the engine). However, it's better to auto-select the first campaign from the actual campaign list rather than hardcoding the ID.

**Fix:** After fetching the campaign list, auto-select the first one:

```js
const campsData = await api.campaigns(dsId).catch(() => null)
if (campsData && campsData.length > 0) {
  setCampaigns(campsData)
  const topCid = campsData[0].id
  const camp = await api.campaign(dsId, topCid).catch(() => null)
  if (camp) {
    setSelectedCampaignId(topCid)
    setSelectedCampaignDetails(camp)
  }
}
```

---

## Summary Table

| # | File | Line(s) | Hardcoded Value | Impact |
|---|---|---|---|---|
| 1 | `App.jsx` | 166–169 | Campaign objects (id, size, score, hashtag, signals) | Wrong campaigns shown for any non-demo dataset |
| 2 | `App.jsx` | 171 | `4538` posts, `956` accounts | Wrong counts shown momentarily |
| 3 | `App.jsx` | 173 | `92` (max CIB score fallback) | Wrong score shown when no campaigns loaded |
| 4 | `api.js` | 26 | `'/datasets/demo'` | Uploaded datasets not listed |
| 5 | `NetworkGraph.jsx` | 194–211 | Legend labels (Link Ring, Rumour Ring, Harassment Pile-on) | Wrong names for any other dataset |
| 6 | `NetworkGraph.jsx` | 5–11 | Color map limited to c1–c5 | Datasets with 6+ campaigns get same color |
| 7 | `App.jsx` | 70–77 | `'c1'` auto-selection | Minor: works but relies on engine always naming top campaign c1 |
