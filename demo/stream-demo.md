# Stream API Demo (mock posts)

This walkthrough demonstrates the rolling-window API with fictional posts. It does not contact a platform, predict violence, or classify accounts as bots.

## Start

Build the frontend if needed, then start the local server from the repository root:

```bash
python src/main.py
```

The default bind address is `127.0.0.1`. The prototype has no authentication; do not expose it on a public or shared network.

## Baseline And Burst

In a second Linux/macOS terminal, paste this block. It creates a fresh stream, adds unrelated baseline posts, then sends two repeated waves from five accounts. The repeated waves satisfy the toolkit's configured minimum edge weight.

```bash
BASE=http://127.0.0.1:8000/api/streams
STREAM_ID="mock-incident-$(date +%s)"
NOW=$(date +%s)

curl -fsS -X POST "$BASE/$STREAM_ID/posts" -H 'Content-Type: application/json' \
  -d "{\"post_id\":\"base-1\",\"account_id\":\"local-1\",\"created_at\":$NOW,\"text\":\"Fictional weather update for Maple District.\"}"
curl -fsS -X POST "$BASE/$STREAM_ID/posts" -H 'Content-Type: application/json' \
  -d "{\"post_id\":\"base-2\",\"account_id\":\"local-2\",\"created_at\":$((NOW + 1)),\"text\":\"The library will close early today.\"}"

for wave in 1 2; do
  for i in 1 2 3 4 5; do
    curl -fsS -X POST "$BASE/$STREAM_ID/posts" -H 'Content-Type: application/json' \
      -d "{\"post_id\":\"burst-$wave-$i\",\"account_id\":\"fictional-$i\",\"created_at\":$((NOW + wave * 10 + i + 2)),\"text\":\"Unverified notice: meet at fictional Maple Hall at 19:00 for a public discussion. #MapleNotice\",\"urls\":[\"https://example.invalid/maple-notice\"]}"
  done
done

curl -fsS "$BASE/$STREAM_ID/alerts"
curl -fsS "$BASE/$STREAM_ID/timeline"
```

Each post response includes a provisional alert snapshot with `window_started_at`, `window_ended_at`, `last_updated_at`, `window_posts`, and any detected coordination campaigns. The two repeated waves are verified to produce a campaign with the bundled toolkit settings. Campaign appearance indicates coordination signals only, not harmful intent. Reposting the same `post_id` and content is idempotent. Reusing an ID for changed content returns `409`.

The body can also be a JSON array of posts; the whole array is checked with one rebuild. Each rebuild takes 5–8 seconds on a laptop whatever the number of posts (the toolkit starts a process pool for each of its five networks), so for replays send posts in batches, for example one request per minute of posts.

Close the stream when finished:

```bash
curl -fsS -X POST "$BASE/$STREAM_ID/close"
```

## Operational Boundaries

- Stream posts are normalized individually and kept in SQLite using event-time retention. Late posts are accepted; the window watermark is the greatest event timestamp received.
- The graph is recomputed from the current window after each request (5–8 seconds). Co-actions count only within `TIME_WINDOW_SECONDS` (60 s), as in batch analysis; the 3-hour stream window (`STREAM_WINDOW_SECONDS`) only limits which posts are checked. A 15-minute window is too short: the demo incidents coordinate in bursts spread over hours and were never flagged. This is intentionally simple and unsuitable for high-volume production streams.
- The current process-local lock does not coordinate multiple application workers. Use one worker for this demo.
- Alerts expire from the event-time window when later event timestamps arrive; there is no independent wall-clock expiry task.
- The stream API emits coordination-only alerts. It does not invoke IBM Bob, extract offline indicators, or create a final case/brief.
- No identity provider, role authentication, platform connector, queue, service-level objective, or operational retention/legal policy is included.
- Use synthetic data only. Legal references and evidence hashes are review aids, not legal conclusions or proof of admissibility.