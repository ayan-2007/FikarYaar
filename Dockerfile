FROM python:3.11-slim

WORKDIR /app

# Copy source + config
COPY pyproject.toml README.md ./

# Install project + all deps (prefer-binary skips native compilation)
RUN pip install --no-cache-dir --prefer-binary .

# Copy the rest of the app
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
