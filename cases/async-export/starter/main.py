from flask import Flask, jsonify


app = Flask(__name__)


@app.get("/")
def index():
    return """
    <h1>Async Export V1</h1>
    <p>The starter server is running. Follow CHALLENGE.md to build the APIs
    and comparison UI.</p>
    """


@app.get("/sync-export")
def sync_export():
    """TODO: simulate a blocking query and return a file attachment."""
    return jsonify({"error": "Not implemented"}), 501


@app.post("/async-export")
def create_async_export_job():
    """TODO: create an in-memory job and return its ID immediately."""
    return jsonify({"error": "Not implemented"}), 501


@app.get("/async-export/<job_id>/status")
def async_export_status(job_id: str):
    """TODO: return status and progress for an existing job."""
    return jsonify(
        {
            "error": "Not implemented",
            "job_id": job_id,
        }
    ), 501


@app.get("/async-export/<job_id>/download")
def download_async_export(job_id: str):
    """TODO: return the completed export as a file attachment."""
    return jsonify(
        {
            "error": "Not implemented",
            "job_id": job_id,
        }
    ), 501


if __name__ == "__main__":
    app.run(debug=True)
