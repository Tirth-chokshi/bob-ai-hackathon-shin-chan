# Setup Guide: Social Media Threat Intelligence Engine

> **This setup guide contains complete instructions to set up and run the template locally.**

---

## Prerequisites

Before you begin, ensure you have the following installed on your machine:

- **Python 3.10+**
- **pip** (Python package manager)
- **Git**

---

## Environment Variables

Copy the template environment file to `.env`:

```bash
cp src/.env.example src/.env
```

| Variable | Description | Required |
|---|---|---|
| `WATSONX_API_KEY` | Your IBM Cloud watsonx.ai API key | Optional |
| `WATSONX_PROJECT_ID` | Your watsonx.ai Project ID | Optional |
| `APP_PORT` | Application server port | Optional (Default: 8000) |
| `APP_ENV` | Application environment (`development` / `production`) | Optional |

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
