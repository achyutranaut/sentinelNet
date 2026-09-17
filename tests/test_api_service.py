"""Tests for Production Scoring API & Infrastructure SLA (ml-ops.org Infrastructure Tests).

Tests endpoints, validation error handling, SHAP explainability, graph analysis,
adversarial evasion testing, WebSocket alert streaming, and benchmarks inference latency.
"""

import time
from fastapi.testclient import TestClient
import numpy as np
import pytest

from src.api.app import app
from src.ingestion.dataset_loader import NetworkFlowGenerator


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_api_health_endpoint(client):
    """Verifies that the health endpoint returns 200 and production model metadata."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert "model_id" in data
    assert "version" in data


def test_api_health_all_tiers_loaded(client):
    """Verifies that /health checks all five tiers are loaded."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["all_tiers_loaded"] is True
    tiers = data["tiers"]
    assert tiers["tier0_preprocessor"] is True
    assert tiers["tier1_supervised"] is True
    assert tiers["tier2_autoencoder"] is True
    assert tiers["tier3_lateral_graph"] is True
    assert tiers["tier4_adversarial_engine"] is True
    assert tiers["tier5_cost_calibrator"] is True
    assert tiers["tier5_shap_explainer"] is True
    assert tiers["tier5_drift_monitor"] is True


def test_api_metrics_endpoint(client):
    """Verifies that telemetry metrics are properly aggregated and exposed."""
    res = client.get("/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "uptime_seconds" in data
    assert "sla_compliance_rate" in data
    assert "latency_p95_ms" in data


def test_api_predict_flow_and_latency_sla(client):
    """Tests single-flow prediction and benchmarks inference latency against SLA."""
    gen = NetworkFlowGenerator(seed=42)
    sample_flow = gen.generate_baseline_flows(1).iloc[0].to_dict()

    # Warmup request
    client.post("/predict", json=sample_flow)

    # Benchmark 20 requests
    latencies = []
    for _ in range(20):
        t0 = time.perf_counter()
        res = client.post("/predict", json=sample_flow)
        t_elapsed = (time.perf_counter() - t0) * 1000.0
        latencies.append(t_elapsed)

        assert res.status_code == 200
        body = res.json()
        assert "is_attack" in body
        assert "detection_tier" in body
        assert "supervised_probability" in body
        assert "reconstruction_loss" in body

    # Evaluate internal inference latency reported by service
    p95_latency = np.percentile(latencies, 95)
    print(f"\nAPI Round-Trip p95 Latency: {p95_latency:.3f}ms")
    assert p95_latency < 50.0


def test_score_valid_flow(client):
    """Verifies POST /score executes Tiers 1 and 2, applies Tier 5 cost calibration, and returns latency."""
    gen = NetworkFlowGenerator(seed=42)
    benign_flow = gen.generate_baseline_flows(1).iloc[0].to_dict()

    res = client.post("/score", json=benign_flow)
    assert res.status_code == 200
    data = res.json()
    assert "is_attack" in data
    assert "calibrated_verdict" in data
    assert "supervised_probability" in data
    assert "reconstruction_loss" in data
    assert "cost_calibrated_threshold" in data
    assert "latency_ms" in data
    assert data["latency_ms"] > 0.0
    assert data["is_attack"] == data["calibrated_verdict"]

    # Test attack flow
    attack_flow = gen.generate_known_attacks(1).iloc[0].to_dict()
    res_att = client.post("/score", json=attack_flow)
    assert res_att.status_code == 200
    data_att = res_att.json()
    assert data_att["is_attack"] is True
    assert data_att["calibrated_verdict"] is True
    assert data_att["latency_ms"] > 0.0


def test_score_decision_threshold_boundary(client):
    """Tests POST /score near the calibrated decision threshold boundary."""
    gen = NetworkFlowGenerator(seed=42)
    sample_flow = gen.generate_baseline_flows(1).iloc[0].to_dict()

    # First score to inspect the supervised probability
    res = client.post("/score", json=sample_flow)
    assert res.status_code == 200
    sup_prob = res.json()["supervised_probability"]

    # 1. Set threshold just above probability -> should NOT trigger supervised attack
    res_above = client.post("/score", json={**sample_flow, "supervised_threshold": min(1.0, sup_prob + 0.05)})
    assert res_above.status_code == 200
    assert res_above.json()["supervised_prediction"] == 0

    # 2. Set threshold just below probability -> MUST trigger supervised attack
    res_below = client.post("/score", json={**sample_flow, "supervised_threshold": max(0.0, sup_prob - 0.05)})
    assert res_below.status_code == 200
    assert res_below.json()["supervised_prediction"] == 1
    assert res_below.json()["is_attack"] is True
    assert res_below.json()["calibrated_verdict"] is True


@pytest.mark.parametrize("invalid_payload,expected_error_substr", [
    ({"src_ip": "999.999.999.999"}, "Invalid IP address format"),
    ({"dst_ip": "invalid-destination"}, "Invalid IP address format"),
    ({"dst_port": 70000}, "less than or equal to 65535"),
    ({"dst_port": 0}, "greater than or equal to 1"),
    ({"dst_port": -1}, "greater than or equal to 1"),
    ({"flow_duration_ms": -10.0}, "greater than or equal to 0"),
    ({"flow_duration_ms": 999999999.0}, "less than or equal to 86400000"),
    ({"total_fwd_packets": -2}, "greater than or equal to 0"),
    ({"total_bwd_packets": -2}, "greater than or equal to 0"),
    ({"total_fwd_packets": 0, "total_bwd_packets": 0}, "at least 1 total packet"),
    ({"total_fwd_bytes": -50.0}, "greater than or equal to 0"),
    ({"total_bwd_bytes": -50.0}, "greater than or equal to 0"),
    ({"flow_duration_ms": "NaN"}, "cannot be nan or infinite"),
    ({"flow_duration_ms": "Infinity"}, "cannot be nan or infinite"),
    ({"flow_bytes_per_sec": "not-a-number"}, "valid float"),
])
def test_score_malformed_inputs_rejected_422(client, invalid_payload, expected_error_substr):
    """Verifies that out-of-range or malformed features are strictly rejected with 422 (ML Security / Section 32)."""
    gen = NetworkFlowGenerator(seed=42)
    base_flow = gen.generate_baseline_flows(1).iloc[0].to_dict()

    bad_payload = {**base_flow, **invalid_payload}
    res = client.post("/score", json=bad_payload)
    assert res.status_code == 422, f"Expected 422 for malformed payload {invalid_payload}, got {res.status_code}: {res.text}"
    assert expected_error_substr.lower() in res.text.lower()


def test_score_raw_malformed_json_rejected_422(client):
    """Verifies unparseable raw JSON payload triggers 422."""
    res = client.post("/score", content="malformed{json: not_valid", headers={"Content-Type": "application/json"})
    assert res.status_code == 422


def test_graph_state_svg_ready(client):
    """Verifies GET /graph/state returns SVG-morphing ready nodes, edges, and metrics."""
    res = client.get("/graph/state")
    assert res.status_code == 200
    data = res.json()

    assert "nodes" in data
    assert "edges" in data
    assert "metrics" in data
    assert len(data["nodes"]) > 0

    # Verify node properties for direct SVG consumption
    first_node = data["nodes"][0]
    assert "id" in first_node
    assert "x" in first_node
    assert "y" in first_node
    assert "r" in first_node
    assert "color" in first_node
    assert "role" in first_node
    assert "degree_zscore" in first_node
    assert "jaccard_novelty" in first_node
    assert "pagerank" in first_node

    # Verify SVG coordinate bounds (viewBox 0 0 800 600)
    for n in data["nodes"]:
        assert 0.0 <= n["x"] <= 800.0
        assert 0.0 <= n["y"] <= 600.0

    # Verify edge properties
    if data["edges"]:
        first_edge = data["edges"][0]
        assert "source" in first_edge
        assert "target" in first_edge
        assert "source_x" in first_edge
        assert "source_y" in first_edge
        assert "target_x" in first_edge
        assert "target_y" in first_edge
        assert "color" in first_edge

    # Verify metrics summary
    metrics = data["metrics"]
    assert "max_degree_zscore" in metrics
    assert "max_jaccard_novelty" in metrics
    assert "max_pagerank_delta" in metrics


def test_evasion_test_endpoint(client):
    """Verifies POST /evasion/test accepts budget parameter and returns recall."""
    # Baseline budget
    res = client.post("/evasion/test", json={"perturbation_budget": 0.0, "sample_size": 20})
    assert res.status_code == 200
    data = res.json()
    assert "recall" in data
    assert "supervised_recall" in data
    assert "autoencoder_recall" in data
    assert "combined_recall" in data
    assert data["perturbation_budget"] == 0.0
    assert 0.0 <= data["recall"] <= 1.0

    # Adversarial budget test with epsilon alias
    res_adv = client.post("/evasion/test", json={"epsilon": 0.25, "sample_size": 20})
    assert res_adv.status_code == 200
    data_adv = res_adv.json()
    assert data_adv["perturbation_budget"] == 0.25
    assert 0.0 <= data_adv["recall"] <= 1.0


@pytest.mark.parametrize("bad_budget", [-0.1, 1.5, "invalid"])
def test_evasion_test_malformed_budget(client, bad_budget):
    """Verifies out-of-range perturbation budgets are rejected with 422."""
    res = client.post("/evasion/test", json={"perturbation_budget": bad_budget})
    assert res.status_code == 422


def test_drift_status_endpoint(client):
    """Verifies GET /drift/status returns KS/PSI statistics and retrain recommended boolean."""
    res = client.get("/drift/status")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "retraining_recommended" in data
    assert isinstance(data["retraining_recommended"], bool)
    assert "drift_feature_ratio" in data
    assert isinstance(data["drift_feature_ratio"], float)
    assert "feature_details" in data
    assert len(data["feature_details"]) > 0

    first_feat = data["feature_details"][0]
    assert "feature_name" in first_feat
    assert "ks_statistic" in first_feat
    assert "ks_pvalue" in first_feat
    assert "psi_score" in first_feat
    assert "severity" in first_feat


def test_alerts_websocket_stream_and_graceful_disconnect(client):
    """Verifies WebSocket /alerts/stream receives alerts with SHAP explanations and survives client disconnect."""
    gen = NetworkFlowGenerator(seed=42)
    attack_flow = gen.generate_known_attacks(1).iloc[0].to_dict()

    with client.websocket_connect("/alerts/stream") as ws:
        init_msg = ws.receive_json()
        assert init_msg.get("event") == "SUBSCRIBED"

        # Trigger score that results in an attack alert
        res = client.post("/score", json=attack_flow)
        assert res.status_code == 200
        assert res.json()["is_attack"] is True

        # Receive streamed alert on websocket
        alert_msg = ws.receive_json()
        assert "alert_id" in alert_msg
        assert alert_msg["is_attack"] is True
        assert "explanation" in alert_msg
        assert "top_drivers" in alert_msg["explanation"]
        assert len(alert_msg["explanation"]["top_drivers"]) > 0

        # Send heartbeat
        ws.send_text("PING")
        pong = ws.receive_json()
        assert pong.get("event") == "HEARTBEAT"

    # Client has disconnected now. Ensure server doesn't crash on subsequent scorings
    res2 = client.post("/score", json=attack_flow)
    assert res2.status_code == 200
    assert res2.json()["is_attack"] is True


def test_api_batch_prediction(client):
    """Tests legacy batch scoring endpoint."""
    gen = NetworkFlowGenerator(seed=42)
    flows = gen.generate_full_dataset(n_baseline=10, n_known=5, n_zero_day=0, n_lateral=0).to_dict(orient="records")

    res = client.post("/predict/batch", json={"flows": flows, "supervised_threshold": 0.5})
    assert res.status_code == 200
    data = res.json()
    assert data["num_scored"] == 15
    assert len(data["results"]) == 15
    assert "total_time_ms" in data


def test_api_explainability(client):
    """Tests TreeSHAP explainability endpoint."""
    gen = NetworkFlowGenerator(seed=42)
    sample_flow = gen.generate_known_attacks(1).iloc[0].to_dict()

    res = client.post("/explain?top_k=3", json=sample_flow)
    assert res.status_code == 200
    data = res.json()
    assert "predicted_probability" in data
    assert "analyst_summary" in data
    assert len(data["top_drivers"]) == 3


def test_api_graph_lateral_movement(client):
    """Tests legacy graph topology analysis endpoint."""
    gen = NetworkFlowGenerator(seed=42)
    flows = gen.generate_lateral_movement(15).to_dict(orient="records")

    res = client.post("/graph/analyze", json=flows)
    assert res.status_code == 200
    data = res.json()
    assert "num_nodes" in data
    assert "num_edges" in data
    assert "pivots" in data
