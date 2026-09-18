import warnings

warnings.warn(
    "Package 'src.tier1_supervised' is deprecated and will be removed in SentinelNet 2.0. "
    "Import directly from 'src.models.supervised_classifier' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.models.supervised_classifier import (
    ClassifierMetrics,
    SupervisedFlowClassifier,
)

__all__ = ["SupervisedFlowClassifier", "ClassifierMetrics"]

