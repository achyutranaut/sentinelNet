import warnings

warnings.warn(
    "Package 'src.tier2_anomaly' is deprecated and will be removed in SentinelNet 2.0. "
    "Import directly from 'src.models.anomaly_autoencoder' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.models.anomaly_autoencoder import (
    AnomalyAutoencoder,
    AutoencoderMetrics,
    AutoencoderNet,
)

__all__ = ["AnomalyAutoencoder", "AutoencoderMetrics", "AutoencoderNet"]

