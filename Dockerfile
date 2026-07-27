FROM python:3.11-slim

WORKDIR /app

# Install system deps needed for some wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency file only (skips building the project wheel entirely)
COPY pyproject.toml ./

# Extract and install deps directly — no wheel build, no hatchling
RUN python3 -c "
import tomllib, subprocess
with open('pyproject.toml', 'rb') as f:
    deps = tomllib.load(f)['project']['dependencies']
subprocess.check_call(['pip', 'install', '--no-cache-dir', '--prefer-binary', *deps])
"

# Copy application code
COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
