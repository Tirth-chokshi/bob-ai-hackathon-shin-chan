import time
from fastapi.testclient import TestClient
import api.main as main
import engine.pipeline as pipeline
from config import SAMPLES


def test_upload_analyse_delete(tmp_path, monkeypatch):
    # keep the real data/runs untouched
    monkeypatch.setattr(main, "RUNS", tmp_path)
    monkeypatch.setattr(pipeline, "RUNS", tmp_path)

    with TestClient(main.app) as c:
        with open(SAMPLES / "scenario_posts.csv", "rb") as f:
            up = c.post("/api/datasets", files={"file": ("..\\..\\evil.csv", f, "text/csv")}).json()
        ds = up["dataset_id"]
        assert (tmp_path / ds / "upload.csv").exists()  # client filename never used as a path
        assert up["posts"] == 4658

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
        assert [x["id"] for x in campaigns] == ["c1", "c2", "c3", "c4"]
        assert "post_ids" not in campaigns[0] and campaigns[0]["assessment"] is None
        assert c.get(f"/api/datasets/{ds}/campaigns/c1").json()["sample_posts"]
        assert c.get(f"/api/datasets/{ds}/campaigns/c1/verdict").status_code == 404  # never calls Bob

        assert c.get("/api/datasets/bad.id/graph").status_code == 400
        assert c.delete("/api/datasets/demo").status_code == 400
        assert c.delete(f"/api/datasets/{ds}").status_code == 200
        assert not (tmp_path / ds).exists()
