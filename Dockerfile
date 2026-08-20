# syntax=docker/dockerfile:1.4
# Note: this build relies on BuildKit features (pip cache mount). Docker 23+
# and Render both enable BuildKit by default.

# ── Base image ────────────────────────────────────────────────
FROM python:3.12-slim

# ── Python runtime behaviour (no .pyc files, unbuffered logs) ─
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ── App directory ─────────────────────────────────────────────
WORKDIR /app

# ── System dependencies (single layer, cleaned, minimal) ──────
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────
# requirements.txt is copied first so this layer stays cached until
# dependencies change; the pip cache mount reuses downloaded wheels
# across builds without adding them to the final image.
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install -r requirements.txt

# ── Project code ──────────────────────────────────────────────
COPY . .

# Runtime directory for collectstatic output + ensure entrypoint is executable
RUN mkdir -p /app/staticfiles \
    && chmod +x /app/docker/entrypoint.sh

# ── Server configuration ──────────────────────────────────────
# Daphne (ASGI) — required for Channels/WebSocket support.
# The entrypoint runs pre-flight steps (R2 sync, migrate, collectstatic),
# then hands off to the CMD below via `exec "$@"`.
ENTRYPOINT ["/app/docker/entrypoint.sh"]

# Shell-form CMD so Render's PORT env var is read at runtime (default 8000)
CMD ["sh", "-c", "daphne -b 0.0.0.0 -p ${PORT:-8000} pu_mp.asgi:application"]

EXPOSE 8000
