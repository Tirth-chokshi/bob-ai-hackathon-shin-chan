# Contributing to Social Media Threat Intelligence Engine

Thank you for your interest in contributing to the **Social Media Threat Intelligence Engine**! This project provides Open Source Intelligence (OSINT) and Coordinated Inauthentic Behavior (CIB) forensic capabilities to law enforcement cyber cells, digital investigators, and researchers.

---

## 🧭 Code of Conduct & Ethical OSINT Principles

Contributors are expected to adhere to the following strict principles:
1. **Behavior First, Content Agnostic:** The engine detects synchronized mathematical coordination (bot networks, sock puppets, inorganic bursts), not political ideology, religion, or protected speech.
2. **Strict Non-Profiling:** Contributors must never add heuristics or features that profile individuals based on religion, caste, gender, ethnicity, or community affiliations.
3. **Decision Support Only:** The system generates forensic leads and evidentiary briefs for trained officers. It must never produce automated executive sanctions or replace judicial due process.

---

## 🛠️ Local Development Setup

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 22+** and **npm**
- **Git**
- (Optional) **IBM Bob Shell** for live AI classification inference (`bob run`)

### 2. Fork and Clone
```bash
git clone https://github.com/Tirth-chokshi/bob-ai-hackathon-shin-chan.git
cd bob-ai-hackathon-shin-chan
```

### 3. Backend Setup
```bash
# Create and activate virtual environment
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r src/requirements.txt
pip install pytest pytest-asyncio
```

### 4. Frontend Setup
```bash
cd src/web
npm ci
npm run dev # Launches local Vite dev server at http://localhost:5173
```

### 5. Running the Full Stack App
```bash
# Build frontend bundle
cd src/web && npm run build && cd ../..

# Launch FastAPI server
python src/main.py
# Server opens at http://127.0.0.1:8000
```

---

## 🧪 Testing Guidelines

Always run tests before submitting a pull request:

```bash
# Run backend test suite
python -m pytest

# Run frontend build check
cd src/web && npm run build
```

Ensure all tests pass and no linter warnings are introduced.

---

## 🔄 Pull Request Workflow

1. **Branch Naming:** Use clear branch names like `feat/new-connector`, `fix/timeline-bounds`, or `docs/update-guide`.
2. **Commit Messages:** Follow conventional commits:
   - `feat(...)`: New feature or capability
   - `fix(...)`: Bug fix
   - `docs(...)`: Documentation updates
   - `test(...)`: Adding or updating tests
   - `refactor(...)`: Code cleanup without behavior change
3. **Open a Pull Request:** Describe the problem your PR solves, how you tested it, and link any related issues.

---

## 📜 License

This project is licensed under the MIT License.
