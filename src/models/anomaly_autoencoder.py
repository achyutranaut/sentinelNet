"""Tier 2: Deep Autoencoder for Zero-Day Network Anomaly Detection in SentinelNet.

Trained exclusively on benign enterprise network flows. Computes reconstruction error
to surface out-of-distribution patterns (zero-day C2 beacons, covert channels, novel exfiltration)
that bypass supervised signature classifiers.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


class AutoencoderNet(nn.Module):
    """PyTorch Deep Autoencoder with bottleneck compression and batch normalization."""

    def __init__(self, input_dim: int = 30, latent_dim: int = 4):
        super().__init__()
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 20),
            nn.BatchNorm1d(20),
            nn.LeakyReLU(0.1),
            nn.Dropout(0.05),
            nn.Linear(20, 10),
            nn.BatchNorm1d(10),
            nn.LeakyReLU(0.1),
            nn.Linear(10, latent_dim),
        )

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 10),
            nn.BatchNorm1d(10),
            nn.LeakyReLU(0.1),
            nn.Dropout(0.05),
            nn.Linear(10, 20),
            nn.BatchNorm1d(20),
            nn.LeakyReLU(0.1),
            nn.Linear(20, input_dim),
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed, latent


@dataclass
class AutoencoderMetrics:
    threshold: float
    benign_mean_loss: float
    attack_mean_loss: float
    per_attack_recall: Dict[str, float]


class AnomalyAutoencoder:
    """Manager for training, scoring, and explaining Deep Autoencoder anomaly detection."""

    def __init__(
        self,
        input_dim: int = 30,
        latent_dim: int = 4,
        learning_rate: float = 0.001,
        batch_size: int = 64,
        epochs: int = 25,
        threshold_percentile: float = 98.5,
        random_state: int = 42
    ):
        torch.manual_seed(random_state)
        np.random.seed(random_state)

        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.lr = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.threshold_percentile = threshold_percentile

        self.device = torch.device("cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu"))
        self.net = AutoencoderNet(input_dim, latent_dim).to(self.device)
        self.threshold: Optional[float] = None
        self.feature_names: List[str] = []
        self.is_trained = False
        self.training_loss_history: List[float] = []

    def train(
        self,
        X_train_benign: np.ndarray,
        feature_names: Optional[List[str]] = None,
        verbose: bool = False
    ) -> "AnomalyAutoencoder":
        """Trains the autoencoder strictly on benign baseline network traffic."""
        if feature_names:
            self.feature_names = feature_names

        self.net.train()
        tensor_x = torch.tensor(X_train_benign, dtype=torch.float32)
        dataset = TensorDataset(tensor_x)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True, drop_last=False)

        optimizer = torch.optim.AdamW(self.net.parameters(), lr=self.lr, weight_decay=1e-4)
        criterion = nn.MSELoss()
        self.training_loss_history = []

        for epoch in range(self.epochs):
            total_loss = 0.0
            for (batch_x,) in loader:
                batch_x = batch_x.to(self.device)
                optimizer.zero_grad()
                recon, _ = self.net(batch_x)
                loss = criterion(recon, batch_x)
                loss.backward()
                optimizer.step()
                total_loss += loss.item() * batch_x.size(0)

            epoch_loss = total_loss / len(X_train_benign)
            self.training_loss_history.append(epoch_loss)

            if verbose and (epoch + 1) % 5 == 0:
                print(f"Epoch [{epoch+1}/{self.epochs}] Loss: {epoch_loss:.5f}")

        # Calibrate reconstruction threshold on benign training data
        train_recon_errors = self.compute_reconstruction_error(X_train_benign)
        self.threshold = float(np.percentile(train_recon_errors, self.threshold_percentile))
        self.is_trained = True
        return self

    def compute_reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        """Computes mean squared reconstruction error per flow sample."""
        self.net.eval()
        with torch.no_grad():
            tensor_x = torch.tensor(X, dtype=torch.float32).to(self.device)
            recon, _ = self.net(tensor_x)
            errors = torch.mean((recon - tensor_x) ** 2, dim=1).cpu().numpy()
        return errors

    def compute_feature_reconstruction_errors(self, X: np.ndarray) -> np.ndarray:
        """Computes squared error for each individual feature: (N, num_features)."""
        self.net.eval()
        with torch.no_grad():
            tensor_x = torch.tensor(X, dtype=torch.float32).to(self.device)
            recon, _ = self.net(tensor_x)
            errors = ((recon - tensor_x) ** 2).cpu().numpy()
        return errors

    def predict_anomaly(self, X: np.ndarray, threshold: Optional[float] = None) -> np.ndarray:
        """Flags 1 for anomaly (loss >= threshold), 0 for normal."""
        thresh = threshold if threshold is not None else self.threshold
        if thresh is None:
            raise RuntimeError("Threshold is not calibrated. Train model first.")
        errors = self.compute_reconstruction_error(X)
        return (errors >= thresh).astype(np.int64)

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
        test_metadata: Optional[Any] = None,
        threshold: Optional[float] = None
    ) -> AutoencoderMetrics:
        """Evaluates autoencoder anomaly detection across various attack profiles."""
        thresh = threshold if threshold is not None else self.threshold
        errors = self.compute_reconstruction_error(X_test)
        preds = (errors >= thresh).astype(np.int64)

        benign_mask = (y_test == 0)
        attack_mask = (y_test == 1)

        b_mean = float(np.mean(errors[benign_mask])) if benign_mask.sum() > 0 else 0.0
        a_mean = float(np.mean(errors[attack_mask])) if attack_mask.sum() > 0 else 0.0

        per_attack = {}
        if test_metadata is not None and "attack_type" in test_metadata.columns:
            for atk in test_metadata["attack_type"].unique():
                mask = (test_metadata["attack_type"] == atk).to_numpy()
                if mask.sum() > 0:
                    rec = float(preds[mask].mean())
                    mean_loss = float(errors[mask].mean())
                    if atk == "BENIGN":
                        per_attack["BENIGN_FALSE_ALARM_RATE"] = rec
                        per_attack["BENIGN_RECON_LOSS"] = mean_loss
                    else:
                        per_attack[f"{atk}_RECALL"] = rec
                        per_attack[f"{atk}_RECON_LOSS"] = mean_loss

        return AutoencoderMetrics(
            threshold=thresh,
            benign_mean_loss=b_mean,
            attack_mean_loss=a_mean,
            per_attack_recall=per_attack
        )

    def save(self, filepath: str) -> None:
        """Saves model weights and calibration parameters."""
        joblib.dump({
            "state_dict": self.net.state_dict(),
            "threshold": self.threshold,
            "feature_names": self.feature_names,
            "input_dim": self.input_dim,
            "latent_dim": self.latent_dim,
            "threshold_percentile": self.threshold_percentile,
            "is_trained": self.is_trained,
            "training_loss_history": self.training_loss_history
        }, filepath)

    @classmethod
    def load(cls, filepath: str) -> "AnomalyAutoencoder":
        """Loads model weights and parameters from disk."""
        data = joblib.load(filepath)
        instance = cls(
            input_dim=data["input_dim"],
            latent_dim=data["latent_dim"],
            threshold_percentile=data["threshold_percentile"]
        )
        instance.net.load_state_dict(data["state_dict"])
        instance.threshold = data["threshold"]
        instance.feature_names = data["feature_names"]
        instance.is_trained = data["is_trained"]
        instance.training_loss_history = data.get("training_loss_history", [])
        instance.net.eval()
        return instance
