"""Decoupled REST & WebSocket Client for SentinelNet Dashboard.

Ensures the UI strictly interacts with the production FastAPI service (:8000)
without importing internal Python ML models, eliminating redundant runtimes and duplicate memory footprints.
"""

import os
from typing import Any, Dict, List, Optional
import httpx


class SentinelApiClient:
    """HTTP client communicating with the SentinelNet FastAPI serving layer."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 10.0
    ):
        self.base_url = base_url or os.getenv("SENTINEL_API_URL", "http://localhost:8000")
        self.api_key = api_key or os.getenv("SENTINEL_API_KEY", "sentinel-dev-secret-key-32b")
        self.headers = {"X-API-Key": self.api_key}
        self.timeout = timeout

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, headers=self.headers, timeout=self.timeout)

    def get_health(self) -> Dict[str, Any]:
        """Checks API health and retrieves model metadata and tier status."""
        with self._client() as client:
            resp = client.get("/health")
            resp.raise_for_status()
            return resp.json()

    def get_metrics(self) -> Dict[str, Any]:
        """Fetches telemetry metrics and latency SLA compliance."""
        with self._client() as client:
            resp = client.get("/metrics")
            resp.raise_for_status()
            return resp.json()

    def score_flow(self, flow: Dict[str, Any], supervised_threshold: Optional[float] = None) -> Dict[str, Any]:
        """Scores an individual network flow with Tiers 1 and 2 and receives TreeSHAP explanation."""
        payload = {**flow}
        if supervised_threshold is not None:
            payload["supervised_threshold"] = supervised_threshold

        with self._client() as client:
            resp = client.post("/score", json=payload)
            resp.raise_for_status()
            return resp.json()

    def score_batch(self, flows: List[Dict[str, Any]], supervised_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Scores a batch of flows through the API sequentially or via pooled connections."""
        results = []
        with self._client() as client:
            for f in flows:
                payload = {**f}
                if supervised_threshold is not None:
                    payload["supervised_threshold"] = supervised_threshold
                resp = client.post("/score", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    results.append({
                        **f,
                        "supervised_prob": data["supervised_probability"],
                        "supervised_score": data["supervised_score"],
                        "reconstruction_loss": data["reconstruction_loss"],
                        "reconstruction_threshold": data["reconstruction_threshold"],
                        "supervised_pred": data["supervised_prediction"],
                        "autoencoder_pred": data["autoencoder_prediction"],
                        "detection_tier": data["detection_tier"],
                        "is_attack": int(data["is_attack"]),
                        "latency_ms": data["latency_ms"]
                    })
                else:
                    # Record failure if throttled or error
                    results.append({**f, "is_attack": 0, "supervised_prob": 0.0, "reconstruction_loss": 0.0})
        return results

    def get_graph_state(self) -> Dict[str, Any]:
        """Retrieves SVG-morphing ready graph nodes, edges, and pivot metrics."""
        with self._client() as client:
            resp = client.get("/graph/state")
            resp.raise_for_status()
            return resp.json()

    def test_evasion(self, perturbation_budget: float, sample_size: int = 40) -> Dict[str, Any]:
        """Evaluates adversarial degradation under budget."""
        with self._client() as client:
            resp = client.post(
                "/evasion/test",
                json={"perturbation_budget": perturbation_budget, "sample_size": sample_size}
            )
            resp.raise_for_status()
            return resp.json()

    def get_drift_status(self) -> Dict[str, Any]:
        """Retrieves current statistical drift statistics and retraining recommendation."""
        with self._client() as client:
            resp = client.get("/drift/status")
            resp.raise_for_status()
            return resp.json()

    def explain_flow(self, flow: Dict[str, Any], top_k: int = 5) -> Dict[str, Any]:
        """Calls explainability endpoint for a single flow."""
        with self._client() as client:
            resp = client.post(f"/explain?top_k={top_k}", json=flow)
            resp.raise_for_status()
            return resp.json()
