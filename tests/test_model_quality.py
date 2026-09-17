"""Tests for MLOps Model Quality & Registry Layer (Model Tests per ml-ops.org).

Verifies algorithmic correctness, loss decrease, deterministic reproducibility,
directional sensitivity/monotonicity, and model registry lifecycle operations.
"""

import shutil
import tempfile
import numpy as np
import pytest

from src.ingestion.dataset_loader import NetworkFlowGenerator
from src.ingestion.preprocessor import prepare_benchmark_splits
from src.models.anomaly_autoencoder import AnomalyAutoencoder
from src.models.registry import InferenceBundle, ModelMetadata, ModelRegistry
from src.models.supervised_classifier import SupervisedFlowClassifier


@pytest.fixture(scope="module")
def small_dataset():
    gen = NetworkFlowGenerator(seed=42)
    df = gen.generate_full_dataset(
        n_baseline=300,
        n_known=150,
        n_zero_day=50,
        n_lateral=40
    )
    splits, preprocessor = prepare_benchmark_splits(df, seed=42)
    return df, splits, preprocessor


def test_autoencoder_loss_strictly_decreases(small_dataset):
    """Verifies that the autoencoder optimization converges and loss decreases."""
    _, splits, _ = small_dataset
    ae = AnomalyAutoencoder(
        input_dim=splits.X_train_autoencoder.shape[1],
        latent_dim=4,
        epochs=10,
        batch_size=32,
        random_state=42
    )
    ae.train(splits.X_train_autoencoder)

    assert len(ae.training_loss_history) == 10
    first_loss = ae.training_loss_history[0]
    final_loss = ae.training_loss_history[-1]
    assert final_loss < first_loss, f"Final loss ({final_loss}) was not lower than initial loss ({first_loss})"
    assert ae.threshold is not None
    assert ae.threshold > 0.0


def test_lightgbm_deterministic_reproducibility(small_dataset):
    """Verifies that identical random seeds yield identical predictions (ml-ops.org reproducibility)."""
    _, splits, _ = small_dataset
    clf1 = SupervisedFlowClassifier(n_estimators=30, random_state=42)
    clf1.train(splits.X_train_supervised, splits.y_train_supervised)
    p1 = clf1.predict_proba(splits.X_val)

    clf2 = SupervisedFlowClassifier(n_estimators=30, random_state=42)
    clf2.train(splits.X_train_supervised, splits.y_train_supervised)
    p2 = clf2.predict_proba(splits.X_val)

    np.testing.assert_allclose(p1, p2, atol=1e-6)


def test_directional_monotonicity_sanity(small_dataset):
    """Tests directional expectation: injecting SYN flood features must increase attack probability."""
    raw_df, splits, preprocessor = small_dataset
    clf = SupervisedFlowClassifier(n_estimators=50, random_state=42)
    clf.train(splits.X_train_supervised, splits.y_train_supervised, feature_names=splits.feature_names)

    benign_row = raw_df[raw_df["attack_type"] == "BENIGN"].iloc[0].to_dict()
    prob_benign = clf.predict_proba(preprocessor.transform(benign_row))[0]

    # Perturbed attack flow: massive SYN packets, high packet rate, collapsed response packets
    attack_flow = dict(benign_row)
    attack_flow["total_fwd_packets"] = 500
    attack_flow["total_fwd_bytes"] = 30000.0
    attack_flow["flow_packets_per_sec"] = 50000.0
    attack_flow["down_up_ratio"] = float(attack_flow["total_bwd_bytes"] / attack_flow["total_fwd_bytes"])
    attack_flow["bwd_packet_length_mean"] = 0.0

    prob_attack = clf.predict_proba(preprocessor.transform(attack_flow))[0]

    assert prob_attack > prob_benign, f"Perturbed attack prob ({prob_attack}) not greater than benign ({prob_benign})"


def test_model_registry_lifecycle(small_dataset):
    """Tests model registry registration, metadata lineage, and production promotion."""
    raw_df, splits, preprocessor = small_dataset

    with tempfile.TemporaryDirectory() as temp_dir:
        reg = ModelRegistry(registry_dir=f"{temp_dir}/registry", models_dir=f"{temp_dir}/models")

        clf = SupervisedFlowClassifier(n_estimators=20, random_state=42).train(
            splits.X_train_supervised, splits.y_train_supervised
        )
        ae = AnomalyAutoencoder(input_dim=splits.X_train_autoencoder.shape[1], epochs=5, random_state=42).train(
            splits.X_train_autoencoder
        )

        dataset_hash = reg.compute_dataset_hash(raw_df)
        metadata = ModelMetadata(
            model_id="",
            version="1.0.0-test",
            created_at="2026-09-18T00:00:00Z",
            dataset_hash=dataset_hash,
            status="staging",
            hyperparameters={"n_estimators": 20, "ae_epochs": 5},
            metrics={"f1": 0.95},
            feature_names=splits.feature_names,
            description="Test release bundle"
        )

        bundle = InferenceBundle(
            preprocessor=preprocessor,
            supervised_model=clf,
            autoencoder_model=ae,
            metadata=metadata
        )

        # 1. Register bundle
        model_id = reg.register_bundle(bundle, promote_to_production=False)
        models = reg.list_models()
        assert len(models) == 1
        assert models[0]["status"] == "staging"
        assert models[0]["dataset_hash"] == dataset_hash

        # 2. Promote to production
        reg.promote_to_production(model_id)
        prod_bundle = reg.get_production_bundle()
        assert prod_bundle.metadata.model_id == model_id
        assert prod_bundle.metadata.status == "production"

        # 3. Test unified scoring
        sample_dict = raw_df.iloc[0].to_dict()
        score = prod_bundle.score_single_flow(sample_dict)
        assert "is_attack" in score
        assert "detection_tier" in score
        assert "supervised_probability" in score
        assert "reconstruction_loss" in score
