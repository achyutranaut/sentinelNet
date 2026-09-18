# SentinelNet Production MLOps Container
FROM python:3.11-slim

WORKDIR /app

# Install lightweight runtime system dependencies (OpenMP for LightGBM/XGBoost)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and configs
COPY configs/ configs/
COPY src/ src/
COPY tests/ tests/

# Train initial baseline production model bundle
RUN PYTHONPATH=. python src/pipeline.py --quick

# Cache pre-built artifacts to protect against empty host volume shadowing
RUN mkdir -p /app/default_artifacts /app/default_data && \
    cp -r /app/artifacts/* /app/default_artifacts/ 2>/dev/null || true && \
    cp -r /app/data/* /app/default_data/ 2>/dev/null || true

# Copy and configure entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000 8501

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default launch command runs scoring API
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

