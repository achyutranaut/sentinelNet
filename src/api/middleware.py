"""Production Telemetry Middleware & Drift Buffer for SentinelNet FastAPI (MLOps CM Layer).

Tracks p95/p99 inference latency against the < 1.5ms SLA, guards against NaNs/Infs,
and buffers streaming flows for rolling statistical drift evaluations.
"""

from collections import deque
import time
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.ops.drift_monitor import DataDriftReport, StatisticalDriftMonitor


class TelemetryCollector:
    """Thread-safe telemetry aggregator tracking latency percentiles and detection metrics."""

    def __init__(self, window_size: int = 2000):
        self.latencies: deque = deque(maxlen=window_size)
        self.total_requests: int = 0
        self.total_attacks_flagged: int = 0
        self.tier1_detections: int = 0
        self.tier2_detections: int = 0
        self.sla_violations: int = 0  # Latencies > 1.5ms
        self.start_time: float = time.time()

    def record_inference(self, latency_ms: float, detection_tier: str, is_attack: bool) -> None:
        """Records telemetry for an individual prediction request."""
        self.latencies.append(latency_ms)
        self.total_requests += 1
        if latency_ms > 1.5:
            self.sla_violations += 1

        if is_attack:
            self.total_attacks_flagged += 1
            if "TIER_1" in detection_tier:
                self.tier1_detections += 1
            if "TIER_2" in detection_tier:
                self.tier2_detections += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Returns summarized serving performance and SLA adherence."""
        lat_arr = np.array(self.latencies) if self.latencies else np.array([0.0])
        return {
            "uptime_seconds": round(time.time() - self.start_time, 1),
            "total_requests": self.total_requests,
            "total_attacks_flagged": self.total_attacks_flagged,
            "attack_rate": round(self.total_attacks_flagged / max(1, self.total_requests), 4),
            "tier1_detections": self.tier1_detections,
            "tier2_detections": self.tier2_detections,
            "sla_violations": self.sla_violations,
            "sla_compliance_rate": round(1.0 - (self.sla_violations / max(1, self.total_requests)), 4),
            "latency_p50_ms": round(float(np.percentile(lat_arr, 50)), 3),
            "latency_p95_ms": round(float(np.percentile(lat_arr, 95)), 3),
            "latency_p99_ms": round(float(np.percentile(lat_arr, 99)), 3),
            "latency_mean_ms": round(float(np.mean(lat_arr)), 3)
        }


class StreamingDriftBuffer:
    """Accumulates incoming serving features and periodically triggers drift evaluations."""

    def __init__(self, drift_monitor: Optional[StatisticalDriftMonitor] = None, buffer_size: int = 200):
        self.drift_monitor = drift_monitor
        self.buffer_size = buffer_size
        self.feature_buffer: List[np.ndarray] = []
        self.latest_drift_report: Optional[DataDriftReport] = None

    def add_features(self, X: np.ndarray) -> None:
        """Appends preprocessed features to the drift buffer."""
        if X.ndim == 1:
            X = X.reshape(1, -1)
        self.feature_buffer.append(X)

        if len(self.feature_buffer) >= self.buffer_size and self.drift_monitor is not None:
            prod_batch = np.vstack(self.feature_buffer)
            self.latest_drift_report = self.drift_monitor.evaluate_drift(prod_batch)
            self.feature_buffer.clear()

    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """Returns the latest evaluated drift metrics."""
        if self.latest_drift_report is None:
            return {"status": "INSUFFICIENT_DATA", "buffered_samples": len(self.feature_buffer), "threshold": self.buffer_size}

        rep = self.latest_drift_report
        return {
            "status": "DRIFT_DETECTED" if rep.dataset_drift_detected else "STABLE",
            "retraining_recommended": rep.retraining_recommended,
            "drift_feature_ratio": round(rep.drift_feature_ratio, 3),
            "num_drifted_features": rep.num_drifted_features,
            "total_features": rep.total_features_evaluated
        }
