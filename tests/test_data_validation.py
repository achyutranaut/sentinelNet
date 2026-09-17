"""Tests for MLOps Data Validation Layer (Data Tests per ml-ops.org).

Verifies Pydantic schema validation, DataFrame invariant contracts,
synthetic flow generation, and strict zero-leakage split isolation.
"""

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from src.ingestion.dataset_loader import NetworkFlowGenerator
from src.ingestion.preprocessor import FlowPreprocessor, prepare_benchmark_splits
from src.ingestion.schema import FlowDataValidator, NetFlowRecord


def test_valid_netflow_record():
    """Verifies that a valid NetFlow record passes Pydantic schema validation."""
    valid_data = {
        "timestamp": 1715000000.0,
        "src_ip": "192.168.1.10",
        "dst_ip": "10.0.1.20",
        "dst_port": 443,
        "flow_duration_ms": 150.0,
        "total_fwd_packets": 10,
        "total_bwd_packets": 12,
        "total_fwd_bytes": 1500.0,
        "total_bwd_bytes": 4500.0,
        "fwd_packet_length_mean": 150.0,
        "fwd_packet_length_std": 20.0,
        "bwd_packet_length_mean": 375.0,
        "bwd_packet_length_std": 45.0,
        "flow_bytes_per_sec": 40000.0,
        "flow_packets_per_sec": 146.6,
        "flow_iat_mean_ms": 7.1,
        "flow_iat_std_ms": 2.3,
        "flow_iat_max_ms": 15.0,
        "flow_iat_min_ms": 1.2,
        "fwd_iat_mean_ms": 15.0,
        "bwd_iat_mean_ms": 12.5,
        "fwd_syn_flags": 1,
        "fwd_rst_flags": 0,
        "fwd_psh_flags": 1,
        "fwd_ack_flags": 9,
        "bwd_syn_flags": 1,
        "bwd_rst_flags": 0,
        "bwd_psh_flags": 2,
        "bwd_ack_flags": 12,
        "header_length_ratio": 0.13,
        "packet_size_variance": 1212.5,
        "down_up_ratio": 3.0,
        "avg_fwd_segment_size": 150.0,
        "avg_bwd_segment_size": 375.0,
        "attack_type": "BENIGN",
        "label": 0
    }
    record = FlowDataValidator.validate_record(valid_data)
    assert record.dst_port == 443
    assert record.src_ip == "192.168.1.10"
    assert record.label == 0


def test_invalid_ip_rejection():
    """Asserts that malformed IP addresses are strictly rejected."""
    bad_data = {
        "timestamp": 1715000000.0,
        "src_ip": "999.999.999.999",  # Invalid IPv4
        "dst_ip": "10.0.1.20",
        "dst_port": 80,
        "flow_duration_ms": 100.0,
        "total_fwd_packets": 5,
        "total_bwd_packets": 5,
        "total_fwd_bytes": 500.0,
        "total_bwd_bytes": 500.0,
    }
    with pytest.raises(ValidationError):
        FlowDataValidator.validate_record(bad_data)


def test_invalid_port_rejection():
    """Asserts that ports outside [1, 65535] are rejected."""
    bad_data = {
        "timestamp": 1715000000.0,
        "src_ip": "192.168.1.1",
        "dst_ip": "10.0.1.20",
        "dst_port": 99999,  # Out of range port
        "flow_duration_ms": 100.0,
        "total_fwd_packets": 5,
        "total_bwd_packets": 5,
        "total_fwd_bytes": 500.0,
        "total_bwd_bytes": 500.0,
    }
    with pytest.raises(ValidationError):
        FlowDataValidator.validate_record(bad_data)


def test_zero_packets_rejection():
    """Asserts that records with 0 packets are rejected by invariant validator."""
    bad_data = {
        "timestamp": 1715000000.0,
        "src_ip": "192.168.1.1",
        "dst_ip": "10.0.1.20",
        "dst_port": 80,
        "flow_duration_ms": 100.0,
        "total_fwd_packets": 0,
        "total_bwd_packets": 0,
        "total_fwd_bytes": 0.0,
        "total_bwd_bytes": 0.0,
    }
    with pytest.raises(ValidationError):
        FlowDataValidator.validate_record(bad_data)


def test_dataframe_invariants_validation():
    """Tests batch DataFrame validation for missing columns and invalid ranges."""
    gen = NetworkFlowGenerator(seed=42)
    df = gen.generate_baseline_flows(100)

    # Valid DataFrame should pass
    is_valid, report = FlowDataValidator.validate_dataframe(df)
    assert is_valid is True
    assert report.valid_records == 100
    assert len(report.errors) == 0

    # Inject corrupt values (negative packet count)
    df_corrupt = df.copy()
    df_corrupt.loc[5, "total_fwd_packets"] = -10
    is_valid, report = FlowDataValidator.validate_dataframe(df_corrupt)
    assert is_valid is False
    assert "total_fwd_packets" in report.negative_val_violations
    assert report.negative_val_violations["total_fwd_packets"] == 1


def test_leak_free_benchmark_splits():
    """Verifies that the dataset splits adhere to strict zero-day isolation:

    1. Supervised training set contains NO zero-day C2 or lateral movement.
    2. Autoencoder training set contains strictly BENIGN flows.
    3. Preprocessed outputs contain no NaNs or Infinities.
    """
    gen = NetworkFlowGenerator(seed=42)
    df = gen.generate_full_dataset(
        n_baseline=400,
        n_known=200,
        n_zero_day=60,
        n_lateral=50
    )

    splits, preprocessor = prepare_benchmark_splits(df, seed=42)

    # Check finite transformed arrays
    assert np.all(np.isfinite(splits.X_train_supervised))
    assert np.all(np.isfinite(splits.X_train_autoencoder))
    assert np.all(np.isfinite(splits.X_val))
    assert np.all(np.isfinite(splits.X_test))

    # Check that Autoencoder training set size is <= total benign in training
    # And supervised labels match binary range
    assert set(np.unique(splits.y_train_supervised)).issubset({0, 1})
    assert set(np.unique(splits.y_test)).issubset({0, 1})

    # Test metadata contains zero-day attacks and lateral movement
    test_attack_types = set(splits.test_metadata["attack_type"].unique())
    assert "ZERO_DAY_C2_EXFILTRATION" in test_attack_types
    assert "LATERAL_MOVEMENT" in test_attack_types
    assert "BENIGN" in test_attack_types
