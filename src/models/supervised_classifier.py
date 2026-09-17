"""Tier 1: High-Throughput Supervised Flow Classifier for SentinelNet.

Employs LightGBM gradient boosted decision trees for sub-millisecond per-flow scoring
of known attack signatures (DDoS, Port Scan, SSH/FTP Brute Force).
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import joblib
import lightgbm as lgb
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class ClassifierMetrics:
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float
    per_attack_recall: Dict[str, float]


class SupervisedFlowClassifier:
    """Supervised LightGBM classifier for known attack signature detection."""

    def __init__(
        self,
        n_estimators: int = 150,
        learning_rate: float = 0.05,
        max_depth: int = 6,
        num_leaves: int = 31,
        random_state: int = 42
    ):
        self.params = {
            "n_estimators": n_estimators,
            "learning_rate": learning_rate,
            "max_depth": max_depth,
            "num_leaves": num_leaves,
            "random_state": random_state,
            "class_weight": "balanced",
            "verbosity": -1,
            "n_jobs": -1
        }
        self.model = lgb.LGBMClassifier(**self.params)
        self.is_trained = False
        self.feature_names: List[str] = []

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None
    ) -> "SupervisedFlowClassifier":
        """Trains the LightGBM classifier on known attack signatures."""
        if feature_names:
            self.feature_names = feature_names

        eval_set = [(X_val, y_val)] if (X_val is not None and y_val is not None) else None
        callbacks = [lgb.early_stopping(stopping_rounds=15, verbose=False)] if eval_set else None

        self.model.fit(
            X_train,
            y_train,
            eval_set=eval_set,
            callbacks=callbacks
        )
        self.is_trained = True
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Computes calibrated probability of attack P(attack | flow)."""
        if not self.is_trained:
            raise RuntimeError("Model must be trained before inference.")
        return self.model.predict_proba(X)[:, 1]

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Predicts binary classification based on decision threshold."""
        probs = self.predict_proba(X)
        return (probs >= threshold).astype(np.int64)

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
        test_metadata: Optional[Any] = None,
        threshold: float = 0.5
    ) -> ClassifierMetrics:
        """Comprehensive evaluation including overall and per-attack-type recall."""
        probs = self.predict_proba(X_test)
        preds = (probs >= threshold).astype(np.int64)

        acc = float(accuracy_score(y_test, preds))
        prec = float(precision_score(y_test, preds, zero_division=0))
        rec = float(recall_score(y_test, preds, zero_division=0))
        f1 = float(f1_score(y_test, preds, zero_division=0))
        roc = float(roc_auc_score(y_test, probs))
        pr_auc = float(average_precision_score(y_test, probs))

        per_attack_recall = {}
        if test_metadata is not None and "attack_type" in test_metadata.columns:
            for atk in test_metadata["attack_type"].unique():
                mask = (test_metadata["attack_type"] == atk).to_numpy()
                if mask.sum() > 0:
                    if atk == "BENIGN":
                        fp_rate = float(preds[mask].mean())
                        per_attack_recall["BENIGN_FALSE_ALARM_RATE"] = fp_rate
                        per_attack_recall["BENIGN_SPECIFICITY"] = 1.0 - fp_rate
                    else:
                        per_attack_recall[atk] = float(preds[mask].mean())

        return ClassifierMetrics(
            accuracy=acc,
            precision=prec,
            recall=rec,
            f1=f1,
            roc_auc=roc,
            pr_auc=pr_auc,
            per_attack_recall=per_attack_recall
        )

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns normalized feature importances."""
        if not self.is_trained:
            raise RuntimeError("Model must be trained.")
        raw_imp = self.model.feature_importances_
        norm_imp = raw_imp / (raw_imp.sum() + 1e-12)
        names = self.feature_names if self.feature_names else [f"f_{i}" for i in range(len(raw_imp))]
        return dict(sorted(zip(names, norm_imp), key=lambda x: x[1], reverse=True))

    def save(self, filepath: str) -> None:
        """Saves model and metadata to disk."""
        joblib.dump({
            "model": self.model,
            "feature_names": self.feature_names,
            "is_trained": self.is_trained,
            "params": self.params
        }, filepath)

    @classmethod
    def load(cls, filepath: str) -> "SupervisedFlowClassifier":
        """Loads model from disk."""
        data = joblib.load(filepath)
        instance = cls()
        instance.model = data["model"]
        instance.feature_names = data["feature_names"]
        instance.is_trained = data["is_trained"]
        instance.params = data["params"]
        return instance
