"""Continuous Training (CT) Pipeline Orchestrator for SentinelNet (ml-ops.org Automation).

Coordinates end-to-end stages:
1. Data Ingestion & Contract Validation (schema.py)
2. Leak-Free Preprocessing & Scaling (preprocessor.py)
3. Model Training (LightGBM Tier 1 + PyTorch Autoencoder Tier 2)
4. Evaluation & SOC Cost Calibration (cost_calibrator.py)
5. Adversarial Stress-Testing (perturbation_engine.py)
6. Model Registration & Production Promotion (registry.py)
"""

import argparse
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
import yaml

from src.adversarial.perturbation_engine import TrafficPerturbationEngine
from src.ingestion.dataset_loader import NetworkFlowGenerator
from src.ingestion.preprocessor import DatasetSplits, FlowPreprocessor, prepare_benchmark_splits
from src.ingestion.schema import FlowDataValidator
from src.models.anomaly_autoencoder import AnomalyAutoencoder
from src.models.registry import InferenceBundle, ModelMetadata, ModelRegistry
from src.models.supervised_classifier import SupervisedFlowClassifier
from src.ops.cost_calibrator import SOCCostCalibrator


def load_config(config_path: str = "configs/config.yaml") -> Dict[str, Any]:
    """Loads central YAML configuration."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def run_pipeline(
    config_path: str = "configs/config.yaml",
    quick_run: bool = False,
    promote: bool = True
) -> str:
    """Executes the complete MLOps Continuous Training pipeline."""
    cfg = load_config(config_path)
    seed = cfg["system"]["random_seed"]

    print("==================================================================")
    print("           SENTINELNET CONTINUOUS TRAINING (CT) PIPELINE          ")
    print("==================================================================")

    # ------------------------------------------------------------------
    # Stage 1: Data Ingestion & Schema Invariant Validation
    # ------------------------------------------------------------------
    print("\n[Stage 1/5] Ingesting & Validating NetFlow Data...")
    n_base = 2000 if quick_run else cfg["data"]["num_baseline_samples"]
    n_known = 800 if quick_run else cfg["data"]["num_known_attack_samples"]
    n_zero = 250 if quick_run else cfg["data"]["num_zero_day_samples"]
    n_lat = 200 if quick_run else cfg["data"]["num_lateral_movement_samples"]

    generator = NetworkFlowGenerator(seed=seed)
    df_raw = generator.generate_full_dataset(
        n_baseline=n_base,
        n_known=n_known,
        n_zero_day=n_zero,
        n_lateral=n_lat
    )
    print(f"Generated {len(df_raw)} network flow records across 4 attack categories.")

    is_valid, report = FlowDataValidator.validate_dataframe(df_raw, strict=True)
    print(f"Data Schema Validation: PASSED ({report.valid_records}/{report.total_records} valid records).")

    # ------------------------------------------------------------------
    # Stage 2: Leak-Free Preprocessing & Isolation Splits
    # ------------------------------------------------------------------
    print("\n[Stage 2/5] Engineering Features & Preparing Leak-Free Splits...")
    splits, preprocessor = prepare_benchmark_splits(
        df_raw,
        test_ratio=cfg["data"]["test_size"],
        val_ratio=cfg["data"]["val_size"],
        seed=seed
    )
    print(f"Supervised Train Set: {splits.X_train_supervised.shape} (Benign + Known Attacks)")
    print(f"Autoencoder Train Set: {splits.X_train_autoencoder.shape} (Strictly Benign Baseline)")
    print(f"Test Set:             {splits.X_test.shape} (Unseen Benign, Known, Zero-Day, Lateral)")

    # ------------------------------------------------------------------
    # Stage 3: Multi-Tier Model Training
    # ------------------------------------------------------------------
    print("\n[Stage 3/5] Training Multi-Tier Detection Architecture...")
    # Tier 1: LightGBM
    lgb_cfg = cfg["models"]["supervised_lightgbm"]
    n_est = 30 if quick_run else lgb_cfg["n_estimators"]
    supervised_clf = SupervisedFlowClassifier(
        n_estimators=n_est,
        learning_rate=lgb_cfg["learning_rate"],
        max_depth=lgb_cfg["max_depth"],
        num_leaves=lgb_cfg["num_leaves"],
        random_state=seed
    )
    supervised_clf.train(
        splits.X_train_supervised,
        splits.y_train_supervised,
        X_val=splits.X_val,
        y_val=splits.y_val,
        feature_names=splits.feature_names
    )
    print("Tier 1 LightGBM Classifier: Trained successfully.")

    # Tier 2: Deep Autoencoder
    ae_cfg = cfg["models"]["anomaly_autoencoder"]
    epochs = 8 if quick_run else ae_cfg["epochs"]
    batch_size = ae_cfg["batch_size"]
    autoencoder = AnomalyAutoencoder(
        input_dim=splits.X_train_autoencoder.shape[1],
        latent_dim=ae_cfg["latent_dim"],
        learning_rate=ae_cfg["learning_rate"],
        batch_size=batch_size,
        epochs=epochs,
        threshold_percentile=ae_cfg["reconstruction_threshold_percentile"],
        random_state=seed
    )
    autoencoder.train(splits.X_train_autoencoder, feature_names=splits.feature_names)
    print(f"Tier 2 Deep Autoencoder: Trained (Recon threshold calibrated at {autoencoder.threshold:.5f}).")

    # ------------------------------------------------------------------
    # Stage 4: Evaluation, Cost Calibration & Adversarial Stress Testing
    # ------------------------------------------------------------------
    print("\n[Stage 4/5] Evaluating Metrics, SOC Asymmetric Costs & Adversarial Resilience...")
    metrics_clf = supervised_clf.evaluate(splits.X_test, splits.y_test, splits.test_metadata)
    metrics_ae = autoencoder.evaluate(splits.X_test, splits.y_test, splits.test_metadata)

    print(f"Tier 1 Test Precision: {metrics_clf.precision:.4f} | Recall: {metrics_clf.recall:.4f} | PR-AUC: {metrics_clf.pr_auc:.4f}")
    print(f"Tier 2 Benign Recon Loss: {metrics_ae.benign_mean_loss:.4f} | Attack Loss: {metrics_ae.attack_mean_loss:.4f}")

    # SOC Cost Calibration
    soc_cfg = cfg["soc_costs"]
    calibrator = SOCCostCalibrator(
        cost_fn=soc_cfg["cost_false_negative"],
        cost_fp=soc_cfg["cost_false_positive"]
    )
    val_probs = supervised_clf.predict_proba(splits.X_val)
    cost_res = calibrator.calibrate_threshold(splits.y_val, val_probs)
    print(f"SOC Cost Calibration: Optimal Threshold = {cost_res.optimal_threshold:.3f} (Cost Reduction: {cost_res.cost_reduction_percent:.1f}%)")

    # Adversarial Evasion Benchmarking
    pert_engine = TrafficPerturbationEngine(seed=seed)
    attack_mask = (splits.y_test == 1)
    robustness_pts = pert_engine.benchmark_adversarial_robustness(
        supervised_clf,
        autoencoder,
        splits.X_test[attack_mask],
        epsilon_levels=[0.0, 0.1, 0.2, 0.3]
    )
    print(f"Adversarial Robustness (Combined Recall): eps=0.0 -> {robustness_pts[0].combined_recall:.1%}, eps=0.2 -> {robustness_pts[2].combined_recall:.1%}")

    # ------------------------------------------------------------------
    # Stage 5: Artifact Bundling & Model Registry Promotion
    # ------------------------------------------------------------------
    print("\n[Stage 5/5] Packaging Unified Inference Bundle & Updating Model Registry...")
    registry = ModelRegistry(
        registry_dir=cfg["system"]["registry_dir"],
        models_dir=cfg["system"]["models_dir"]
    )

    dataset_hash = registry.compute_dataset_hash(df_raw)
    metrics_summary = {
        "precision": metrics_clf.precision,
        "recall": metrics_clf.recall,
        "f1": metrics_clf.f1,
        "pr_auc": metrics_clf.pr_auc,
        "roc_auc": metrics_clf.roc_auc,
        "ae_threshold": float(autoencoder.threshold),
        "optimal_threshold": cost_res.optimal_threshold,
        "cost_reduction_percent": cost_res.cost_reduction_percent,
        "adversarial_recall_eps_02": robustness_pts[2].combined_recall
    }

    metadata = ModelMetadata(
        model_id="",
        version=cfg["system"]["version"],
        created_at=pd.Timestamp.now("UTC").isoformat(),
        dataset_hash=dataset_hash,
        status="staging",
        hyperparameters={"supervised": lgb_cfg, "autoencoder": ae_cfg},
        metrics=metrics_summary,
        feature_names=splits.feature_names,
        description="Automated CT Pipeline Release"
    )

    bundle = InferenceBundle(
        preprocessor=preprocessor,
        supervised_model=supervised_clf,
        autoencoder_model=autoencoder,
        metadata=metadata
    )

    model_id = registry.register_bundle(bundle, promote_to_production=promote)
    print(f"Model successfully registered as ID: {model_id} (Status: {'PRODUCTION' if promote else 'STAGING'})")

    # Save reference baseline for drift monitoring
    ref_path = Path(cfg["system"]["data_dir"]) / "reference_baseline.joblib"
    ref_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "reference_data": splits.X_train_supervised[:2000],
        "feature_names": splits.feature_names
    }, ref_path)
    print(f"Reference distribution baseline cached to {ref_path}.")

    print("\n==================================================================")
    print("                PIPELINE EXECUTION COMPLETED                      ")
    print("==================================================================")
    return model_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelNet MLOps CT Pipeline")
    parser.add_argument("--config", type=str, default="configs/config.yaml", help="Path to config file")
    parser.add_argument("--quick", action="store_true", help="Run fast pipeline for testing")
    parser.add_argument("--no-promote", action="store_true", help="Do not promote model to production")
    args = parser.parse_args()

    run_pipeline(config_path=args.config, quick_run=args.quick, promote=not args.no_promote)
