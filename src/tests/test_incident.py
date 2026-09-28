import networkx as nx
from engine.incident import detection_time, profile_campaign
from engine.schema import Post


def post(i, account, t, text, platform="x", city="A", link=""):
    return Post(post_id=f"p{i}", account_id=account, username=account, created_at=t,
                text=f"{text} {link}".strip(), urls=[link] if link else [], platform=platform, city=city,
                account_created_at=t - 5 * 86400)


def test_spread_profile_and_detection_time():
    accounts = [f"a{i}" for i in range(6)]
    posts = [post(0, "seed", 100, "rumour starts", platform="whatsapp", city="A")]
    # two bursts, 1000 s apart: every pair shares the same link twice -> linked at the second burst
    for burst, (t, platform, city) in enumerate([(1000, "whatsapp", "A"), (2000, "x", "B")]):
        for i, a in enumerate(accounts):
            posts.append(post(10 * burst + i + 1, a, t + i, "share this", platform=platform, city=city, link="https://v.example/1"))

    assert detection_time(posts, window=60) == 2004  # a4, the 5th account, repeats at 2000 + 4
    assert detection_time(posts[:7], window=60) is None  # one burst is not enough

    G = nx.Graph()
    G.add_weighted_edges_from([("a0", a, 2) for a in accounts[1:]])
    prof = profile_campaign(["seed", *accounts], posts, G, window=60)
    assert prof["seeds"][0]["username"] == "seed" and prof["seeds"][0]["platform"] == "whatsapp"
    assert [p["name"] for p in prof["platform_path"]] == ["whatsapp", "x"]
    assert [p["name"] for p in prof["town_path"]] == ["A", "B"]
    assert prof["amplifiers"][0]["account_id"] == "a0"
    assert prof["new_account_share"] == 1.0
