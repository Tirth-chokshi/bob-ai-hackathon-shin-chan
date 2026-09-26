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

**No key?** The app still runs: detection, scoring, the network graph and escalation work, and Bob's results are shown from the cache for the bundled demo run. Only new Bob analysis needs a key.

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
| `TIMEZONE` | Timezone for brief timestamps | Optional (Default: Asia/Kolkata) |
| `TIME_WINDOW_SECONDS` | Coordination time window | Optional (Default: 60) |
| `MIN_EDGE_WEIGHT` | Minimum times two accounts must coordinate | Optional (Default: 2) |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Tirth-chokshi/bob-ai-hackathon-shin-chan.git
cd bob-ai-hackathon-shin-chan
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

1. The app opens on **Overview** for the demo dataset: 4 campaigns ranked by coordination score, with 3 marked Urgent. The cricket decoy (C4) ranks lowest and is marked Monitor.
2. Select a campaign: the panel shows why it was flagged, IBM Bob's saved assessment and its first posts.
3. **Network** shows the same campaigns as a graph; click a dot to open its campaign.
4. **Brief** → **Print or save as PDF** produces the time-stamped threat brief.
5. Optional: **Datasets** → upload a CSV (for example `data/raw/ira_1.csv`). The analysis starts automatically and shows each step; the full IRA file takes about 5 minutes.

---

## Using Your Own Data

Upload a CSV or JSON on the **Datasets** page. Each row is one post and needs three things: the account that posted it, the time, and the text. Column names are recognised automatically (`user_id`, `author`, `timestamp`, `content`, …), no cleaning is needed, and links and hashtags are taken from the text when there is no column for them. Full list of accepted columns and time formats: [`data-format.md`](data-format.md). Template: `src/web/public/posts-template.csv`.

Text-only datasets (for example CONSTRAINT or HASOC) have no account or time and are rejected with a message saying what is missing.

---

## Using the Bob Investigation Console (MCP)

After a dataset has been analysed in the web app:

1. Open a terminal in the repository root.
2. Run `bob chat` (signed in with your IBMid).
3. Switch mode: `/mode osint-analyst`.
4. Check the tools: `/mcp` should list the `threat-intel` server (configured in `.bob/mcp.json`).
5. Ask, for example: *"List the campaigns in the demo dataset and tell me which accounts started campaign 1."*

The MCP server is read-only: it can only read analysis results from `data/runs/`.

---

## Running the Tests

```bash
python -m pytest src/tests
```

The engine test generates the demo scenario and checks that all planted campaigns are detected and the decoy ranks lowest.

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
