import warnings

warnings.warn(
    "Package 'src.tier4_adversarial' is deprecated and will be removed in SentinelNet 2.0. "
    "Import directly from 'src.adversarial.perturbation_engine' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.adversarial.perturbation_engine import (
    RobustnessCurvePoint,
    TrafficPerturbationEngine,
)

__all__ = ["TrafficPerturbationEngine", "RobustnessCurvePoint"]

