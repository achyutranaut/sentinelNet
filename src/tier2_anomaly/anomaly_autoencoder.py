"""Tier 2: Deep Autoencoder Shim.

Re-exports AnomalyAutoencoder, AutoencoderMetrics, and AutoencoderNet from src.models.anomaly_autoencoder.
"""

from src.models.anomaly_autoencoder import (
    AnomalyAutoencoder,
    AutoencoderMetrics,
    AutoencoderNet,
)

__all__ = ["AnomalyAutoencoder", "AutoencoderMetrics", "AutoencoderNet"]
