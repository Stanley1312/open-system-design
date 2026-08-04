FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY demo_app.py demo_db.py demo_worker.py worker_pool.py ./
COPY templates ./templates
COPY static ./static

EXPOSE 5000

CMD ["uv", "run", "--no-sync", "python", "demo_app.py"]
