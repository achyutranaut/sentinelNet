"""Tier 4: Adversarial Evasion & Traffic Perturbation Engine Package.

Simulates domain perturbations and gradient evasion attacks to benchmark resilience.
"""

from src.adversarial.perturbation_engine import (
    RobustnessCurvePoint,
    TrafficPerturbationEngine,
)

__all__ = ["TrafficPerturbationEngine", "RobustnessCurvePoint"]
