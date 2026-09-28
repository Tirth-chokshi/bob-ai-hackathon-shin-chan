"""A small post batch built at test time, with known answers: never stored, never shown in the app.

- 120 ordinary accounts, each posting its own text at random times over six hours
- ring "R": 10 accounts a few days old post the same text and link within seconds, four times
- ring "H": 8 accounts reply to the same post within minutes, three times (a pile-on)
"""
import csv
import random
from pathlib import Path

T0 = 1790000000  # a fixed start time, so every run is the same
WORDS = "rain market school bus road water power price train match film exam temple crowd news phone".split()


def planted_posts(seed: int = 7) -> tuple[list[dict], dict]:
    r = random.Random(seed)
    rows = []

    def post(pid, account, t, text, created=T0 - 3 * 365 * 86400, **extra):
        rows.append({"post_id": pid, "account_id": account, "username": account, "created_at": t, "text": text,
                     "account_created_at": created, "platform": extra.pop("platform", "x"), **extra})

    organic = [f"citizen_{i}" for i in range(120)]
    for i, a in enumerate(organic):
        for k in range(3):
            post(f"o{i}_{k}", a, T0 + r.randint(0, 6 * 3600), " ".join(r.sample(WORDS, 6)) + f" {i}-{k}")

    ring = [f"alert_{i}" for i in range(10)]
    for burst in range(4):
        start = T0 + 3600 + burst * 1800
        for i, a in enumerate(ring):
            post(f"r{burst}_{i}", a, start + r.randint(0, 40), "Bus stand pe sab log pahuncho aaj shaam 6 baje "
                 "https://youtu.be/k7Xq2ZtR9dA #RajpuraBachao", created=T0 - 3 * 86400, platform="whatsapp" if i < 3 else "x")

    pile = [f"troll_{i}" for i in range(8)]
    for burst in range(3):
        start = T0 + 2 * 3600 + burst * 2400
        for i, a in enumerate(pile):
            post(f"h{burst}_{i}", a, start + r.randint(0, 200), f"@factcheck jhooth mat bolo {r.choice(WORDS)} #Resign",
                 created=T0 - 10 * 86400, reply_to=f"target{burst}")

    rows.sort(key=lambda x: x["created_at"])
    return rows, {"R": ring, "H": pile, "organic": organic}


def write_csv(path: Path, rows: list[dict]) -> Path:
    fields = ["post_id", "platform", "account_id", "username", "created_at", "text", "reply_to", "account_created_at"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return path
