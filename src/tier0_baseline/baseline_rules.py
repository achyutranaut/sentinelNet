"""Tier 0: Static Deterministic Heuristic Baseline for SentinelNet.

Serves as the empirical baseline yardstick. Implements non-ML heuristic rules
derived from standard network security operations (rate thresholds and header flags).
Every subsequent tier must demonstrate statistically significant marginal improvement
over this baseline under cost-asymmetric evaluation.
"""

import time
from typing import Any, Dict, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score


class Tier0HeuristicDetector:
    """Deterministic, rule-based baseline intrusion detector."""

    def __init__(
        self,
        pps_threshold: float = 2500.0,
        bps_threshold: float = 1_000_000.0,
        scan_duration_max_ms: float = 20.0,
        scan_max_packets: int = 3,
        auth_ports: Optional[Tuple[int, ...]] = (21, 22, 3389)
    ):
        self.pps_threshold = pps_threshold
        self.bps_threshold = bps_threshold
        self.scan_duration_max_ms = scan_duration_max_ms
        self.scan_max_packets = scan_max_packets
        self.auth_ports = auth_ports or (21, 22, 3389)

    def predict_record(self, record: Dict[str, Any]) -> int:
        """Predicts a single raw flow dictionary. Returns 1 if flagged, else 0."""
        # 1. Volumetric DDoS heuristic
        pps = record.get("flow_packets_per_sec", 0.0)
        bps = record.get("flow_bytes_per_sec", 0.0)
        if pps > self.pps_threshold or bps > self.bps_threshold:
            return 1

        # 2. Port scan heuristic
        duration = record.get("flow_duration_ms", 0.0)
        fwd_pkts = record.get("total_fwd_packets", 0)
        fwd_ack = record.get("fwd_ack_flags", 0)
        fwd_syn = record.get("fwd_syn_flags", 0)
        if duration <= self.scan_duration_max_ms and fwd_pkts <= self.scan_max_packets and fwd_ack == 0 and fwd_syn >= 1:
            return 1

        # 3. Brute force authentication heuristic
        dst_port = record.get("dst_port", 0)
        fwd_rst = record.get("fwd_rst_flags", 0)
        if dst_port in self.auth_ports and fwd_rst > 0:
            return 1

        return 0

    def predict_dataframe(self, df: pd.DataFrame) -> np.ndarray:
        """Vectorized evaluation over a DataFrame."""
        # Rule 1: Volumetric Flood
        cond_flood = (df["flow_packets_per_sec"] > self.pps_threshold) | (df["flow_bytes_per_sec"] > self.bps_threshold)

        # Rule 2: Port Scan (rapid SYN without ACK)
        cond_scan = (
            (df["flow_duration_ms"] <= self.scan_duration_max_ms) &
            (df["total_fwd_packets"] <= self.scan_max_packets) &
            (df["fwd_ack_flags"] == 0) &
            (df["fwd_syn_flags"] >= 1)
        )

        # Rule 3: Brute force authentication (RST flag on auth port)
        cond_brute = (
            (df["dst_port"].isin(self.auth_ports)) &
            (df["fwd_rst_flags"] > 0)
        )

        flagged = cond_flood | cond_scan | cond_brute
        return flagged.astype(int).to_numpy()

    def evaluate(
        self,
        test_df: pd.DataFrame,
        cost_fn: float = 50000.0,
        cost_fp: float = 50.0
    ) -> Dict[str, Any]:
        """Runs evaluation over the benchmark test set and records metrics."""
        y_true = test_df["label"].to_numpy()

        start_t = time.perf_counter()
        y_pred = self.predict_dataframe(test_df)
        elapsed_sec = time.perf_counter() - start_t
        latency_us = (elapsed_sec / len(test_df)) * 1_000_000.0

        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        acc = accuracy_score(y_true, y_pred)
        roc_auc = roc_auc_score(y_true, y_pred)

        # Cost-asymmetric dollar risk evaluation
        fn = int(np.sum((y_true == 1) & (y_pred == 0)))
        fp = int(np.sum((y_true == 0) & (y_pred == 1)))
        tp = int(np.sum((y_true == 1) & (y_pred == 1)))
        tn = int(np.sum((y_true == 0) & (y_pred == 0)))
        total_cost = (fn * cost_fn) + (fp * cost_fp)

        # Breakdown by attack type
        attack_recall = {}
        for attack_name, group in test_df.groupby("attack_type"):
            if attack_name == "BENIGN":
                continue
            grp_true = group["label"].to_numpy()
            grp_pred = self.predict_dataframe(group)
            attack_recall[attack_name] = float(recall_score(grp_true, grp_pred, zero_division=0))

        return {
            "tier": "Tier 0 (Heuristic Baseline)",
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "roc_auc": float(roc_auc),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "total_dollar_loss": float(total_cost),
            "latency_us_per_sample": float(latency_us),
            "attack_type_recall": attack_recall
        }


def run_tier0_benchmark():
    raw_df = pd.read_parquet("data/raw/raw_flows.parquet")
    splits = joblib.load("data/processed/dataset_splits.joblib")
    
    # Reconstruct test dataframe with metadata
    test_features_df = raw_df.iloc[-len(splits.y_test):].copy().reset_index(drop=True)
    # Ensure test metadata labels match
    test_features_df["label"] = splits.y_test
    test_features_df["attack_type"] = splits.test_metadata["attack_type"].to_numpy()

    detector = Tier0HeuristicDetector()
    results = detector.evaluate(test_features_df)

    print("=" * 60)
    print(">>> TIER 0 BASELINE EVALUATION RESULTS")
    print("=" * 60)
    print(f"Accuracy:        {results['accuracy']:.4f}")
    print(f"Precision:       {results['precision']:.4f}")
    print(f"Recall:          {results['recall']:.4f}")
    print(f"F1-Score:        {results['f1']:.4f}")
    print(f"ROC-AUC:         {results['roc_auc']:.4f}")
    print(f"Latency:         {results['latency_us_per_sample']:.2f} µs/sample")
    print(f"TP: {results['tp']} | FP: {results['fp']} | FN: {results['fn']} | TN: {results['tn']}")
    print(f"Expected Financial Loss: ${results['total_dollar_loss']:,.2f}")
    print("\nRecall by Attack Category:")
    for atk, rec in results["attack_type_recall"].items():
        print(f"  - {atk:<26}: {rec * 100:.1f}%")
    print("=" * 60)

    # Save metrics
    metrics_path = "artifacts/tier0_metrics.joblib"
    joblib.dump(results, metrics_path)
    print(f"[+] Tier 0 benchmark saved to {metrics_path}")
    return results


if __name__ == "__main__":
    run_tier0_benchmark()
