"""Inference & Detection Engine Package.

Exposes the unified inference bundle and traffic perturbation engine.
"""

from src.adversarial.perturbation_engine import TrafficPerturbationEngine
from src.models.registry import InferenceBundle

__all__ = ["TrafficPerturbationEngine", "InferenceBundle"]
