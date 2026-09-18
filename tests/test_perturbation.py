"""Tests for Physical Coupling Invariants in Adversarial Perturbations."""

import numpy as np
import pytest
from src.adversarial.perturbation_engine import TrafficPerturbationEngine
from src.ingestion.dataset_loader import NetworkFlowGenerator


def test_perturbation_physical_coupling():
    """Verifies that padding and jitter update derived features consistently."""
    gen = NetworkFlowGenerator(seed=42)
    engine = TrafficPerturbationEngine(seed=42)
    df_clean = gen.generate_known_attacks(10)

    # Apply 30% padding and 150ms jitter
    df_pert = engine.apply_realistic_traffic_perturbation(df_clean, padding_ratio=0.3, jitter_ms=150.0)

    for i in range(len(df_clean)):
        orig = df_clean.iloc[i]
        pert = df_pert.iloc[i]

        # Invariant 1: Forward bytes strictly increased
        assert pert["total_fwd_bytes"] > orig["total_fwd_bytes"]

        # Invariant 2: Flow duration strictly increased
        assert pert["flow_duration_ms"] > orig["flow_duration_ms"]

        # Invariant 3: Recalculated bytes per sec matches physics formula
        expected_duration_sec = pert["flow_duration_ms"] / 1000.0
        expected_total_bytes = pert["total_fwd_bytes"] + pert["total_bwd_bytes"]
        expected_bps = expected_total_bytes / expected_duration_sec

        assert np.isclose(pert["flow_bytes_per_sec"], expected_bps, rtol=1e-3)

        # Invariant 4: Recalculated packets per sec matches physics formula
        expected_total_pkts = pert["total_fwd_packets"] + pert["total_bwd_packets"]
        expected_pps = expected_total_pkts / expected_duration_sec

        assert np.isclose(pert["flow_packets_per_sec"], expected_pps, rtol=1e-3)


def test_perturbation_no_negative_values():
    """Verifies perturbations never introduce negative physical values."""
    gen = NetworkFlowGenerator(seed=42)
    engine = TrafficPerturbationEngine(seed=42)
    df = gen.generate_baseline_flows(20)

    df_pert = engine.apply_realistic_traffic_perturbation(df, padding_ratio=0.5, jitter_ms=300.0)

    numeric_cols = df_pert.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        assert (df_pert[col] >= 0.0).all(), f"Column {col} contained negative values after perturbation"
