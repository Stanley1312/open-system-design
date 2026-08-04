import uuid
from datetime import UTC, datetime, timedelta

import demo_app


def make_job(status="pending", duration=10):
    now = datetime.now(UTC)
    return {
        "job_id": uuid.uuid4(),
        "status": status,
        "duration": duration,
        "worker_id": 0 if status == "running" else None,
        "result": "export result" if status == "completed" else None,
        "error": "simulated failure" if status == "error" else None,
        "started_at": now - timedelta(seconds=5) if status != "pending" else None,
        "completed_at": now if status in {"completed", "error"} else None,
        "created_at": now - timedelta(seconds=6),
    }


def test_create_job_rejects_non_object_json():
    client = demo_app.app.test_client()

    response = client.post("/async-export", json=[1, 2, 3])

    assert response.status_code == 400
    assert response.get_json()["error"] == "Request body must be a JSON object"


def test_create_job_rejects_bool_duration():
    client = demo_app.app.test_client()

    response = client.post("/async-export", json={"duration_seconds": True})

    assert response.status_code == 400


def test_create_job_returns_pending_job(monkeypatch):
    job = make_job()
    monkeypatch.setattr(demo_app.demo_db, "create_job", lambda duration: job)
    client = demo_app.app.test_client()

    response = client.post("/async-export", json={"duration_seconds": 10})

    assert response.status_code == 202
    assert response.get_json()["status"] == "pending"
    assert response.get_json()["progress"] == 0


def test_running_job_progress_is_capped_below_complete(monkeypatch):
    job = make_job(status="running", duration=1)
    monkeypatch.setattr(demo_app.demo_db, "get_job", lambda job_id: job)
    client = demo_app.app.test_client()

    response = client.get("/async-export/any-job/status")

    assert response.status_code == 200
    assert response.get_json()["progress"] == 99


def test_unknown_job_returns_404(monkeypatch):
    monkeypatch.setattr(demo_app.demo_db, "get_job", lambda job_id: None)
    client = demo_app.app.test_client()

    response = client.get("/async-export/not-a-job/status")

    assert response.status_code == 404


def test_premature_download_returns_conflict(monkeypatch):
    job = make_job(status="running")
    monkeypatch.setattr(demo_app.demo_db, "get_job", lambda job_id: job)
    client = demo_app.app.test_client()

    response = client.get("/async-export/job-id/download")

    assert response.status_code == 409


def test_completed_job_downloads_text(monkeypatch):
    job = make_job(status="completed")
    monkeypatch.setattr(demo_app.demo_db, "get_job", lambda job_id: job)
    client = demo_app.app.test_client()

    response = client.get("/async-export/job-id/download")

    assert response.status_code == 200
    assert response.data == b"export result"
    assert response.mimetype == "text/plain"
