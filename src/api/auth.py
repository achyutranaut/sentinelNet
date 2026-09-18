"""Authentication & Authorization for SentinelNet Scoring API (MLOps Security Layer).

Enforces API key verification across REST endpoints and WebSocket streams.
Guards against unauthorized adversarial probing and unauthenticated access.
"""

import os
import secrets
from typing import Optional
from fastapi import Depends, HTTPException, Query, Security, WebSocket, status
from fastapi.security import APIKeyHeader, APIKeyQuery

API_KEY_NAME = "X-API-Key"
DEFAULT_DEV_API_KEY = "sentinel-dev-secret-key-32b"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


def get_expected_api_key() -> str:
    """Retrieves the configured API key from the environment or default development key."""
    return os.getenv("SENTINEL_API_KEY", DEFAULT_DEV_API_KEY)


async def verify_api_key(
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query),
) -> str:
    """Verifies incoming API key from either 'X-API-Key' header or '?api_key=' query param.

    Raises HTTP 401 Unauthorized if missing or invalid. Uses constant-time comparison.
    """
    expected = get_expected_api_key()
    provided = header_key or query_key

    if not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing. Provide header 'X-API-Key: <key>' or query parameter '?api_key=<key>'.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return provided


async def verify_ws_api_key(
    websocket: WebSocket,
    api_key: Optional[str] = Query(None, alias="api_key"),
) -> bool:
    """Verifies API key for WebSocket connections during handshake.

    Checks query parameter '?api_key=' or 'X-API-Key' / 'Sec-WebSocket-Protocol' headers.
    """
    expected = get_expected_api_key()
    provided = api_key or websocket.headers.get("x-api-key")

    if not provided:
        protocols = websocket.headers.get("sec-websocket-protocol", "").split(",")
        for p in protocols:
            p_clean = p.strip()
            if p_clean and secrets.compare_digest(p_clean, expected):
                provided = p_clean
                break

    if not provided or not secrets.compare_digest(provided, expected):
        await websocket.close(code=1008, reason="Unauthorized: Invalid or missing API key.")
        return False

    return True
