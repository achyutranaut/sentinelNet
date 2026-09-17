"""Tier 4: Adversarial Perturbation Engine Shim.

Re-exports TrafficPerturbationEngine and RobustnessCurvePoint from src.adversarial.perturbation_engine.
"""

from src.adversarial.perturbation_engine import (
    RobustnessCurvePoint,
    TrafficPerturbationEngine,
)

__all__ = ["TrafficPerturbationEngine", "RobustnessCurvePoint"]
