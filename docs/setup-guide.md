# Setup Guide: Social Media Threat Intelligence Engine

> Complete instructions to set up and run the project locally on Windows, macOS or Linux.

---

## Prerequisites

Before you begin, ensure you have the following installed on your machine:

- **Python 3.10+**
- **pip** (Python package manager)
- **Git**
- **Node.js 24+** with npm (required by IBM Bob Shell and to build the React frontend)
- **IBM Bob Shell** — install from [bob.ibm.com/download](https://bob.ibm.com/download), then run `bob` once and sign in with your IBMid
- **An IBM Bob API key** — needed for live Bob analysis (see below)

### Getting an IBM Bob API key

1. Sign in at [bob.ibm.com](https://bob.ibm.com) and open your subscription instance.
2. Go to **API keys** → **Create**. Choose the **Inference** type (it can only run inference, so it is the safer choice).
3. Copy the key immediately — it is shown only once.
4. Put it in `src/.env` as `BOB_API_KEY=...` (next section).

Headless `bob run` requires a key even when Bob Shell is signed in. Never commit the key or paste it into chats; `src/.env` is already in `.gitignore`.

**No key?** The app still runs: detection, scoring, the network graph and escalation work, and Bob's saved results are shown for campaigns already assessed. Only new Bob analysis needs a key.

---

## Environment Variables

Copy the template environment file to `.env`:

```bash
cp src/.env.example src/.env
```

On Windows (PowerShell): `Copy-Item src/.env.example src/.env`

| Variable | Description | Required |
|---|---|---|
| `BOB_API_KEY` | IBM Bob API key for headless `bob run` (threat analysis and brief summary) | Yes for live Bob analysis; without it the app uses cached verdicts |
| `BOB_MAX_COST` | Bobcoin cap per Bob call | Optional (Default: 0.25; one call measured at ~0.025) |
| `APP_PORT` | Application server port | Optional (Default: 8000) |
| `APP_HOST` | Bind address | Optional (Default: 127.0.0.1) |
| `APP_ENV` | Application environment (`development` / `production`) | Optional |
| `APP_AUTH_USERNAME` / `APP_AUTH_PASSWORD` | HTTP Basic Auth credentials required in production mode | Required in production |
| `TIMEZONE` | Timezone for brief timestamps | Optional (Default: Asia/Kolkata) |
| `TIME_WINDOW_SECONDS` | Coordination time window | Optional (Default: 60) |
| `MIN_EDGE_WEIGHT` | Minimum times two accounts must coordinate | Optional (Default: 2) |
| `STREAM_WINDOW_SECONDS` | Event-time window for provisional stream alerts | Optional (Default: 10800, 3 hours) |
| `STREAM_RETENTION_SECONDS` | How long stream posts are kept (event time) | Optional (Default: 86400) |
| `X_BEARER_TOKEN` | X API token for **Datasets → Search X** (plan must include recent search) | Optional |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Tirth-chokshi/social-threat-intel-engine.git
cd social-threat-intel-engine
```

### 2. Configure Environment

Copy `src/.env.example` to `src/.env` (see above) and add your `BOB_API_KEY`.

### 3. Install Dependencies

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r src/requirements.txt
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r src/requirements.txt
```

### 4. Build the Frontend (React)

```bash
cd src/web
npm ci
npm run build
cd ../..
```

This creates `src/web/dist/`, which the Python app serves. Re-run `npm run build` after pulling frontend changes.

### 5. Check IBM Bob

```bash
bob --version
```

Should print `2.0.x` or later. A warning about system certificates means Node.js is older than 24.

---

## Running the Application

**macOS / Linux:**

```bash
source .venv/bin/activate
python src/main.py
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
python src/main.py
```

Open **http://127.0.0.1:8000** in your browser.

### Frontend development mode (for contributors)

Run the Python app as above, then in a second terminal:

```bash
cd src/web
npm run dev
```

Open **http://localhost:5173** — changes reload instantly and `/api` calls are proxied to the Python app on port 8000.

### Verify it works

1. The app starts empty on **Datasets**. Upload X API v2 JSON (try `src/web/public/x-api-v2-example.json`) or search X. The analysis starts automatically and shows each step.
2. **Overview** opens with a summary paragraph of what was found, any planned gatherings IBM Bob has extracted, the incident timeline and the campaign table. Select a campaign: the detail panel shows how it spread, who started it and why it was flagged.
3. Press **Ask IBM Bob** on a campaign for its threat type, target, severity, any call to gather and legal sections to check (needs the key).
4. **Network** shows who coordinated with whom; the accounts that started a campaign have a thick ring.
5. **Posts** lists every post; click any account, hashtag or town (here or in the campaign panel) to filter to it.
6. **Brief** → **Print or save as PDF** produces the time-stamped threat brief.

Posts can also be sent one at a time to the rolling-window stream API (`/api/streams/{id}/posts`), which returns a provisional coordination alert after each post; see [`../demo/stream-demo.md`](../demo/stream-demo.md). It rebuilds the graph from the window on every post, so it suits a local demonstration, not production volumes.

The local development default binds to `127.0.0.1` and has no login. Do not expose it on a public or shared network. Production mode requires the authentication variables below and fails closed without them.

For a protected Render demo deployment, follow [`deployment.md`](deployment.md). Production mode requires `APP_AUTH_USERNAME` and `APP_AUTH_PASSWORD` and fails closed if either is missing.

---

## Using Your Own Data

Upload **X API v2 JSON** on the **Datasets** page, exactly as the API returned it: a search, timeline or lookup response, a list of them, one per line, or filtered-stream lines. Each post needs `created_at` and `author_id` (`tweet.fields=created_at,author_id`); the recommended fields, an example and the database layout are in [`data-model.md`](data-model.md).

Text-only datasets (for example CONSTRAINT or HASOC) have no account or time and are rejected with a message saying what is missing.

---

### Datasets

The app ships without data. Collect posts with the X API v2 (recent or full-archive search, user timelines, filtered
stream) using the fields in [`data-model.md`](data-model.md), save the responses unchanged as `.json` or `.jsonl`, and
upload them. `python src/eval/measure.py` analyses every X API v2 file in `data/raw` and writes `src/eval/results.md`.

## Using the Bob Investigation Console (MCP)

After a dataset has been analysed in the web app:

1. Open a terminal in the repository root.
2. Run `bob chat` (signed in with your IBMid).
3. Switch mode: `/mode osint-analyst`.
4. Check the tools: `/mcp` should list the `threat-intel` server (configured in `.bob/mcp.json`).
5. Ask, for example: *"List my datasets, then the campaigns in the newest one, and tell me which accounts started campaign 1."*

The MCP server is read-only: it can only read analysis results from `data/runs/`.

---

## Running the Tests

```bash
python -m pytest src/tests
```

The engine test builds a small post batch at test time (`src/tests/fixtures.py`: ordinary posters plus two planted rings) and checks that both rings are found, nothing else is, and no ordinary poster is clustered. Nothing is stored or shown in the app.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Missing dependencies | Activate `.venv` and run `python -m pip install -r src/requirements.txt` |
| Python version error | Ensure Python 3.10+ is installed and active in your terminal |
| `Bob API key is required` | Set `BOB_API_KEY` in `src/.env` and restart the app |
| Header says "IBM Bob: saved results only" | Live assessments need both `BOB_API_KEY` in `src/.env` and Bob Shell on the backend's PATH (`bob --version`); until then saved results are shown |
| Bob warns about system certificates | Update Node.js to v24 (`winget install OpenJS.NodeJS.LTS` on Windows) |
| `bob` not found | Reinstall Bob Shell and open a new terminal so `PATH` is refreshed |
| `/mcp` does not show `threat-intel` | Start `bob chat` from the repository root so `.bob/mcp.json` is picked up |
| PowerShell blocks `Activate.ps1` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once |
| Browser shows "Frontend not built" or a blank page | Run `npm ci && npm run build` in `src/web`, then restart the app |
| `npm ci` fails | Check `node --version` is 24+; delete `src/web/node_modules` and retry |
