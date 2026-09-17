"""Serving Package (FastAPI Production Inference).

Exposes the production FastAPI application instance.
"""

from src.api.app import app

__all__ = ["app"]
