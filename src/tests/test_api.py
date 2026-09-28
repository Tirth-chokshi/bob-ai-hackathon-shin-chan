import time
import networkx as nx
from fastapi.testclient import TestClient
import api.main as main
import engine.pipeline as pipeline
from tests.fixtures import planted_posts, write_csv
from engine.schema import Campaign


def test_upload_analyse_delete(tmp_path, monkeypatch):
    # keep the real data/runs untouched
    monkeypatch.setattr(main, "RUNS", tmp_path)
    monkeypatch.setattr(pipeline, "RUNS", tmp_path)

    with TestClient(main.app) as c:
        rows, _ = planted_posts()
        with open(write_csv(tmp_path / "batch.csv", rows), "rb") as f:
            up = c.post("/api/datasets", files={"file": ("..\\..\\evil.csv", f, "text/csv")}).json()
        ds = up["dataset_id"]
        assert (tmp_path / ds / "upload.csv").exists()  # client filename never used as a path
        assert up["posts"] == len(rows)

        # analysis runs in the background and reports named steps
        assert c.post(f"/api/datasets/{ds}/analyze").status_code == 202
        for _ in range(180):
            job = c.get(f"/api/datasets/{ds}/job").json()
            if job["state"] != "running":
                break
            time.sleep(1)
        assert job["state"] == "done", job

        listed = {d["id"]: d for d in c.get("/api/datasets").json()}
        assert listed[ds]["analyzed"] and listed[ds]["name"] == "evil.csv"

        campaigns = c.get(f"/api/datasets/{ds}/campaigns").json()
        assert [x["id"] for x in campaigns] == ["c1", "c2"]
        assert "post_ids" not in campaigns[0] and campaigns[0]["assessment"] is None
        assert c.get(f"/api/datasets/{ds}/campaigns/c1").json()["sample_posts"]
        assert c.get(f"/api/datasets/{ds}/campaigns/c1/verdict").status_code == 404  # never calls Bob

        # the Posts view: every post, filtered; and the at-a-glance numbers
        stats = c.get(f"/api/datasets/{ds}/stats").json()
        assert stats["posts"] == up["posts"] and "whatsapp" in stats["platforms"] and "hinglish" in stats["languages"]
        found = c.get(f"/api/datasets/{ds}/posts", params={"campaign": "c1", "limit": 5}).json()
        assert 0 < len(found["posts"]) <= 5 and all(x["campaign"] == "c1" for x in found["posts"])
        assert found["facets"]["campaign"] == {"c1": found["total"]}

        assert c.get("/api/datasets/bad.id/graph").status_code == 400
        assert c.delete(f"/api/datasets/{ds}").status_code == 200
        assert not (tmp_path / ds).exists()


def test_classify_sends_all_stored_sample_posts(monkeypatch):
    campaign = Campaign(
        id="c1", accounts=["a1"], post_ids=[f"p{i}" for i in range(20)],
        size=1, score=50, features={}, signals=[], first_seen=0, last_seen=19,
    )
    samples = [
        {"post_id": f"p{i}", "account_id": "a1", "username": "user",
         "created_at": i, "text": f"post {i}"}
        for i in range(20)
    ]
    received = []

    class Verdict:
        def model_dump(self):
            return {"threat_type": "benign_coordination"}

    def fake_classify(run_dir, campaign_arg, sample_posts):
        received.extend(sample_posts)
        return Verdict(), 0.01, False

    monkeypatch.setattr(main, "load_campaign", lambda *_: campaign)
    monkeypatch.setattr(main, "load_samples", lambda *_: samples)
    monkeypatch.setattr(main, "classify", fake_classify)
    monkeypatch.setattr(main, "escalate", lambda *_: {"level": "LOW"})

    with TestClient(main.app) as client:
        response = client.post("/api/datasets/test/campaigns/c1/classify")

    assert response.status_code == 200
    assert len(received) == 20
    assert received[-1].post_id == "p19"


def test_stream_api_uses_event_time_window_and_marks_alert_provisional(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "STREAM_DB", tmp_path / "streams.sqlite")
    monkeypatch.setattr(main, "STREAMS", tmp_path / "stream-work")
    monkeypatch.setattr(main, "STREAM_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "STREAM_RETENTION_SECONDS", 1000)
    observed = []

    def fake_graph(posts, **kwargs):
        observed.append([post.created_at for post in posts])
        return nx.Graph()

    monkeypatch.setattr(main, "build_graph", fake_graph)
    monkeypatch.setattr(main, "find_campaigns", lambda *args, **kwargs: [])

    with TestClient(main.app) as client:
        late = {"post_id": "p2", "account_id": "a2", "created_at": 120, "text": "second post"}
        first = {"post_id": "p1", "account_id": "a1", "created_at": 90, "text": "first post"}
        old = {"post_id": "p0", "account_id": "a0", "created_at": 10, "text": "old post"}
        response = client.post("/api/streams/alpha/posts", json=late)
        assert response.status_code == 200
        assert response.json()["alert"]["status"] == "provisional"
        assert response.json()["alert"]["review_required"] is True
        client.post("/api/streams/alpha/posts", json=first)
        duplicate = client.post("/api/streams/alpha/posts", json=first)
        assert duplicate.json()["duplicate"] is True
        client.post("/api/streams/alpha/posts", json=old)

        alert = client.get("/api/streams/alpha/alerts").json()
        assert alert["window_posts"] == 2
        assert alert["retained_posts"] == 3
        assert observed[-1] == [90, 120]
        assert client.get("/api/streams/alpha/timeline").json()["points"]
        batch = client.post("/api/streams/beta/posts", json=[late, first])  # a list is one rebuild
        assert batch.json()["posts"] == 2 and observed[-1] == [90, 120]
        assert client.post("/api/streams/alpha/close").json()["status"] == "closed"
        assert client.post("/api/streams/alpha/posts", json={**late, "post_id": "p3"}).status_code == 409


def test_upload_with_unknown_column_names_asks_for_mapping(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "RUNS", tmp_path)
    rows = ["Sr,Poster,When posted,Message body"] + [
        f"{i},{['ramesh', 'pintu'][i % 2]},22/09/2020 10:{i:02d},aaj shaam sab log bus stand pahuncho" for i in range(8)]
    with TestClient(main.app) as c:
        up = c.post("/api/datasets", files={"file": ("tipline.csv", "\n".join(rows).encode(), "text/csv")}).json()
        assert up["needs_mapping"] and up["suggested"]["account_id"] == "Poster" and len(up["rows"]) == 5
        listed = {d["id"]: d for d in c.get("/api/datasets").json()}
        assert listed[up["dataset_id"]]["needs_mapping"] and not listed[up["dataset_id"]]["analyzed"]

        bad = c.post(f"/api/datasets/{up['dataset_id']}/mapping", json={"mapping": {"text": "Message body"}})
        assert bad.status_code == 422 and "who posted it" in bad.json()["detail"]
        ok = c.post(f"/api/datasets/{up['dataset_id']}/mapping", json={"mapping": up["suggested"]}).json()
        assert ok["posts"] == 8 and ok["timezone"] == "Asia/Kolkata" and "status" not in ok
        assert c.get(f"/api/datasets/{up['dataset_id']}/columns").json()["suggested"]["account_id"] == "Poster"


def test_x_search_connector(tmp_path, monkeypatch):
    from tests.test_formats import X_PAGE
    monkeypatch.setattr(main, "RUNS", tmp_path)
    monkeypatch.setattr(main, "X_BEARER_TOKEN", "test-token")
    asked = {}
    def fake_search(query, token, max_posts):
        asked.update(query=query, token=token)
        return [X_PAGE]
    monkeypatch.setattr(main, "search_recent", fake_search)
    with TestClient(main.app) as c:
        r = c.post("/api/connectors/x/search", json={"query": "#RajpuraBachao"}).json()
        assert asked == {"query": "#RajpuraBachao", "token": "test-token"}
        assert r["posts"] == 3 and r["source"] == "x_api" and r["name"] == "X search: #RajpuraBachao"
        assert (tmp_path / r["dataset_id"] / "upload.jsonl").exists()  # raw API pages kept as the source


def test_stream_accepts_x_api_lines(tmp_path, monkeypatch):
    from tests.test_formats import X_PAGE
    monkeypatch.setattr(main, "STREAM_DB", tmp_path / "streams.sqlite")
    monkeypatch.setattr(main, "STREAMS", tmp_path / "work")
    monkeypatch.setattr(main, "build_graph", lambda posts, **kw: nx.Graph())
    with TestClient(main.app) as c:
        line = {"data": X_PAGE["data"][0], "includes": X_PAGE["includes"], "matching_rules": [{"id": "1"}]}
        r = c.post("/api/streams/xs/posts", json=line).json()
        assert r["posts"] == 1 and r["alert"]["window_posts"] == 1


def test_posts_view_threads_and_real_counts(tmp_path, monkeypatch):
    """Replies, reposts and quotes are linked; counts are the platform's when present, else found in the dataset."""
    import json
    from engine.explore import search_posts, thread
    run = tmp_path / "r"
    run.mkdir()
    post = lambda pid, **kw: {"post_id": pid, "account_id": kw.pop("a", pid), "username": kw.pop("u", pid),
                              "created_at": kw.pop("t", 0), "text": kw.pop("text", pid), "hashtags": [], "urls": [], **kw}
    posts = [post("root", t=1, text="first #tag"), post("r1", t=2, reply_to="root"), post("r2", t=3, reply_to="r1"),
             post("rt1", t=4, repost_of="root"), post("rt2", t=5, repost_of="root"), post("q1", t=6, quote_of="root"),
             post("x", t=7, metrics={"likes": 9, "reposts": 3})]
    (run / "posts.json").write_text(json.dumps(posts), encoding="utf-8")
    (run / "campaigns.json").write_text(json.dumps([{"id": "c1", "post_ids": ["rt1", "rt2"]}]), encoding="utf-8")

    feed = {p["post_id"]: p for p in search_posts(run, limit=50)["posts"]}
    assert feed["root"]["counts"] == {"replies": 1, "reposts": 2, "quotes": 1, "source": "dataset"}
    assert feed["x"]["counts"]["likes"] == 9 and feed["x"]["counts"]["source"] == "platform"
    assert feed["rt1"]["original"]["post_id"] == "root" and feed["q1"]["quoted"]["post_id"] == "root"
    assert feed["r2"]["replying_to"] == "r1"
    assert [p["post_id"] for p in search_posts(run, sort="top")["posts"]][:1] == ["x"]
    assert search_posts(run, kind="reposts")["total"] == 2 and search_posts(run, campaign="c1")["total"] == 2

    t = thread(run, "r2")
    assert [a["post_id"] for a in t["ancestors"]] == ["root", "r1"] and not t["missing_parent"]
    t = thread(run, "root")
    assert [r["post_id"] for r in t["replies"]] == ["r1"] and len(t["reposted_by"]) == 2 and t["quotes"][0]["post_id"] == "q1"
