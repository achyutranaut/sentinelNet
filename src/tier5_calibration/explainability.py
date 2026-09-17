"""Tier 5: TreeSHAP Explainability Engine Shim.

Re-exports IncidentExplainabilityEngine, IncidentTriageSummary, and FlowFeatureExplanation from src.ops.explainability.
"""

from src.ops.explainability import (
    FlowFeatureExplanation,
    IncidentExplainabilityEngine,
    IncidentTriageSummary,
)

__all__ = [
    "IncidentExplainabilityEngine",
    "IncidentTriageSummary",
    "FlowFeatureExplanation",
]
