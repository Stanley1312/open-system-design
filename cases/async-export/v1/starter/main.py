from io import BytesIO
import time

from flask import Flask, jsonify, render_template, request, send_file


app = Flask(__name__)

DEFAULT_EXPORT_DURATION_SECONDS = 5
MAX_EXPORT_DURATION_SECONDS = 120


@app.get("/")
def index():
    """Show the slow baseline before introducing asynchronous jobs."""
    return render_template(
        "index.html",
        default_duration=DEFAULT_EXPORT_DURATION_SECONDS,
    )


@app.get("/sync-export")
def sync_export():
    """Keep the request open while simulated export work is running."""
    raw_duration = request.args.get(
        "time",
        default=str(DEFAULT_EXPORT_DURATION_SECONDS),
    )

    try:
        duration = int(raw_duration)
    except (TypeError, ValueError):
        return jsonify({"error": "time must be an integer from 1 to 120"}), 400

    if not 1 <= duration <= MAX_EXPORT_DURATION_SECONDS:
        return jsonify({"error": "time must be an integer from 1 to 120"}), 400

    # This wait is intentional. Try the UI first and notice that the browser
    # receives nothing until all simulated work has finished.
    time.sleep(duration)

    content = (
        "Synchronous export completed.\n"
        f"The request stayed open for {duration} seconds.\n"
    )
    return send_file(
        BytesIO(content.encode("utf-8")),
        mimetype="text/plain",
        as_attachment=True,
        download_name="sync-export.txt",
    )


# Your challenge starts here. Read ../CHALLENGE.md and add the asynchronous
# flow one small step at a time: create a job, read its status, then download.


if __name__ == "__main__":
    app.run(debug=True)
