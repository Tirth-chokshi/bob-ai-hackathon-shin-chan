"""Telegram Desktop export (result.json) → Posts.

Reads a single chat/channel export ({"name", "id", "messages": [...]}) or a full account export
({"chats": {"list": [...]}}). Text may be a string or a list of plain strings and entity objects.
Uses date_unixtime when present; otherwise the local date is read as IST.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from engine.schema import Post

IST = timezone(timedelta(hours=5, minutes=30))


def is_telegram_export(data) -> bool:
    return isinstance(data, dict) and ("messages" in data or "chats" in data)


def _text(value) -> str:
    if isinstance(value, list):
        return "".join(part if isinstance(part, str) else part.get("text", "") for part in value)
    return value or ""


def _time(msg: dict) -> int:
    if msg.get("date_unixtime"):
        return int(msg["date_unixtime"])
    dt = datetime.fromisoformat(msg["date"])
    return int((dt if dt.tzinfo else dt.replace(tzinfo=IST)).timestamp())


def load_telegram(path: str | Path, limit: int | None = None) -> list[Post]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    chats = data["chats"]["list"] if "chats" in data else [data]
    posts = []
    for chat in chats:
        chat_id = chat.get("id", "chat")
        for msg in chat.get("messages", []):
            if msg.get("type") != "message":
                continue  # service messages: joins, pins, title changes
            sender = msg.get("from") or chat.get("name") or "unknown"
            reply = msg.get("reply_to_message_id")
            posts.append(Post(
                post_id=f"tg_{chat_id}_{msg['id']}",
                account_id=f"tg:{msg.get('from_id') or sender}",
                username=sender,
                created_at=_time(msg),
                text=_text(msg.get("text")),
                reply_to=f"tg_{chat_id}_{reply}" if reply else None,
                platform="telegram",
            ))
    return posts[:limit] if limit else posts
