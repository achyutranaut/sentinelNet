"""Tier 0: Static Deterministic Heuristic Baseline Package.

Exposes the rule-based heuristic detector used as the non-ML baseline yardstick.
"""

from src.tier0_baseline.baseline_rules import Tier0HeuristicDetector, run_tier0_benchmark

__all__ = ["Tier0HeuristicDetector", "run_tier0_benchmark"]
