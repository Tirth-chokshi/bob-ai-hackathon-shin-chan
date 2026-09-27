import json
from datetime import date
from pathlib import Path
from config import BOB_RULES

LEGAL_TABLE_PATH = BOB_RULES / "01-legal-table.md"
LEGAL_METADATA_PATH = BOB_RULES / "legal-reference-metadata.json"


def load_legal_metadata(table: dict[str, dict[str, str]], path: Path = LEGAL_METADATA_PATH) -> dict:
    """Load version metadata and ensure every provision matches the source table."""
    if not path.exists():
        raise FileNotFoundError(f"Legal reference metadata not found at: {path}")
    metadata = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "reference_version", "source_document", "review_status",
                "effective_date", "last_legal_review", "required_disclaimer", "provisions"}
    if not required.issubset(metadata):
        raise ValueError("Legal reference metadata is missing required fields")
    if metadata["schema_version"] != 1 or metadata["review_status"] not in {
        "pending_qualified_review", "reviewed"
    }:
        raise ValueError("Unsupported legal reference metadata version or review status")
    if not metadata["reference_version"] or not metadata["required_disclaimer"]:
        raise ValueError("Legal reference version and disclaimer are required")
    for field in ("effective_date", "last_legal_review"):
        value = metadata[field]
        if value is not None:
            try:
                date.fromisoformat(value)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Legal metadata {field} must be an ISO date or null") from e

    entries = {entry.get("id"): entry for entry in metadata["provisions"]}
    if set(entries) != set(table):
        raise ValueError("Legal metadata provision IDs do not match the legal table")
    for provision_id, info in table.items():
        entry = entries[provision_id]
        if entry.get("kind") != info["kind"]:
            raise ValueError(f"Legal metadata kind mismatch for {provision_id}")
        for field in ("source", "effective_date", "last_legal_review"):
            if field not in entry:
                raise ValueError(f"Legal metadata {field} missing for {provision_id}")
            value = entry[field]
            if field != "source" and value is not None:
                try:
                    date.fromisoformat(value)
                except (TypeError, ValueError) as e:
                    raise ValueError(f"Legal metadata {field} must be an ISO date or null for {provision_id}") from e
        if entry["source"] is not None and not isinstance(entry["source"], str):
            raise ValueError(f"Legal metadata source must be a string or null for {provision_id}")
    return metadata


def load_legal_table(path: Path | None = None, metadata_path: Path | None = None) -> dict[str, dict[str, str]]:
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

    metadata_file = metadata_path or LEGAL_METADATA_PATH if path is None else metadata_path
    if metadata_file is not None:
        metadata = load_legal_metadata(table, metadata_file)
        entries = {entry["id"]: entry for entry in metadata["provisions"]}
        for provision_id, info in table.items():
            info.update(entries[provision_id])
            info.update(reference_version=metadata["reference_version"],
                        review_status=metadata["review_status"],
                        required_disclaimer=metadata["required_disclaimer"])
    return table


def allowed_offence_ids(path: Path | None = None) -> list[str]:
    """Returns all IDs of kind 'offence'."""
    table = load_legal_table(path)
    return [sec_id for sec_id, info in table.items() if info["kind"] == "offence"]

