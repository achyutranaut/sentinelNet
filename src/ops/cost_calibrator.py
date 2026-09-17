"""Tier 5: SOC Asymmetric Cost & Neyman-Pearson Threshold Calibrator.

Calibrates decision thresholds considering enterprise financial realities:
False Negative (unflagged breach) cost ($50,000) >> False Positive (analyst triage) cost ($50).
Minimizes total monetary risk while maintaining acceptable analyst alert volume.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from sklearn.metrics import confusion_matrix


@dataclass
class CostCalibrationResult:
    optimal_threshold: float
    min_cost: float
    default_cost_at_05: float
    cost_reduction_percent: float
    optimal_fn: int
    optimal_fp: int
    optimal_tp: int
    optimal_tn: int
    optimal_far: float
    optimal_recall: float


class SOCCostCalibrator:
    """Optimizes decision thresholds to minimize enterprise asymmetric breach loss."""

    def __init__(
        self,
        cost_fn: float = 50000.0,
        cost_fp: float = 50.0,
        cost_tp: float = 0.0,
        cost_tn: float = 0.0
    ):
        self.cost_fn = cost_fn
        self.cost_fp = cost_fp
        self.cost_tp = cost_tp
        self.cost_tn = cost_tn

    def compute_total_cost(self, y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, int, int, int, int]:
        """Calculates total dollar impact from confusion matrix."""
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        total_cost = (fn * self.cost_fn) + (fp * self.cost_fp) + (tp * self.cost_tp) + (tn * self.cost_tn)
        return float(total_cost), int(tn), int(fp), int(fn), int(tp)

    def calibrate_threshold(
        self,
        y_true: np.ndarray,
        predicted_probs: np.ndarray,
        num_candidates: int = 100
    ) -> CostCalibrationResult:
        """Finds the optimal decision threshold that minimizes total enterprise risk."""
        candidate_thresholds = np.linspace(0.01, 0.99, num_candidates)
        best_thresh = 0.5
        min_cost = float("inf")
        best_stats = (0, 0, 0, 0)

        # Baseline cost at standard 0.5 threshold
        default_preds = (predicted_probs >= 0.5).astype(int)
        default_cost, _, _, _, _ = self.compute_total_cost(y_true, default_preds)

        for thresh in candidate_thresholds:
            preds = (predicted_probs >= thresh).astype(int)
            cost, tn, fp, fn, tp = self.compute_total_cost(y_true, preds)
            if cost < min_cost:
                min_cost = cost
                best_thresh = float(thresh)
                best_stats = (tn, fp, fn, tp)

        opt_tn, opt_fp, opt_fn, opt_tp = best_stats
        opt_far = opt_fp / max(1, opt_fp + opt_tn)
        opt_recall = opt_tp / max(1, opt_tp + opt_fn)
        reduction_pct = max(0.0, (default_cost - min_cost) / max(1.0, default_cost) * 100.0)

        return CostCalibrationResult(
            optimal_threshold=best_thresh,
            min_cost=min_cost,
            default_cost_at_05=default_cost,
            cost_reduction_percent=reduction_pct,
            optimal_fn=opt_fn,
            optimal_fp=opt_fp,
            optimal_tp=opt_tp,
            optimal_tn=opt_tn,
            optimal_far=float(opt_far),
            optimal_recall=float(opt_recall)
        )
