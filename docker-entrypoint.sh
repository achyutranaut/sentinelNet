#!/bin/sh
set -e

# Guard against volume shadowing:
# If the mounted artifacts volume is empty or missing model bundle/manifest,
# bootstrap it from the pre-built container cache or run quick training.
if [ ! -f "/app/artifacts/registry/registry_manifest.json" ] || [ -z "$(ls -A /app/artifacts/models 2>/dev/null)" ]; then
    echo "[SentinelNet Entrypoint] No production model found in /app/artifacts. Initializing from image cache..."
    mkdir -p /app/artifacts/models /app/artifacts/registry /app/data
    if [ -d "/app/default_artifacts" ] && [ -n "$(ls -A /app/default_artifacts 2>/dev/null)" ]; then
        cp -rn /app/default_artifacts/* /app/artifacts/ 2>/dev/null || cp -r /app/default_artifacts/* /app/artifacts/
    else
        echo "[SentinelNet Entrypoint] Running continuous training bootstrap..."
        PYTHONPATH=. python src/pipeline.py --quick
    fi
fi

exec "$@"
