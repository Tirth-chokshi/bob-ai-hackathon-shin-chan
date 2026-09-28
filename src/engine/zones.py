"""Which clock a dataset's times are shown in. Stored as an IANA name in the run's meta.json ("timezone")."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from engine.schema import Post

INDIA = "Asia/Kolkata"
INDIC = {"hi", "hinglish", "bn", "pa", "gu", "ta", "te", "kn", "ml", "mr", "ur", "or"}


def guess_timezone(posts: list[Post]) -> str:
    """India time for Indian-language or messaging-app data (those exports carry the phone's IST clock), else UTC."""
    if not posts:
        return "UTC"
    indic = sum(p.language in INDIC or p.platform in ("whatsapp", "telegram") for p in posts)
    return INDIA if indic / len(posts) >= 0.1 else "UTC"


def dataset_zone(run_dir: Path) -> ZoneInfo:
    meta = run_dir / "meta.json"
    name = json.loads(meta.read_text(encoding="utf-8")).get("timezone") if meta.exists() else None
    return ZoneInfo(name or "UTC")


def zone_abbr(zone: ZoneInfo, ts: int) -> str:
    return "IST" if zone.key == INDIA else datetime.fromtimestamp(ts, zone).strftime("%Z")


def local_text(ts: int | None, zone: ZoneInfo, fmt: str = "%a %d %b %Y %H:%M") -> str | None:
    """A timestamp as local wall-clock text with its zone, e.g. 'Tue 22 Sep 2020 10:02 IST'."""
    if ts is None:
        return None
    return f"{datetime.fromtimestamp(ts, zone).strftime(fmt)} {zone_abbr(zone, ts)}"
