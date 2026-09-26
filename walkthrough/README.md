# 🛡️ Social Media Threat Intelligence Engine — Walkthrough

> Complete technical walkthrough for the IBM Bob AI Hackathon submission by **Team Shin-chan**.

---

## 📁 Walkthrough Documents

| File | What it covers |
|---|---|
| [`00-index.md`](./00-index.md) | Index of the walkthrough |
| [`01-overview.md`](./01-overview.md) | What the system does, the two-phase architecture, and data flow |
| [`02-backend.md`](./02-backend.md) | Python backend: API, engine pipeline, Bob client, brief renderer |
| [`03-frontend.md`](./03-frontend.md) | React frontend: components, API client, tabs, state management |
| [`04-hardcoded-values.md`](./04-hardcoded-values.md) | **All hardcoded values in the frontend that need to change for new datasets** |
| [`05-how-to-add-data.md`](./05-how-to-add-data.md) | Step-by-step guide for uploading new CSV datasets and running analysis |

---

## Quick-Start Reminder

```bash
# 1. Install Python deps
python -m pip install -r src/requirements.txt

# 2. (Optional) Configure IBM Bob API key
cp src/.env.example src/.env   # then edit BOB_API_KEY=<your key>

# 3. Start the full-stack server
python src/main.py
# → http://127.0.0.1:8000
```
