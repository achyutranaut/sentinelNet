"""Tier 4: Adversarial Evasion & Traffic Perturbation Engine for SentinelNet.

Simulates realistic evasion techniques (packet padding, inter-arrival time dilation/jitter,
and Fast Gradient Sign Method (FGSM) gradient perturbations).
Benchmarks detection degradation vs evasion budget and provides adversarial retraining augmentation.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from src.ingestion.preprocessor import FlowPreprocessor
from src.models.anomaly_autoencoder import AnomalyAutoencoder
from src.models.supervised_classifier import SupervisedFlowClassifier


@dataclass
class RobustnessCurvePoint:
    epsilon: float
    supervised_recall: float
    autoencoder_recall: float
    combined_recall: float


class TrafficPerturbationEngine:
    """Simulates domain-realistic network traffic perturbations and mathematical gradient attacks."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def apply_realistic_traffic_perturbation(
        self,
        df: pd.DataFrame,
        padding_ratio: float = 0.3,
        jitter_ms: float = 150.0
    ) -> pd.DataFrame:
        """Applies domain-valid NetFlow feature perturbations simulating evasive malware.

        1. Packet Padding: Increases byte counts and packet length averages without adding flows.
        2. IAT Dilation: Increases duration and inter-arrival times to mimic low-and-slow traffic.
        """
        df_pert = df.copy()

        # 1. Packet Padding Perturbation
        if "total_fwd_bytes" in df_pert.columns:
            pad_multiplier = 1.0 + float(padding_ratio)
            df_pert["total_fwd_bytes"] = df_pert["total_fwd_bytes"] * pad_multiplier
            df_pert["fwd_packet_length_mean"] = df_pert["fwd_packet_length_mean"] * pad_multiplier
            df_pert["avg_fwd_segment_size"] = df_pert["avg_fwd_segment_size"] * pad_multiplier

        # 2. Timing Jitter / Dilation Perturbation
        if "flow_duration_ms" in df_pert.columns:
            df_pert["flow_duration_ms"] = df_pert["flow_duration_ms"] + float(jitter_ms)
            df_pert["flow_iat_mean_ms"] = df_pert["flow_iat_mean_ms"] + float(jitter_ms / 5.0)
            df_pert["fwd_iat_mean_ms"] = df_pert["fwd_iat_mean_ms"] + float(jitter_ms / 5.0)
            # Dilated timing reduces rate features
            safe_duration_sec = np.maximum(0.001, df_pert["flow_duration_ms"] / 1000.0)
            total_pkts = df_pert["total_fwd_packets"] + df_pert["total_bwd_packets"]
            total_bytes = df_pert["total_fwd_bytes"] + df_pert["total_bwd_bytes"]
            df_pert["flow_packets_per_sec"] = total_pkts / safe_duration_sec
            df_pert["flow_bytes_per_sec"] = total_bytes / safe_duration_sec

        return df_pert

    def generate_fgsm_perturbation(
        self,
        autoencoder: AnomalyAutoencoder,
        X: np.ndarray,
        epsilon: float = 0.1
    ) -> np.ndarray:
        """Applies Fast Gradient Sign Method (FGSM) on normalized features against the Autoencoder.

        Perturbs features in the direction that minimizes reconstruction loss:
        X_adv = X - epsilon * sign(grad_X(MSE(Recon, X)))
        to make attack traffic appear more 'benign' to the unsupervised model.
        """
        if epsilon <= 0.0:
            return X.copy()

        autoencoder.net.eval()
        tensor_x = torch.tensor(X, dtype=torch.float32, device=autoencoder.device, requires_grad=True)

        recon, _ = autoencoder.net(tensor_x)
        # Loss: mean squared reconstruction error per sample
        loss = torch.mean((recon - tensor_x) ** 2)
        loss.backward()

        if tensor_x.grad is not None:
            # Move in direction of reducing reconstruction loss to trick anomaly detector
            data_grad = tensor_x.grad.data
            sign_grad = data_grad.sign()
            adv_tensor = tensor_x - epsilon * sign_grad
            adv_x = adv_tensor.detach().cpu().numpy()
            return np.clip(adv_x, -10.0, 10.0)

        return X.copy()

    def benchmark_adversarial_robustness(
        self,
        supervised_clf: SupervisedFlowClassifier,
        autoencoder: AnomalyAutoencoder,
        X_test_attacks: np.ndarray,
        epsilon_levels: Optional[List[float]] = None
    ) -> List[RobustnessCurvePoint]:
        """Evaluates detection recall drop across increasing perturbation budgets."""
        if epsilon_levels is None:
            epsilon_levels = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4]

        results: List[RobustnessCurvePoint] = []
        ae_thresh = autoencoder.threshold if autoencoder.threshold is not None else 1.0

        for eps in epsilon_levels:
            X_adv = self.generate_fgsm_perturbation(autoencoder, X_test_attacks, epsilon=eps)

            sup_probs = supervised_clf.predict_proba(X_adv)
            sup_preds = (sup_probs >= 0.5).astype(int)
            sup_recall = float(np.mean(sup_preds))

            recon_losses = autoencoder.compute_reconstruction_error(X_adv)
            ae_preds = (recon_losses >= ae_thresh).astype(int)
            ae_recall = float(np.mean(ae_preds))

            combined_preds = (sup_preds | ae_preds).astype(int)
            combined_recall = float(np.mean(combined_preds))

            results.append(RobustnessCurvePoint(
                epsilon=eps,
                supervised_recall=sup_recall,
                autoencoder_recall=ae_recall,
                combined_recall=combined_recall
            ))

        return results

    def create_adversarially_augmented_dataset(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        autoencoder: AnomalyAutoencoder,
        augmentation_ratio: float = 0.25,
        epsilon: float = 0.15
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Augments training dataset with FGSM adversarial attack samples for robust defense training."""
        attack_mask = (y_train == 1)
        X_attacks = X_train[attack_mask]
        n_aug = int(len(X_attacks) * augmentation_ratio)

        if n_aug == 0:
            return X_train.copy(), y_train.copy()

        selected_idx = self.rng.choice(len(X_attacks), size=n_aug, replace=False)
        X_selected = X_attacks[selected_idx]

        X_adv = self.generate_fgsm_perturbation(autoencoder, X_selected, epsilon=epsilon)
        y_adv = np.ones(len(X_adv), dtype=y_train.dtype)

        X_augmented = np.vstack([X_train, X_adv])
        y_augmented = np.concatenate([y_train, y_adv])

        return X_augmented, y_augmented
