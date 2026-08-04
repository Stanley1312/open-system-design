"""HTTP scaffold for the Async Export V2 challenge."""

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify(
        {
            "case": "Async Export V2",
            "next_step": "Implement the endpoints in CHALLENGE.md",
        }
    )


@app.post("/async-export")
def create_async_export_job():
    # TODO: validate input and persist a pending job.
    return jsonify({"error": "Not implemented"}), 501


@app.get("/async-export/<job_id>/status")
def async_export_status(job_id: str):
    # TODO: load the job and return its status and progress.
    return jsonify({"job_id": job_id, "error": "Not implemented"}), 501


@app.get("/async-export/<job_id>/download")
def download_async_export(job_id: str):
    # TODO: return 409 until the export is completed, then send the file.
    return jsonify({"job_id": job_id, "error": "Not implemented"}), 501


if __name__ == "__main__":
    app.run()
