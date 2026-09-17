"""Tests for Training-Serving Skew Elimination (ml-ops.org Skew & Equivalence Tests).

Verifies that passing a flow record through the single-record serving path
produces identical features, probabilities, and reconstruction losses
as passing it through the offline batch training pipeline.
"""

import numpy as np
import pandas as pd
import pytest

from src.ingestion.dataset_loader import NetworkFlowGenerator
from src.ingestion.preprocessor import FlowPreprocessor
from src.models.registry import InferenceBundle, ModelRegistry


def test_training_serving_feature_and_score_equivalence():
    """Asserts that batch DataFrame preprocessing and single dict preprocessing produce identical outputs."""
    registry = ModelRegistry()
    bundle = registry.get_production_bundle()

    gen = NetworkFlowGenerator(seed=123)
    df_sample = gen.generate_full_dataset(n_baseline=10, n_known=5, n_zero_day=2, n_lateral=2)

    # 1. Batch transformation (offline training path)
    X_batch = bundle.preprocessor.transform(df_sample)
    sup_probs_batch = bundle.supervised_model.predict_proba(X_batch)
    ae_recon_batch = bundle.autoencoder_model.compute_reconstruction_error(X_batch)

    # 2. Individual flow scoring (online serving path)
    for i in range(len(df_sample)):
        flow_dict = df_sample.iloc[i].to_dict()

        # Preprocess single record
        X_single = bundle.preprocessor.transform(flow_dict)

        # Vector comparison
        np.testing.assert_allclose(
            X_batch[i],
            X_single[0],
            atol=1e-7,
            err_msg=f"Training-serving feature mismatch detected at sample index {i}"
        )

        # Score comparison
        score = bundle.score_single_flow(flow_dict)
        np.testing.assert_allclose(
            sup_probs_batch[i],
            score["supervised_probability"],
            atol=1e-6,
            err_msg=f"Supervised probability mismatch at index {i}"
        )
        np.testing.assert_allclose(
            ae_recon_batch[i],
            score["reconstruction_loss"],
            atol=1e-5,
            err_msg=f"Autoencoder reconstruction loss mismatch at index {i}"
        )
