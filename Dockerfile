FROM python:3.11-slim

WORKDIR /app

# Install only runtime Python dependencies (skips building the project wheel)
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --prefer-binary $(python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
    print(' '.join(data['project']['dependencies']))
")

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
