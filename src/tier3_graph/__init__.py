import warnings

warnings.warn(
    "Package 'src.tier3_graph' is deprecated and will be removed in SentinelNet 2.0. "
    "Import directly from 'src.graph.lateral_tracker' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.graph.lateral_tracker import (
    GraphAnomalyReport,
    HostThreatScore,
    TemporalLateralTracker,
)

__all__ = ["TemporalLateralTracker", "HostThreatScore", "GraphAnomalyReport"]

