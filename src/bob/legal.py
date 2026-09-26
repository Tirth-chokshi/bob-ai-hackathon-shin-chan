from pathlib import Path
from config import BOB_RULES

LEGAL_TABLE_PATH = BOB_RULES / "01-legal-table.md"


def load_legal_table(path: Path | None = None) -> dict[str, dict[str, str]]:
    """
    Parses the legal reference table from .bob/rules-osint-analyst/01-legal-table.md
    into a structured dictionary mapping ID -> {law, ipc, title, kind}.
    """
    target_path = path or LEGAL_TABLE_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Legal table markdown file not found at: {target_path}")

    table: dict[str, dict[str, str]] = {}
    with open(target_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue

            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) < 5:
                continue

            sec_id, law, ipc, covers, kind = parts[:5]
            if sec_id.lower() == "id" or "---" in sec_id:
                continue

            table[sec_id] = {
                "id": sec_id,
                "law": law,
                "ipc": ipc,
                "title": covers,
                "kind": kind.lower(),
            }

    return table


def allowed_offence_ids(path: Path | None = None) -> list[str]:
    """Returns all IDs of kind 'offence'."""
    table = load_legal_table(path)
    return [sec_id for sec_id, info in table.items() if info["kind"] == "offence"]


def allowed_procedural_ids(path: Path | None = None) -> list[str]:
    """Returns all IDs of kind 'procedural'."""
    table = load_legal_table(path)
    return [sec_id for sec_id, info in table.items() if info["kind"] == "procedural"]
