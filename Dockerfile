# ---- Build stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv for fast pip
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies to /app/.venv
RUN uv sync --frozen --no-dev

# ---- Runtime stage ----
FROM python:3.11-slim

WORKDIR /app

# Copy virtual env from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Use venv python
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Run with gunicorn for production
CMD ["gunicorn", "app.main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]