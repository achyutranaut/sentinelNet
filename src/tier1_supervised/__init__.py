"""Tier 1: High-Throughput Supervised Flow Classifier Package.

Provides LightGBM-based sub-millisecond per-flow classification of known attack signatures.
"""

from src.models.supervised_classifier import (
    ClassifierMetrics,
    SupervisedFlowClassifier,
)

__all__ = ["SupervisedFlowClassifier", "ClassifierMetrics"]
