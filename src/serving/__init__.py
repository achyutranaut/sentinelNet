import warnings

warnings.warn(
    "Package 'src.serving' is deprecated and will be removed in SentinelNet 2.0. "
    "Import directly from 'src.api.app' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.api.app import app

__all__ = ["app"]

