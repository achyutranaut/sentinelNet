"""Tier 5: Statistical Data Drift & Model Performance Monitor (MLOps CM Layer).

Implements Kolmogorov-Smirnov (KS) two-sample tests and Population Stability Index (PSI)
to detect covariate shift and concept drift in streaming NetFlow traffic,
triggering automated model retraining when thresholds are exceeded.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


@dataclass
class FeatureDriftDetail:
    feature_name: str
    ks_statistic: float
    ks_pvalue: float
    psi_score: float
    is_drifted: bool
    severity: str  # "NONE", "MODERATE", "CRITICAL"


@dataclass
class DataDriftReport:
    total_features_evaluated: int
    num_drifted_features: int
    drift_feature_ratio: float
    dataset_drift_detected: bool
    retraining_recommended: bool
    feature_details: Dict[str, FeatureDriftDetail]


class StatisticalDriftMonitor:
    """Monitors live serving traffic against baseline reference data for distribution shifts."""

    def __init__(
        self,
        reference_data: np.ndarray,
        feature_names: List[str],
        ks_alpha: float = 0.05,
        psi_moderate_threshold: float = 0.10,
        psi_critical_threshold: float = 0.25,
        drift_ratio_trigger: float = 0.20
    ):
        self.reference_data = reference_data
        self.feature_names = feature_names
        self.ks_alpha = ks_alpha
        self.psi_mod = psi_moderate_threshold
        self.psi_crit = psi_critical_threshold
        self.drift_ratio_trigger = drift_ratio_trigger

    def compute_psi(self, reference_col: np.ndarray, production_col: np.ndarray, num_bins: int = 10) -> float:
        """Computes Population Stability Index (PSI) between reference and production windows."""
        ref = reference_col[np.isfinite(reference_col)]
        prod = production_col[np.isfinite(production_col)]

        if len(ref) == 0 or len(prod) == 0:
            return 0.0

        # Bin breakpoints based on reference quantiles
        quantiles = np.linspace(0, 100, num_bins + 1)
        bins = np.percentile(ref, quantiles)
        bins[0] -= 1e-5
        bins[-1] += 1e-5
        bins = np.unique(bins)

        if len(bins) < 2:
            return 0.0

        ref_counts, _ = np.histogram(ref, bins=bins)
        prod_counts, _ = np.histogram(prod, bins=bins)

        # Normalize with epsilon smoothing to prevent div by zero
        eps = 1e-4
        ref_pct = (ref_counts + eps) / (len(ref) + eps * len(ref_counts))
        prod_pct = (prod_counts + eps) / (len(prod) + eps * len(prod_counts))

        psi = np.sum((prod_pct - ref_pct) * np.log(prod_pct / ref_pct))
        return float(max(0.0, psi))

    def evaluate_drift(self, production_data: np.ndarray) -> DataDriftReport:
        """Evaluates KS test and PSI on every feature between reference and production data."""
        num_features = min(self.reference_data.shape[1], production_data.shape[1])
        details: Dict[str, FeatureDriftDetail] = {}
        drifted_count = 0

        for idx in range(num_features):
            feat_name = self.feature_names[idx] if idx < len(self.feature_names) else f"feat_{idx}"
            ref_col = self.reference_data[:, idx]
            prod_col = production_data[:, idx]

            # 1. Two-sample Kolmogorov-Smirnov Test
            ks_res = ks_2samp(ref_col, prod_col)
            ks_stat = float(ks_res.statistic)
            ks_pval = float(ks_res.pvalue)

            # 2. Population Stability Index (PSI)
            psi = self.compute_psi(ref_col, prod_col)

            # Drift classification
            is_drifted = (ks_pval < self.ks_alpha) or (psi >= self.psi_mod)
            if psi >= self.psi_crit:
                severity = "CRITICAL"
            elif psi >= self.psi_mod or (ks_pval < self.ks_alpha):
                severity = "MODERATE"
            else:
                severity = "NONE"

            if is_drifted:
                drifted_count += 1

            details[feat_name] = FeatureDriftDetail(
                feature_name=feat_name,
                ks_statistic=ks_stat,
                ks_pvalue=ks_pval,
                psi_score=psi,
                is_drifted=is_drifted,
                severity=severity
            )

        drift_ratio = drifted_count / max(1, num_features)
        dataset_drift = drift_ratio >= self.drift_ratio_trigger
        retraining_recommended = dataset_drift or any(d.severity == "CRITICAL" for d in details.values())

        return DataDriftReport(
            total_features_evaluated=num_features,
            num_drifted_features=drifted_count,
            drift_feature_ratio=float(drift_ratio),
            dataset_drift_detected=dataset_drift,
            retraining_recommended=retraining_recommended,
            feature_details=details
        )
