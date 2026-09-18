"""Tier 1: Known-Signature Supervised Classifier (LightGBM) for SentinelNet.

Trains an ultra-fast gradient boosted decision tree classifier exclusively on flow
behavioral features (excluding metadata like IP addresses to prevent memorization).
Benchmarked against Tier 0 on accuracy, PR-AUC, recall, latency, and expected dollar loss.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
import yaml


class Tier1SupervisedClassifier:
    """LightGBM supervised flow classifier."""

    def __init__(
        self,
        n_estimators: int = 150,
        learning_rate: float = 0.05,
        max_depth: int = 6,
        num_leaves: int = 31,
        class_weight: str = "balanced",
        eval_metric: str = "binary_logloss",
        early_stopping_rounds: int = 15,
        random_state: int = 42
    ):
        self.params = {
            "n_estimators": n_estimators,
            "learning_rate": learning_rate,
            "max_depth": max_depth,
            "num_leaves": num_leaves,
            "class_weight": class_weight,
            "random_state": random_state,
            "verbose": -1,
            "n_jobs": -1
        }
        self.eval_metric = eval_metric
        self.early_stopping_rounds = early_stopping_rounds
        self.model: Optional[lgb.LGBMClassifier] = None
        self.feature_names: Optional[List[str]] = None

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> "Tier1SupervisedClassifier":
        """Trains LightGBM with early stopping on validation loss."""
        self.feature_names = feature_names
        self.model = lgb.LGBMClassifier(**self.params)
        
        callbacks = [
            lgb.early_stopping(stopping_rounds=self.early_stopping_rounds, verbose=False)
        ]
        
        start_t = time.perf_counter()
        self.model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            eval_metric=self.eval_metric,
            callbacks=callbacks
        )
        fit_time = time.perf_counter() - start_t
        print(f"[+] LightGBM trained in {fit_time:.3f}s (best iteration: {self.model.best_iteration_})")
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Returns malicious probability (class 1)."""
        if self.model is None:
            raise RuntimeError("Model must be fitted before predict_proba.")
        return self.model.predict_proba(X)[:, 1]

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Returns binary predictions at the specified decision threshold."""
        probs = self.predict_proba(X)
        return (probs >= threshold).astype(int)

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
        test_metadata: pd.DataFrame,
        threshold: float = 0.5,
        cost_fn: float = 50000.0,
        cost_fp: float = 50.0
    ) -> Dict[str, Any]:
        """Evaluates model performance and financial loss against test set."""
        start_t = time.perf_counter()
        probs = self.predict_proba(X_test)
        latency_us = ((time.perf_counter() - start_t) / len(X_test)) * 1_000_000.0

        y_pred = (probs >= threshold).astype(int)

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_test, probs)
        pr_auc = average_precision_score(y_test, probs)

        fn = int(np.sum((y_test == 1) & (y_pred == 0)))
        fp = int(np.sum((y_test == 0) & (y_pred == 1)))
        tp = int(np.sum((y_test == 1) & (y_pred == 1)))
        tn = int(np.sum((y_test == 0) & (y_pred == 0)))
        total_cost = (fn * cost_fn) + (fp * cost_fp)

        # Breakdown by attack type
        attack_recall = {}
        for attack_name in test_metadata["attack_type"].unique():
            if attack_name == "BENIGN":
                continue
            idx = (test_metadata["attack_type"] == attack_name).to_numpy()
            sub_true = y_test[idx]
            sub_pred = y_pred[idx]
            attack_recall[attack_name] = float(recall_score(sub_true, sub_pred, zero_division=0))

        return {
            "tier": "Tier 1 (LightGBM Supervised)",
            "threshold": threshold,
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "roc_auc": float(roc_auc),
            "pr_auc": float(pr_auc),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "total_dollar_loss": float(total_cost),
            "latency_us_per_sample": float(latency_us),
            "attack_type_recall": attack_recall
        }

    def save(self, filepath: str) -> None:
        joblib.dump({
            "model": self.model,
            "params": self.params,
            "feature_names": self.feature_names
        }, filepath)

    @classmethod
    def load(cls, filepath: str) -> "Tier1SupervisedClassifier":
        data = joblib.load(filepath)
        instance = cls(**data["params"])
        instance.model = data["model"]
        instance.feature_names = data.get("feature_names")
        return instance


def run_tier1_benchmark(config_path: str = "configs/config.yaml"):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    lgb_cfg = config["models"]["supervised_lightgbm"]
    splits = joblib.load("data/processed/dataset_splits.joblib")

    classifier = Tier1SupervisedClassifier(
        n_estimators=lgb_cfg.get("n_estimators", 150),
        learning_rate=lgb_cfg.get("learning_rate", 0.05),
        max_depth=lgb_cfg.get("max_depth", 6),
        num_leaves=lgb_cfg.get("num_leaves", 31),
        class_weight=lgb_cfg.get("class_weight", "balanced"),
        early_stopping_rounds=lgb_cfg.get("early_stopping_rounds", 15),
        random_state=config["system"].get("random_seed", 42)
    )

    print("=" * 60)
    print(">>> TIER 1 SUPERVISED LIGHTGBM TRAINING & BENCHMARK")
    print("=" * 60)
    classifier.fit(
        splits.X_train_supervised,
        splits.y_train_supervised,
        splits.X_val,
        splits.y_val,
        feature_names=splits.feature_names
    )

    # Save model
    model_path = "artifacts/models/tier1_lightgbm.joblib"
    classifier.save(model_path)
    print(f"[+] Model saved to {model_path}")

    # Evaluate at default 0.5 threshold
    results = classifier.evaluate(
        splits.X_test,
        splits.y_test,
        splits.test_metadata
    )

    print("\n" + "=" * 60)
    print(">>> TIER 1 EVALUATION RESULTS (threshold=0.5)")
    print("=" * 60)
    print(f"Accuracy:        {results['accuracy']:.4f}")
    print(f"Precision:       {results['precision']:.4f}")
    print(f"Recall:          {results['recall']:.4f}")
    print(f"F1-Score:        {results['f1']:.4f}")
    print(f"ROC-AUC:         {results['roc_auc']:.4f}")
    print(f"PR-AUC:          {results['pr_auc']:.4f}")
    print(f"Latency:         {results['latency_us_per_sample']:.2f} µs/sample")
    print(f"TP: {results['tp']} | FP: {results['fp']} | FN: {results['fn']} | TN: {results['tn']}")
    print(f"Expected Financial Loss: ${results['total_dollar_loss']:,.2f}")
    print("\nRecall by Attack Category:")
    for atk, rec in results["attack_type_recall"].items():
        print(f"  - {atk:<26}: {rec * 100:.1f}%")
    print("=" * 60)

    # Compare with Tier 0
    tier0_metrics = joblib.load("artifacts/tier0_metrics.joblib")
    dollar_savings = tier0_metrics["total_dollar_loss"] - results["total_dollar_loss"]
    print(f"[+] Marginal Dollar Risk Reduction over Tier 0: ${dollar_savings:,.2f}")

    joblib.dump(results, "artifacts/tier1_metrics.joblib")
    return results


if __name__ == "__main__":
    run_tier1_benchmark()
