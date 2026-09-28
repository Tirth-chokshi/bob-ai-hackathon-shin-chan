"""WhatsApp chat export (.txt) → Posts.

Handles the Android format   "22/09/20, 10:02 - Ramesh Ji: message"   (24 h or am/pm)
and the iPhone format        "[22/09/20, 10:02:15] Ramesh Ji: message".
Lines without a timestamp continue the previous message; system lines without a sender are skipped.
Dates are read day-first (as exported in India) and times as IST, the phone's clock.
"""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from engine.schema import Post

IST = timezone(timedelta(hours=5, minutes=30))
LINE = re.compile(
    r"^\[?(?P<d>\d{1,2})/(?P<m>\d{1,2})/(?P<y>\d{2,4}),?\s+(?P<H>\d{1,2}):(?P<M>\d{2})(?::(?P<S>\d{2}))?"
    r"\s*(?P<ampm>[AaPp]\.?\s?[Mm]\.?)?\]?\s*(?:-\s+)?(?P<rest>.*)$"
)


def _timestamp(g: dict) -> int:
    year = int(g["y"]) + (2000 if len(g["y"]) == 2 else 0)
    hour = int(g["H"])
    if g["ampm"]:
        pm = g["ampm"].lower().startswith("p")
        hour = hour % 12 + (12 if pm else 0)
    dt = datetime(year, int(g["m"]), int(g["d"]), hour, int(g["M"]), int(g["S"] or 0), tzinfo=IST)
    return int(dt.timestamp())


def load_whatsapp(path: str | Path, limit: int | None = None) -> list[Post]:
    messages = []  # [created_at, sender, text]
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n").replace("‎", "").replace(" ", " ")
            m = LINE.match(line)
            if m and ": " in m["rest"]:
                sender, text = m["rest"].split(": ", 1)
                messages.append([_timestamp(m.groupdict()), sender.strip(), text])
            elif m:
                continue  # system line such as "Messages are end-to-end encrypted"
            elif messages:
                messages[-1][2] += "\n" + line  # continuation of a multi-line message
    if limit:
        messages = messages[:limit]
    return [
        Post(post_id=f"wa_{i + 1}", account_id=f"wa:{sender}", username=sender, created_at=t, text=text,
             platform="whatsapp")
        for i, (t, sender, text) in enumerate(messages)
    ]
