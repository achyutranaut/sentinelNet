"""Tier 1: High-Throughput Supervised Flow Classifier Shim.

Re-exports SupervisedFlowClassifier and ClassifierMetrics from src.models.supervised_classifier.
"""

from src.models.supervised_classifier import (
    ClassifierMetrics,
    SupervisedFlowClassifier,
)

__all__ = ["SupervisedFlowClassifier", "ClassifierMetrics"]
