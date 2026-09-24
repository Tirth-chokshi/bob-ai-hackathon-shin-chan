# Setup Guide: Social Media Threat Intelligence Engine

> **This setup guide contains complete instructions to set up and run the template locally.**

---

## Prerequisites

Before you begin, ensure you have the following installed on your machine:

- **Python 3.10+**
- **pip** (Python package manager)
- **Git**
- **IBM Bob Shell** (needs Node.js 24+) — install from [bob.ibm.com/download](https://bob.ibm.com/download) and sign in, or set `BOB_API_KEY`

---

## Environment Variables

Copy the template environment file to `.env`:

```bash
cp src/.env.example src/.env
```

| Variable | Description | Required |
|---|---|---|
| `BOB_API_KEY` | IBM Bob Inference API key for headless `bob run` | Only if Bob Shell is not signed in |
| `BOB_MAX_COST` | Bobcoin cap per classification call | Optional (Default: 0.50) |
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

```bash
cp src/.env.example src/.env
```

### 3. Install Dependencies

```bash
pip install -r src/requirements.txt
```

---

## Running the Application

```bash
python src/main.py
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Missing dependencies | Run `pip install -r src/requirements.txt` |
| Python version error | Ensure Python 3.10+ is installed and active in your terminal |
