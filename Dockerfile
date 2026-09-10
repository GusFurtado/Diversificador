# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12
ARG UV_VERSION=0.9.28

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# --- Build stage ---
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /app
COPY --from=uv /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# 1. Library dependencies — cached on the lockfile
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# 2. The library itself, installed non-editable so it lands in site-packages
COPY markowizard/ markowizard/
COPY README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# 3. Web-server dependencies (not part of the published library)
COPY backend/requirements.txt ./backend/requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python /app/.venv/bin/python -r backend/requirements.txt

# --- Runtime stage ---
FROM python:${PYTHON_VERSION}-slim

WORKDIR /app
RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app backend/ ./backend/
COPY --chown=app:app frontend/ ./frontend/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=2)"

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
