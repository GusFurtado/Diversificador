# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv for fast package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev deps in production)
RUN uv sync --no-dev --no-install-project

# Copy the package source
COPY markowizard/ markowizard/
COPY backend/ backend/
COPY frontend/ frontend/
COPY README.md .

# Build and install the package
RUN uv sync --no-dev

# --- Runtime stage ---
FROM python:3.12-slim

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy frontend and backend
COPY --from=builder /app/frontend /app/frontend
COPY --from=builder /app/backend /app/backend

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]