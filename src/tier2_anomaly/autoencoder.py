"""Tier 2: Unsupervised Zero-Day Anomaly Detector (PyTorch Autoencoder).

Trained exclusively on benign network traffic (Y=0). Learns normal network
communication manifolds. Flows with reconstruction loss exceeding an empirical
percentile threshold are flagged as novel or zero-day anomalies.
Demonstrates detection capability on attacks that bypass Tier 1.
"""

import time
from typing import Any, Dict, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import yaml


class FlowAutoencoderNet(nn.Module):
    """Symmetric bottleneck feed-forward autoencoder."""

    def __init__(self, input_dim: int = 30, latent_dim: int = 4):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 20),
            nn.BatchNorm1d(20),
            nn.LeakyReLU(0.1),
            nn.Linear(20, 10),
            nn.BatchNorm1d(10),
            nn.LeakyReLU(0.1),
            nn.Linear(10, latent_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 10),
            nn.BatchNorm1d(10),
            nn.LeakyReLU(0.1),
            nn.Linear(10, 20),
            nn.BatchNorm1d(20),
            nn.LeakyReLU(0.1),
            nn.Linear(20, input_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        return self.decoder(z)


class Tier2AnomalyAutoencoder:
    """Manages PyTorch Autoencoder training, threshold calibration, and scoring."""

    def __init__(
        self,
        input_dim: int = 30,
        latent_dim: int = 4,
        learning_rate: float = 0.001,
        weight_decay: float = 0.0001,
        epochs: int = 25,
        batch_size: int = 64,
        threshold_percentile: float = 98.5,
        device: Optional[str] = None
    ):
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.epochs = epochs
        self.batch_size = batch_size
        self.threshold_percentile = threshold_percentile
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        self.net = FlowAutoencoderNet(input_dim, latent_dim).to(self.device)
        self.threshold: float = 0.0
        self.is_trained: bool = False

    def fit(self, X_benign_train: np.ndarray, X_benign_val: Optional[np.ndarray] = None) -> "Tier2AnomalyAutoencoder":
        """Trains autoencoder strictly on benign flows to learn baseline manifold."""
        tensor_x = torch.tensor(X_benign_train, dtype=torch.float32)
        dataset = TensorDataset(tensor_x)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True, drop_last=True)

        criterion = nn.MSELoss()
        optimizer = torch.optim.AdamW(self.net.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)

        self.net.train()
        start_t = time.perf_counter()
        for epoch in range(self.epochs):
            total_loss = 0.0
            for (batch_x,) in loader:
                batch_x = batch_x.to(self.device)
                optimizer.zero_grad()
                recon = self.net(batch_x)
                loss = criterion(recon, batch_x)
                loss.backward()
                optimizer.step()
                total_loss += loss.item() * len(batch_x)

            if (epoch + 1) % 5 == 0 or epoch == self.epochs - 1:
                avg_loss = total_loss / len(X_benign_train)
                print(f"[*] Epoch [{epoch+1:02d}/{self.epochs:02d}] - Benign Reconstruction MSE: {avg_loss:.5f}")

        self.is_trained = True
        train_time = time.perf_counter() - start_t
        print(f"[+] Autoencoder trained in {train_time:.2f}s")

        # Calibrate threshold on benign validation or training data
        val_data = X_benign_val if X_benign_val is not None else X_benign_train
        val_errors = self.compute_reconstruction_error(val_data)
        self.threshold = float(np.percentile(val_errors, self.threshold_percentile))
        print(f"[+] Calibrated Anomaly Threshold ({self.threshold_percentile}th percentile): {self.threshold:.4f}")
        return self

    def compute_reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        """Computes per-sample Mean Squared Error between input and reconstruction."""
        self.net.eval()
        tensor_x = torch.tensor(X, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            recon = self.net(tensor_x)
            # Row-wise MSE
            mse = torch.mean((tensor_x - recon) ** 2, dim=1).cpu().numpy()
        return mse

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Returns binary predictions: 1 if reconstruction error exceeds threshold, else 0."""
        errors = self.compute_reconstruction_error(X)
        return (errors > self.threshold).astype(int)

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
        test_metadata: pd.DataFrame,
        cost_fn: float = 50000.0,
        cost_fp: float = 50.0
    ) -> Dict[str, Any]:
        """Evaluates autoencoder anomaly detection performance on the benchmark test set."""
        start_t = time.perf_counter()
        errors = self.compute_reconstruction_error(X_test)
        latency_us = ((time.perf_counter() - start_t) / len(X_test)) * 1_000_000.0

        y_pred = (errors > self.threshold).astype(int)

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_test, errors)

        fn = int(np.sum((y_test == 1) & (y_pred == 0)))
        fp = int(np.sum((y_test == 0) & (y_pred == 1)))
        tp = int(np.sum((y_test == 1) & (y_pred == 1)))
        tn = int(np.sum((y_test == 0) & (y_pred == 0)))
        total_cost = (fn * cost_fn) + (fp * cost_fp)

        # Breakdown by attack category
        attack_recall = {}
        attack_mean_mse = {}
        for attack_name in test_metadata["attack_type"].unique():
            idx = (test_metadata["attack_type"] == attack_name).to_numpy()
            sub_true = y_test[idx]
            sub_pred = y_pred[idx]
            sub_err = errors[idx]
            attack_mean_mse[attack_name] = float(np.mean(sub_err))
            if attack_name != "BENIGN":
                attack_recall[attack_name] = float(recall_score(sub_true, sub_pred, zero_division=0))

        benign_fp_rate = float(fp / max(1, (fp + tn)))

        return {
            "tier": "Tier 2 (PyTorch Anomaly Autoencoder)",
            "threshold": float(self.threshold),
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "roc_auc": float(roc_auc),
            "benign_fp_rate": benign_fp_rate,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "total_dollar_loss": float(total_cost),
            "latency_us_per_sample": float(latency_us),
            "attack_type_recall": attack_recall,
            "mean_reconstruction_mse": attack_mean_mse
        }

    def save(self, filepath: str) -> None:
        torch.save({
            "state_dict": self.net.state_dict(),
            "threshold": self.threshold,
            "input_dim": self.input_dim,
            "latent_dim": self.latent_dim,
            "threshold_percentile": self.threshold_percentile
        }, filepath)

    @classmethod
    def load(cls, filepath: str, device: Optional[str] = None) -> "Tier2AnomalyAutoencoder":
        dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
        checkpoint = torch.load(filepath, map_location=dev, weights_only=True)
        instance = cls(
            input_dim=checkpoint["input_dim"],
            latent_dim=checkpoint["latent_dim"],
            threshold_percentile=checkpoint.get("threshold_percentile", 98.5),
            device=dev
        )
        instance.net.load_state_dict(checkpoint["state_dict"])
        instance.threshold = checkpoint["threshold"]
        instance.is_trained = True
        return instance


def run_tier2_benchmark(config_path: str = "configs/config.yaml"):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    ae_cfg = config["models"]["anomaly_autoencoder"]
    splits = joblib.load("data/processed/dataset_splits.joblib")

    # Extract benign validation flows for threshold calibration
    benign_val_mask = splits.val_metadata["attack_type"] == "BENIGN"
    X_val_benign = splits.X_val[benign_val_mask]

    detector = Tier2AnomalyAutoencoder(
        input_dim=splits.X_train_autoencoder.shape[1],
        latent_dim=ae_cfg.get("latent_dim", 4),
        learning_rate=ae_cfg.get("learning_rate", 0.001),
        weight_decay=ae_cfg.get("weight_decay", 0.0001),
        epochs=ae_cfg.get("epochs", 25),
        batch_size=ae_cfg.get("batch_size", 64),
        threshold_percentile=ae_cfg.get("reconstruction_threshold_percentile", 98.5)
    )

    print("=" * 60)
    print(">>> TIER 2 ZERO-DAY ANOMALY AUTOENCODER TRAINING")
    print(f"    (Trained strictly on {len(splits.X_train_autoencoder)} BENIGN flows)")
    print("=" * 60)
    detector.fit(splits.X_train_autoencoder, X_val_benign)

    # Save model
    model_path = "artifacts/models/tier2_autoencoder.pt"
    detector.save(model_path)
    print(f"[+] Autoencoder model saved to {model_path}")

    # Evaluate on test set
    results = detector.evaluate(
        splits.X_test,
        splits.y_test,
        splits.test_metadata
    )

    print("\n" + "=" * 60)
    print(">>> TIER 2 EVALUATION RESULTS")
    print("=" * 60)
    print(f"Accuracy:        {results['accuracy']:.4f}")
    print(f"Precision:       {results['precision']:.4f}")
    print(f"Recall:          {results['recall']:.4f}")
    print(f"F1-Score:        {results['f1']:.4f}")
    print(f"ROC-AUC:         {results['roc_auc']:.4f}")
    print(f"Benign FP Rate:  {results['benign_fp_rate'] * 100:.2f}%")
    print(f"Latency:         {results['latency_us_per_sample']:.2f} µs/sample")
    print(f"TP: {results['tp']} | FP: {results['fp']} | FN: {results['fn']} | TN: {results['tn']}")
    print(f"Expected Financial Loss: ${results['total_dollar_loss']:,.2f}")
    print("\nRecall by Attack Category:")
    for atk, rec in results["attack_type_recall"].items():
        print(f"  - {atk:<26}: {rec * 100:.1f}%")
    print("\nMean Reconstruction MSE by Traffic Class:")
    for atk, mse in results["mean_reconstruction_mse"].items():
        print(f"  - {atk:<26}: {mse:.4f}")
    print("=" * 60)

    # Compare with Tier 1 on Zero-Day Detection
    tier1_metrics = joblib.load("artifacts/tier1_metrics.joblib")
    zday_t1 = tier1_metrics["attack_type_recall"]["ZERO_DAY_C2_EXFILTRATION"]
    zday_t2 = results["attack_type_recall"]["ZERO_DAY_C2_EXFILTRATION"]
    print(f"\n[+] ZERO-DAY C2 CATCH RATE: Tier 1 = {zday_t1 * 100:.1f}%  ==>  Tier 2 = {zday_t2 * 100:.1f}%")

    joblib.dump(results, "artifacts/tier2_metrics.joblib")
    return results


if __name__ == "__main__":
    run_tier2_benchmark()
