import csv
import json
import random
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
SAMPLES_DIR = SRC_DIR / "samples"


def generate(seed: int = 42) -> tuple[list[dict], dict]:
    rng = random.Random(seed)
    t0 = 1790140000  # Base timestamp in seconds

    posts: list[dict] = []
    post_counter = 1

    def next_post_id() -> str:
        nonlocal post_counter
        pid = f"p{post_counter:05d}"
        post_counter += 1
        return pid

    # 1. Background accounts (~800 accounts, 1-8 years old)
    bg_accounts = [f"bg_{i:04d}" for i in range(1, 801)]
    bg_meta = {}
    for acc in bg_accounts:
        age_days = rng.randint(365, 365 * 8)
        created_at = t0 - (age_days * 86400) + rng.randint(0, 86400)
        username = f"user_{acc}"
        bg_meta[acc] = {"username": username, "created_at": created_at}

    # Journalist account for harassment target
    journo_id = "journo_01"
    journo_username = "asha_reports"
    journo_created = t0 - (4 * 365 * 86400)
    bg_meta[journo_id] = {"username": journo_username, "created_at": journo_created}

    # Seed 3 journalist posts over the 48h timeline
    journo_post_ids = []
    for idx, delta_h in enumerate([6, 20, 34], 1):
        pid = next_post_id()
        journo_post_ids.append(pid)
        p_time = t0 + delta_h * 3600
        posts.append({
            "post_id": pid,
            "account_id": journo_id,
            "username": journo_username,
            "created_at": p_time,
            "text": f"Investigative report part {idx}: Reviewing infrastructure expenditure and water canal maintenance in Sundarpur district. Public accountability is essential.",
            "repost_of": "",
            "reply_to": "",
            "urls": f"http://sundarpur-times.example/report-{idx}",
            "hashtags": "#SundarpurNews #Accountability",
            "account_created_at": journo_created
        })

    # Background chatter topics
    bg_topics = [
        "Morning tea at Station Road in Sundarpur hits different during winters.",
        "Heavy traffic near Sundarpur Clock Tower due to market rush today.",
        "Pleasant breezy weather across Sundarpur this afternoon.",
        "Sundarpur central library renovation is finally completing this month.",
        "Delicious street food near Gandhi circle, best kachori in Sundarpur!",
        "Local municipal council announced park cleanup drive this Sunday.",
        "Evening cricket practice match at Sundarpur town stadium was exciting.",
        "Power cut announced for northern suburbs of Sundarpur tomorrow 10am-12pm.",
        "Monsoon drainage repairs starting near Sundarpur east bus terminus.",
        "Great community turnout for the Sundarpur cultural festival rehearsals."
    ]

    for acc in bg_accounts:
        num_posts = rng.randint(4, 6)
        for _ in range(num_posts):
            p_time = t0 + rng.randint(0, 48 * 3600)
            topic = rng.choice(bg_topics)
            repost = ""
            reply = ""
            # Occasionally reply to another post or repost
            if posts and rng.random() < 0.08:
                target = rng.choice(posts)
                if rng.random() < 0.5:
                    reply = target["post_id"]
                    topic = f"@{target['username']} Agree with this point completely."
                else:
                    repost = target["post_id"]

            posts.append({
                "post_id": next_post_id(),
                "account_id": acc,
                "username": bg_meta[acc]["username"],
                "created_at": p_time,
                "text": topic,
                "repost_of": repost,
                "reply_to": reply,
                "urls": "http://sundarpurnews.example/local" if rng.random() < 0.1 else "",
                "hashtags": "#Sundarpur #Daily" if rng.random() < 0.15 else "",
                "account_created_at": bg_meta[acc]["created_at"]
            })

    # 2. Campaign A — Rumour ring (40 accounts, 2-10 days old, 6 bursts, high text overlap, call to action)
    camp_a_accounts = [f"a_{1000 + i}" for i in range(1, 41)]
    camp_a_meta = {}
    for acc in camp_a_accounts:
        age_days = rng.randint(2, 10)
        c_at = t0 - (age_days * 86400) - rng.randint(1000, 50000)
        camp_a_meta[acc] = {"username": f"alert_{acc}", "created_at": c_at}

    templates_a = [
        "Sundarpur dam gates will be opened TONIGHT, whole east side will flood. Officials hiding it! Everyone gather at Collector office 7 PM! #SundarpurAlert",
        "Urgent alert for Sundarpur east: Dam floodgates opening tonight without public notice! East side will submerge. Assemble at District Collector office 7 PM! #SundarpurAlert",
        "Critical warning! Water release from Sundarpur main dam planned tonight! Administration silent. Mass gathering at Collector office 7 PM sharp! #SundarpurAlert"
    ]

    burst_times_a = [t0 + h * 3600 + 1200 for h in [4, 10, 16, 22, 28, 36]]
    for b_idx, burst_t in enumerate(burst_times_a):
        base_tmpl = templates_a[b_idx % len(templates_a)]
        for acc in camp_a_accounts:
            post_t = burst_t + rng.randint(0, 28)  # within 30s
            # Create slight lexical variations maintaining > 0.8 overlap
            t_words = base_tmpl.split()
            if rng.random() < 0.3:
                # swap exclamation or minor punctuation
                var_text = base_tmpl.replace("!", "!!").replace("TONIGHT", "TONIGHT itself")
            elif rng.random() < 0.6:
                var_text = base_tmpl.replace("Critical warning!", "Warning!").replace("sharp!", "sharp.")
            else:
                var_text = base_tmpl

            posts.append({
                "post_id": next_post_id(),
                "account_id": acc,
                "username": camp_a_meta[acc]["username"],
                "created_at": post_t,
                "text": var_text,
                "repost_of": "",
                "reply_to": "",
                "urls": "",
                "hashtags": "#SundarpurAlert",
                "account_created_at": camp_a_meta[acc]["created_at"]
            })

    # 3. Campaign B — Link ring (25 accounts, 5-20 days old, 5 rounds sharing common URLs within 60s)
    camp_b_accounts = [f"b_{2000 + i}" for i in range(1, 26)]
    camp_b_meta = {}
    for acc in camp_b_accounts:
        age_days = rng.randint(5, 20)
        c_at = t0 - (age_days * 86400) - rng.randint(500, 60000)
        camp_b_meta[acc] = {"username": f"voice_{acc}", "created_at": c_at}

    slugs_b = [
        "dam-leak-coverup-doc",
        "secret-canal-diversion",
        "water-crisis-exposed",
        "emergency-documents-leak",
        "sundarpur-audit-unmasked"
    ]
    round_times_b = [t0 + h * 3600 + 2400 for h in [7, 14, 21, 30, 40]]
    for r_idx, r_time in enumerate(round_times_b):
        slug = slugs_b[r_idx]
        url = f"http://sundarpur-truth.example/{slug}"
        for acc in camp_b_accounts:
            post_t = r_time + rng.randint(0, 55)  # within 60s
            lead_in = rng.choice([
                "Read the leaked documents before they get taken down:",
                "Exclusive report exposing the truth that mainstream media ignores:",
                "See the official inspection report leaked online:",
                "Important evidence documents available here:"
            ])
            posts.append({
                "post_id": next_post_id(),
                "account_id": acc,
                "username": camp_b_meta[acc]["username"],
                "created_at": post_t,
                "text": f"{lead_in} {url} #SundarpurExposed",
                "repost_of": "",
                "reply_to": "",
                "urls": url,
                "hashtags": "#SundarpurExposed",
                "account_created_at": camp_b_meta[acc]["created_at"]
            })

    # 4. Campaign C — Harassment pile-on (30 accounts, 3-15 days old, 3 waves replying to @asha_reports within 5m)
    camp_c_accounts = [f"c_{3000 + i}" for i in range(1, 31)]
    camp_c_meta = {}
    for acc in camp_c_accounts:
        age_days = rng.randint(3, 15)
        c_at = t0 - (age_days * 86400) - rng.randint(1000, 40000)
        camp_c_meta[acc] = {"username": f"patriot_{acc}", "created_at": c_at}

    harass_templates = [
        "@{target} Stop peddling biased sensational fake news to divide Sundarpur! Your defamatory agenda is exposed.",
        "@{target} Corrupt journalism at its peak. Stop spreading lies and defaming our local officials without proof!",
        "@{target} Sensationalism and manufactured scandals will not work here. Stop misleading the public!"
    ]

    for wave_idx, target_pid in enumerate(journo_post_ids):
        # Wave starts 15 minutes after journalist post
        wave_start = [p["created_at"] for p in posts if p["post_id"] == target_pid][0] + 900
        for acc in camp_c_accounts:
            post_t = wave_start + rng.randint(0, 290)  # within 5 minutes
            tmpl = rng.choice(harass_templates)
            msg = tmpl.format(target=journo_username)
            posts.append({
                "post_id": next_post_id(),
                "account_id": acc,
                "username": camp_c_meta[acc]["username"],
                "created_at": post_t,
                "text": msg,
                "repost_of": "",
                "reply_to": target_pid,
                "urls": "",
                "hashtags": "#FakeNewsExposed",
                "account_created_at": camp_c_meta[acc]["created_at"]
            })

    # 5. Campaign D — Decoy (benign coordination: 60 established accounts, 1-6 years old).
    # Fans post the same chants within minutes at three match moments, so they DO coordinate;
    # the score has to rank them below the threat rings, and Bob should call them benign.
    camp_d_accounts = [f"d_{4000 + i}" for i in range(1, 61)]
    camp_d_meta = {}
    for acc in camp_d_accounts:
        age_days = rng.randint(365, 365 * 6)
        c_at = t0 - (age_days * 86400) - rng.randint(1000, 40000)
        camp_d_meta[acc] = {"username": f"fan_{acc}", "created_at": c_at}

    decoy_moments = [  # (start, chants) — final whistle, trophy lift, open-bus parade
        (t0 + 26 * 3600, [
            "What a thrilling win! Sundarpur Strikers won the district cricket finals! #SundarpurStrikers",
            "Sensational finish by the captain! Sundarpur Strikers are champions! #SundarpurStrikers",
            "Proud moment for our city team! What an incredible victory! #SundarpurStrikers",
        ]),
        (t0 + 26 * 3600 + 1800, [
            "Trophy lifted! Congratulations Sundarpur Strikers, district champions! #SundarpurStrikers",
            "Our captain lifts the district trophy! Well deserved! #SundarpurStrikers",
            "Champions of the district! Proud of every player today! #SundarpurStrikers",
        ]),
        (t0 + 27 * 3600 + 1800, [
            "Open bus parade for Sundarpur Strikers at the Clock Tower now! Come cheer! #SundarpurStrikers",
            "Whole town cheering the Strikers parade at the Clock Tower! #SundarpurStrikers",
            "Crowds everywhere for our champions' victory parade! #SundarpurStrikers",
        ]),
    ]

    for start, chants in decoy_moments:
        for acc in camp_d_accounts:
            posts.append({
                "post_id": next_post_id(),
                "account_id": acc,
                "username": camp_d_meta[acc]["username"],
                "created_at": start + rng.randint(0, 180),  # within 3 minutes
                "text": rng.choice(chants),
                "repost_of": "",
                "reply_to": "",
                "urls": "",
                "hashtags": "#SundarpurStrikers",
                "account_created_at": camp_d_meta[acc]["created_at"]
            })

    # Sort all posts chronologically
    posts.sort(key=lambda x: (x["created_at"], x["post_id"]))

    truth = {
        "fixture_id": "synthetic_sundarpur",
        "fixture_version": "1.0",
        "seed": seed,
        "A": camp_a_accounts,
        "B": camp_b_accounts,
        "C": camp_c_accounts,
        "D": camp_d_accounts,
        "labels": {
            "A": "organized_misinformation",
            "B": "organized_misinformation",
            "C": "targeted_harassment",
            "D": "benign_coordination"
        }
    }

    return posts, truth


def save_scenario(seed: int = 42, out_csv: Path | None = None, out_truth: Path | None = None):
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    posts, truth = generate(seed=seed)

    csv_path = out_csv or (SAMPLES_DIR / "scenario_posts.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "post_id", "account_id", "username", "created_at",
            "text", "repost_of", "reply_to", "urls", "hashtags",
            "account_created_at"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(posts)

    truth_path = out_truth or (SAMPLES_DIR / "truth.json")
    truth_path.parent.mkdir(parents=True, exist_ok=True)
    with open(truth_path, "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2)

    print(f"Generated {len(posts)} scenario posts -> {csv_path}")
    print(f"Generated truth with {len(truth['labels'])} planted campaigns -> {truth_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic social media threat scenario")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for generation")
    parser.add_argument("--output", type=Path, default=None, help="Output CSV path")
    parser.add_argument("--truth", type=Path, default=None, help="Output truth JSON path")
    args = parser.parse_args()

    save_scenario(seed=args.seed, out_csv=args.output, out_truth=args.truth)

