import os
from pathlib import Path
from dotenv import load_dotenv

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
load_dotenv(SRC / ".env")

DATA = ROOT / "data"                    # gitignored
RAW = DATA / "raw"                      # downloaded datasets
RUNS = DATA / "runs"                    # analysis output, one folder per dataset
SAMPLES = SRC / "samples"               # committed: scenario CSV, truth.json, demo_run/
BOB_RULES = ROOT / ".bob" / "rules-osint-analyst"
WEB_DIST = SRC / "web" / "dist"

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
TIME_WINDOW = int(os.getenv("TIME_WINDOW_SECONDS", "60"))
MIN_EDGE_WEIGHT = int(os.getenv("MIN_EDGE_WEIGHT", "2"))
BOB_API_KEY = os.getenv("BOB_API_KEY", "")
BOB_MAX_COST = os.getenv("BOB_MAX_COST", "0.25")
