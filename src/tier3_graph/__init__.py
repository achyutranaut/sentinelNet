"""Tier 3: Temporal Network Interaction Graph Package.

Tracks host-to-host interaction topology over sliding windows to detect lateral movement.
"""

from src.graph.lateral_tracker import (
    GraphAnomalyReport,
    HostThreatScore,
    TemporalLateralTracker,
)

__all__ = ["TemporalLateralTracker", "HostThreatScore", "GraphAnomalyReport"]
