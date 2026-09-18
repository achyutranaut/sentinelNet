"""Tier 6: High-Throughput Production Serving API for SentinelNet (MLOps CD Layer).

FastAPI microservice delivering sub-millisecond per-flow inference,
multi-tier ensemble scoring (LightGBM + Autoencoder + Cost Calibration),
SVG-ready temporal lateral movement topology, adversarial robustness testing,
resilient WebSocket alert streaming with TreeSHAP explanations, and statistical drift observability.
Hardened with API key authentication, adversarial DoS rate limiting, CORS, non-blocking async execution,
and thread-safe lifecycle initialization.
"""

import asyncio
from collections import deque
from contextlib import asynccontextmanager
import logging
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import joblib
import networkx as nx
import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel

from src.api.auth import verify_api_key, verify_ws_api_key
from src.api.middleware import RateLimitChecker, StreamingDriftBuffer, TelemetryCollector
from src.api.schemas import (
    AlertStreamItem,
    DriftFeatureStat,
    FeatureDriftStat,
    DriftStatusResponse,
    EvasionTestRequest,
    EvasionTestResponse,
    FlowScoreRequest,
    GraphEdge,
    GraphMetricsSummary,
    GraphNode,
    GraphStateResponse,
    HealthResponse,
    HealthTierDetails,
    ScoreResponse,
    SHAPExplanationPayload,
    SHAPFeatureDriver,
)
from src.api.websocket_manager import AlertStreamManager
from src.adversarial.perturbation_engine import TrafficPerturbationEngine
from src.graph.lateral_tracker import TemporalLateralTracker
from src.ingestion.dataset_loader import NetworkFlowGenerator
from src.ingestion.schema import NetFlowRecord
from src.models.registry import InferenceBundle, ModelRegistry
from src.ops.cost_calibrator import SOCCostCalibrator
from src.ops.drift_monitor import StatisticalDriftMonitor
from src.ops.explainability import IncidentExplainabilityEngine

logger = logging.getLogger("sentinelnet.api")
_init_lock = threading.Lock()

# Per-route rate limiters
score_rate_limiter = RateLimitChecker(max_requests=60, window_seconds=60.0, route_name="score")
evasion_rate_limiter = RateLimitChecker(max_requests=5, window_seconds=60.0, route_name="evasion_test")


def init_state(app: FastAPI) -> None:
    """Loads all five tiers' artifacts and monitors once into app.state."""
    registry = ModelRegistry()
    generator = NetworkFlowGenerator(seed=42)

    # 1. Tier 0, 1, 2: Load production inference bundle (preprocessor, LightGBM, autoencoder)
    try:
        bundle = registry.get_production_bundle()
    except Exception as e:
        logger.warning("Primary production bundle lookup failed: %s. Falling back to latest.", e)
        models = registry.list_models()
        if models:
            bundle = registry.load_bundle(models[-1]["model_id"])
        else:
            raise RuntimeError("No model artifacts found in registry.")

    # 2. Tier 5: Explainability Engine
    explainer = IncidentExplainabilityEngine(bundle.supervised_model)

    # 3. Tier 5: Cost Calibrator & Neyman-Pearson Decision Threshold
    cost_calibrator = SOCCostCalibrator(cost_fn=50000.0, cost_fp=50.0)
    cost_threshold = float(bundle.metadata.metrics.get("optimal_threshold", 0.2376))

    # 4. Tier 5: Statistical Drift Monitor & Buffer
    ref_path = Path("data/reference_baseline.joblib")
    if ref_path.exists():
        ref_data = joblib.load(ref_path)
        drift_monitor = StatisticalDriftMonitor(
            reference_data=ref_data["reference_data"],
            feature_names=ref_data["feature_names"]
        )
    else:
        dummy_ref = np.zeros((100, 30))
        drift_monitor = StatisticalDriftMonitor(dummy_ref, bundle.metadata.feature_names)
    drift_buffer = StreamingDriftBuffer(drift_monitor=drift_monitor, buffer_size=100)

    # 5. Tier 3: Temporal Lateral Movement Tracker & Baseline Fitting
    lateral_tracker = TemporalLateralTracker()
    baseline_df = generator.generate_baseline_flows(400)
    lateral_tracker.fit_baseline(baseline_df)

    # Seed initial sliding graph window with realistic enterprise topology
    initial_window = pd.concat([
        generator.generate_baseline_flows(50),
        generator.generate_lateral_movement(20)
    ]).reset_index(drop=True)
    graph_flows = deque(initial_window.to_dict(orient="records"), maxlen=500)

    # 6. Tier 4: Adversarial Perturbation Engine & Sample Attack Batch
    adversarial_engine = TrafficPerturbationEngine(seed=42)
    sample_attacks_df = generator.generate_known_attacks(80)
    sample_attacks = bundle.preprocessor.transform(sample_attacks_df)

    # Telemetry and WebSocket Connection Manager
    telemetry = TelemetryCollector()
    alert_manager = AlertStreamManager()

    # Bind state to app instance
    app.state.bundle = bundle
    app.state.explainer = explainer
    app.state.cost_calibrator = cost_calibrator
    app.state.cost_threshold = cost_threshold
    app.state.drift_monitor = drift_monitor
    app.state.drift_buffer = drift_buffer
    app.state.lateral_tracker = lateral_tracker
    app.state.graph_flows = graph_flows
    app.state.generator = generator
    app.state.adversarial_engine = adversarial_engine
    app.state.sample_attacks = sample_attacks
    app.state.telemetry = telemetry
    app.state.alert_manager = alert_manager
    app.state.initialized = True

    logger.info(
        "SentinelNet serving layer initialized with model: %s (v%s, optimal_threshold=%.4f)",
        bundle.metadata.model_id,
        bundle.metadata.version,
        cost_threshold
    )


def ensure_initialized(app: FastAPI) -> None:
    """Guarantees app.state has all tier artifacts initialized with thread-safe double-checked locking."""
    if not getattr(app.state, "initialized", False):
        with _init_lock:
            if not getattr(app.state, "initialized", False):
                init_state(app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Loads all five tiers' trained artifacts once on startup."""
    ensure_initialized(app)
    yield


app = FastAPI(
    title="SentinelNet Scoring Service",
    description="Multi-Tier Network Intrusion Detection & Production MLOps Serving Layer",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend clients (React/Vite on 5173, Next.js on 3000, Streamlit on 8501)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# =============================================================================
# Helper sync functions for non-blocking execution via asyncio.to_thread
# =============================================================================
def _sync_score_inference(bundle: InferenceBundle, flow_dict: Dict[str, Any], cost_threshold: float):
    """Synchronous CPU-bound pipeline for preprocessing, LightGBM and Autoencoder inference."""
    X = bundle.preprocessor.transform(flow_dict)
    supervised_prob = float(bundle.supervised_model.predict_proba(X)[0])
    recon_loss = float(bundle.autoencoder_model.compute_reconstruction_error(X)[0])
    ae_threshold = float(bundle.autoencoder_model.threshold if bundle.autoencoder_model.threshold is not None else 1.0)
    autoencoder_pred = int(recon_loss >= ae_threshold)
    supervised_pred = int(supervised_prob >= cost_threshold)
    return X, supervised_prob, recon_loss, ae_threshold, autoencoder_pred, supervised_pred


def _sync_explain_flow(explainer: IncidentExplainabilityEngine, X: np.ndarray, flow_dict: Dict[str, Any], top_k: int = 5):
    """Synchronous CPU-bound TreeSHAP explanation calculation."""
    return explainer.explain_flow(X, raw_flow_dict=flow_dict, top_k=top_k)


def _sync_evasion_test(adversarial_engine, autoencoder_model, supervised_model, X_batch, budget, cost_threshold):
    """Synchronous CPU-bound FGSM perturbation and recall benchmark."""
    X_adv = adversarial_engine.generate_fgsm_perturbation(
        autoencoder_model,
        X_batch,
        epsilon=budget
    )
    sup_probs = supervised_model.predict_proba(X_adv)
    sup_preds = (sup_probs >= cost_threshold).astype(int)
    sup_recall = float(np.mean(sup_preds))

    ae_thresh = autoencoder_model.threshold if autoencoder_model.threshold is not None else 1.0
    recon_losses = autoencoder_model.compute_reconstruction_error(X_adv)
    ae_preds = (recon_losses >= ae_thresh).astype(int)
    ae_recall = float(np.mean(ae_preds))

    combined_preds = (sup_preds | ae_preds).astype(int)
    combined_recall = float(np.mean(combined_preds))
    return combined_recall, sup_recall, ae_recall


def _sync_generate_graph_state(lateral_tracker: TemporalLateralTracker, flows: List[Dict[str, Any]]) -> GraphStateResponse:
    """Synchronous CPU-bound NetworkX graph computation and SVG layout generation."""
    df_window = pd.DataFrame(flows)
    report = lateral_tracker.analyze_window(df_window)

    G = nx.DiGraph()
    for _, row in df_window.iterrows():
        src = str(row["src_ip"])
        dst = str(row["dst_ip"])
        weight = G[src][dst]["weight"] + 1 if G.has_edge(src, dst) else 1
        G.add_edge(src, dst, weight=weight)

    flagged_pivots_map = {p.host_ip: p for p in report.flagged_pivots}
    flagged_ips = set(flagged_pivots_map.keys())

    pos = nx.spring_layout(G, seed=42) if len(G) > 0 else {}

    if pos:
        xs = [p[0] for p in pos.values()]
        ys = [p[1] for p in pos.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        range_x = max(1e-4, max_x - min_x)
        range_y = max(1e-4, max_y - min_y)
    else:
        min_x, min_y, range_x, range_y = 0.0, 0.0, 1.0, 1.0

    nodes: List[GraphNode] = []
    node_map: Dict[str, GraphNode] = {}

    out_degs = dict(G.out_degree()) if len(G) > 0 else {}
    in_degs = dict(G.in_degree()) if len(G) > 0 else {}
    prs = nx.pagerank(G, alpha=0.85) if len(G) > 0 else {}

    deg_vals = list(out_degs.values())
    mean_deg = float(np.mean(deg_vals)) if deg_vals else 0.0
    std_deg = float(np.std(deg_vals)) if deg_vals and np.std(deg_vals) > 1e-4 else 1.0

    max_zscore = 0.0
    max_novelty = 0.0
    max_pr_delta = 0.0

    for node_id in G.nodes():
        px, py = pos.get(node_id, (0.0, 0.0))
        svg_x = round(60.0 + ((px - min_x) / range_x) * 680.0, 1)
        svg_y = round(60.0 + ((py - min_y) / range_y) * 480.0, 1)

        out_deg = out_degs.get(node_id, 0)
        in_deg = in_degs.get(node_id, 0)
        pr = prs.get(node_id, 0.0)
        base_pr = lateral_tracker.baseline_pagerank.get(node_id, 0.0)
        pr_delta = pr - base_pr

        zscore = (out_deg - mean_deg) / std_deg

        neighbors = set(G.successors(node_id))
        novel = sum(1 for dst in neighbors if (node_id, dst) not in lateral_tracker.baseline_edges)
        novelty = (novel / max(1, len(neighbors))) if neighbors else 0.0

        is_pivot = node_id in flagged_ips
        pivot_info = flagged_pivots_map.get(node_id)
        reasons = pivot_info.reasons if pivot_info else []

        if is_pivot:
            role = "PIVOT_HOST"
            color = "#ef4444"
            radius = 18.0
        elif "10.0.1" in str(node_id):
            role = "INTERNAL_SERVER"
            color = "#3b82f6"
            radius = 14.0
        elif "192.168.1." in str(node_id):
            role = "DMZ_SERVER"
            color = "#8b5cf6"
            radius = 13.0
        else:
            role = "ENDPOINT"
            color = "#10b981"
            radius = 11.0

        if zscore > max_zscore:
            max_zscore = zscore
        if novelty > max_novelty:
            max_novelty = novelty
        if pr_delta > max_pr_delta:
            max_pr_delta = pr_delta

        gn = GraphNode(
            id=node_id,
            label=node_id,
            x=svg_x,
            y=svg_y,
            r=radius,
            color=color,
            role=role,
            is_pivot=is_pivot,
            out_degree=out_deg,
            in_degree=in_deg,
            degree_zscore=round(float(zscore), 2),
            jaccard_novelty=round(float(novelty), 3),
            pagerank=round(float(pr), 4),
            pagerank_delta=round(float(pr_delta), 4),
            reasons=reasons
        )
        nodes.append(gn)
        node_map[node_id] = gn

    edges: List[GraphEdge] = []
    for u, v, data in G.edges(data=True):
        if u in node_map and v in node_map:
            edge_color = "#ef4444" if (u in flagged_ips or v in flagged_ips) else "#475569"
            edges.append(GraphEdge(
                source=u,
                target=v,
                source_x=node_map[u].x,
                source_y=node_map[u].y,
                target_x=node_map[v].x,
                target_y=node_map[v].y,
                weight=int(data.get("weight", 1)),
                color=edge_color
            ))

    metrics_summary = GraphMetricsSummary(
        window_start=round(float(report.window_start), 1),
        window_end=round(float(report.window_end), 1),
        num_nodes=len(nodes),
        num_edges=len(edges),
        num_pivots=len(report.flagged_pivots),
        max_degree_zscore=round(float(max_zscore), 2),
        max_jaccard_novelty=round(float(max_novelty), 3),
        max_pagerank_delta=round(float(max_pr_delta), 4)
    )

    return GraphStateResponse(
        nodes=nodes,
        edges=edges,
        metrics=metrics_summary,
        num_nodes=len(nodes),
        num_edges=len(edges),
        flagged_pivots=[p.host_ip for p in report.flagged_pivots]
    )


# =============================================================================
# Health & Provenance (Publicly accessible for container orchestrators)
# =============================================================================
@app.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check(request: Request) -> HealthResponse:
    """Checks that all 5 tiers of the SentinelNet pipeline are successfully loaded."""
    ensure_initialized(request.app)
    state = request.app.state

    bundle = getattr(state, "bundle", None)
    tier0 = bundle is not None and getattr(bundle, "preprocessor", None) is not None
    tier1 = bundle is not None and getattr(bundle, "supervised_model", None) is not None
    tier2 = bundle is not None and getattr(bundle, "autoencoder_model", None) is not None
    tier3 = getattr(state, "lateral_tracker", None) is not None
    tier4 = getattr(state, "adversarial_engine", None) is not None
    tier5_cost = getattr(state, "cost_calibrator", None) is not None
    tier5_shap = getattr(state, "explainer", None) is not None
    tier5_drift = getattr(state, "drift_monitor", None) is not None

    all_tiers_loaded = all([tier0, tier1, tier2, tier3, tier4, tier5_cost, tier5_shap, tier5_drift])
    status_str = "HEALTHY" if all_tiers_loaded else "UNHEALTHY"

    return HealthResponse(
        status=status_str,
        all_tiers_loaded=all_tiers_loaded,
        model_id=bundle.metadata.model_id if bundle else None,
        version=bundle.metadata.version if bundle else None,
        dataset_hash=bundle.metadata.dataset_hash if bundle else None,
        model_status=bundle.metadata.status if bundle else None,
        tiers=HealthTierDetails(
            tier0_preprocessor=tier0,
            tier1_supervised=tier1,
            tier2_autoencoder=tier2,
            tier3_lateral_graph=tier3,
            tier4_adversarial_engine=tier4,
            tier5_cost_calibrator=tier5_cost,
            tier5_shap_explainer=tier5_shap,
            tier5_drift_monitor=tier5_drift
        )
    )


# =============================================================================
# Tier 1 & 2 Scoring + Tier 5 Cost Calibration (Protected by API Key + Rate Limit)
# =============================================================================
@app.post(
    "/score",
    response_model=ScoreResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key), Depends(score_rate_limiter)]
)
async def score_flow(record: FlowScoreRequest, request: Request) -> ScoreResponse:
    """Accepts a validated flow record, scores it with Tiers 1 and 2, applies Tier 5 cost-weighted threshold.

    Streams threats to WebSocket subscribers with attached TreeSHAP explanations.
    Uses non-blocking execution via asyncio.to_thread to maintain sub-millisecond event-loop responsiveness.
    """
    ensure_initialized(request.app)
    state = request.app.state
    bundle = state.bundle
    if bundle is None:
        raise HTTPException(status_code=503, detail="Production model not initialized.")

    t0 = time.perf_counter()
    flow_dict = record.model_dump()
    cost_thresh = float(record.supervised_threshold if record.supervised_threshold is not None else state.cost_threshold)

    # Execute ML inference in background thread to avoid event loop stalling
    X, supervised_prob, recon_loss, ae_threshold, autoencoder_pred, supervised_pred = await asyncio.to_thread(
        _sync_score_inference,
        bundle,
        flow_dict,
        cost_thresh
    )

    # Multi-Tier Ensemble Verdict
    is_attack = bool(supervised_pred or autoencoder_pred)
    calibrated_verdict = is_attack

    detection_tier = "BENIGN"
    if supervised_pred and autoencoder_pred:
        detection_tier = "TIER_1_AND_TIER_2"
    elif supervised_pred:
        detection_tier = "TIER_1_SUPERVISED"
    elif autoencoder_pred:
        detection_tier = "TIER_2_ZERO_DAY_ANOMALY"

    latency_ms = (time.perf_counter() - t0) * 1000.0

    # Telemetry SLA recording
    state.telemetry.record_inference(latency_ms, detection_tier, is_attack)

    # Ingest feature into rolling drift buffer
    if state.drift_buffer is not None:
        state.drift_buffer.add_features(X)

    # Add to rolling temporal graph buffer
    state.graph_flows.append(flow_dict)

    # Stream new alert via WebSocket if attack
    if is_attack and state.alert_manager.subscriber_count() > 0:
        try:
            summary = await asyncio.to_thread(_sync_explain_flow, state.explainer, X, flow_dict, 5)
            drivers = [
                SHAPFeatureDriver(
                    feature=d.feature_name,
                    value=round(float(d.feature_value), 2),
                    shap_attribution=round(float(d.shap_value), 4),
                    direction=d.impact_direction
                )
                for d in summary.top_drivers
            ]
            shap_payload = SHAPExplanationPayload(
                predicted_probability=round(summary.predicted_probability, 4),
                base_value=round(summary.base_value, 4),
                analyst_summary=summary.analyst_summary,
                top_drivers=drivers
            )
        except Exception as e:
            logger.exception("TreeSHAP explanation generation failed for alert: %s", e)
            shap_payload = SHAPExplanationPayload(
                predicted_probability=round(supervised_prob, 4),
                base_value=0.5,
                analyst_summary=f"Incident flagged by {detection_tier}.",
                top_drivers=[]
            )

        alert = AlertStreamItem(
            alert_id=f"ALT-{int(time.time() * 1000)}-{record.dst_port}",
            timestamp=record.timestamp,
            src_ip=record.src_ip,
            dst_ip=record.dst_ip,
            dst_port=record.dst_port,
            attack_type=record.attack_type or "SUSPICIOUS_FLOW",
            detection_tier=detection_tier,
            supervised_probability=round(supervised_prob, 4),
            reconstruction_loss=round(recon_loss, 4),
            is_attack=is_attack,
            explanation=shap_payload
        )
        await state.alert_manager.broadcast_alert(alert)

    return ScoreResponse(
        is_attack=is_attack,
        calibrated_verdict=calibrated_verdict,
        detection_tier=detection_tier,
        supervised_probability=round(supervised_prob, 4),
        supervised_score=round(supervised_prob, 4),
        supervised_prediction=supervised_pred,
        reconstruction_loss=round(recon_loss, 4),
        reconstruction_threshold=round(ae_threshold, 4),
        autoencoder_prediction=autoencoder_pred,
        cost_calibrated_threshold=round(cost_thresh, 4),
        model_version=bundle.metadata.version,
        latency_ms=round(latency_ms, 3)
    )


# =============================================================================
# Tier 3 Temporal Host Communication Graph State (Direct SVG Consumable)
# =============================================================================
@app.get(
    "/graph/state",
    response_model=GraphStateResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key)]
)
async def get_graph_state(request: Request) -> GraphStateResponse:
    """Returns current host communication graph with precomputed SVG canvas coordinates and metrics.

    Offloads NetworkX topology generation to a thread pool to avoid blocking the event loop.
    """
    ensure_initialized(request.app)
    state = request.app.state
    lateral_tracker: TemporalLateralTracker = state.lateral_tracker

    flows = list(state.graph_flows)
    if not flows:
        flows = state.generator.generate_baseline_flows(40).to_dict(orient="records")

    return await asyncio.to_thread(_sync_generate_graph_state, lateral_tracker, flows)


# =============================================================================
# Tier 4 Adversarial Perturbation Testing Lab (Protected by API Key + Rate Limit)
# =============================================================================
@app.post(
    "/evasion/test",
    response_model=EvasionTestResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key), Depends(evasion_rate_limiter)]
)
async def test_adversarial_evasion(req: EvasionTestRequest, request: Request) -> EvasionTestResponse:
    """Evaluates detection recall degradation against FGSM adversarial perturbation budget.

    Strictly rate limited to 5 requests/minute to prevent DoS via heavy PyTorch gradient computation.
    """
    ensure_initialized(request.app)
    state = request.app.state
    bundle = state.bundle
    if bundle is None:
        raise HTTPException(status_code=503, detail="Production model not initialized.")

    budget = float(req.perturbation_budget)
    X_attacks = state.sample_attacks
    if req.sample_size and req.sample_size < len(X_attacks):
        X_batch = X_attacks[:req.sample_size]
    else:
        X_batch = X_attacks

    # Offload heavy FGSM and evaluation to worker thread
    combined_recall, sup_recall, ae_recall = await asyncio.to_thread(
        _sync_evasion_test,
        state.adversarial_engine,
        bundle.autoencoder_model,
        bundle.supervised_model,
        X_batch,
        budget,
        state.cost_threshold
    )

    return EvasionTestResponse(
        perturbation_budget=budget,
        recall=round(combined_recall, 4),
        supervised_recall=round(sup_recall, 4),
        autoencoder_recall=round(ae_recall, 4),
        combined_recall=round(combined_recall, 4),
        samples_tested=len(X_batch)
    )


# =============================================================================
# Tier 5 WebSocket Live Alert & TreeSHAP Stream (Secured with API Key)
# =============================================================================
@app.websocket("/alerts/stream")
async def alerts_stream(websocket: WebSocket, api_key: Optional[str] = None):
    """Streams live alerts with TreeSHAP explanations. Handles client disconnects gracefully.

    Authenticated via 'api_key' query parameter or 'X-API-Key' / 'Sec-WebSocket-Protocol' header.
    """
    is_authenticated = await verify_ws_api_key(websocket, api_key=api_key)
    if not is_authenticated:
        return

    ensure_initialized(websocket.app)
    alert_mgr: AlertStreamManager = websocket.app.state.alert_manager
    await alert_mgr.connect(websocket)

    try:
        while True:
            # Listen for ping or messages from dashboard client
            message = await websocket.receive_text()
            # Send keepalive acknowledgement
            await websocket.send_json({
                "event": "HEARTBEAT",
                "received": message,
                "timestamp": time.time()
            })
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        await alert_mgr.disconnect(websocket)


# =============================================================================
# Tier 5 Statistical Drift Status
# =============================================================================
@app.get(
    "/drift/status",
    response_model=DriftStatusResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key)]
)
async def get_drift_status(request: Request) -> DriftStatusResponse:
    """Returns KS and PSI drift statistics and boolean retraining recommendation flag."""
    ensure_initialized(request.app)
    state = request.app.state
    drift_monitor: StatisticalDriftMonitor = state.drift_monitor

    # If the drift buffer has evaluated a production report, use it; otherwise evaluate on reference
    rep = state.drift_buffer.latest_drift_report
    if rep is None:
        rep = drift_monitor.evaluate_drift(drift_monitor.reference_data[:100])

    details = [
        FeatureDriftStat(
            feature_name=d.feature_name,
            ks_statistic=round(float(d.ks_statistic), 4),
            ks_pvalue=round(float(d.ks_pvalue), 4),
            psi_score=round(float(d.psi_score), 4),
            is_drifted=bool(d.is_drifted),
            severity=str(d.severity)
        )
        for d in rep.feature_details.values()
    ]

    return DriftStatusResponse(
        status="DRIFT_DETECTED" if rep.dataset_drift_detected else "STABLE",
        retraining_recommended=bool(rep.retraining_recommended),
        drift_feature_ratio=round(float(rep.drift_feature_ratio), 4),
        num_drifted_features=int(rep.num_drifted_features),
        total_features_evaluated=int(rep.total_features_evaluated),
        dataset_drift_detected=bool(rep.dataset_drift_detected),
        feature_details=details
    )


# =============================================================================
# Backward Compatibility Endpoints (Marked Deprecated)
# =============================================================================
class FlowPredictionResponse(BaseModel):
    is_attack: bool
    detection_tier: str
    supervised_probability: float
    supervised_prediction: int
    reconstruction_loss: float
    reconstruction_threshold: float
    autoencoder_prediction: int
    model_version: str
    inference_latency_ms: float


class BatchPredictionRequest(BaseModel):
    flows: List[Dict[str, Any]]
    supervised_threshold: Optional[float] = 0.5


@app.get("/metrics", status_code=status.HTTP_200_OK, deprecated=True)
async def get_telemetry_metrics(request: Request, response: Response) -> Dict[str, Any]:
    """Exposes real-time serving SLAs, latency percentiles, and detection statistics.

    Deprecated: Migrate to standard Prometheus /health telemetry.
    """
    response.headers["Deprecation"] = "true"
    ensure_initialized(request.app)
    return request.app.state.telemetry.get_metrics()


@app.get("/drift", status_code=status.HTTP_200_OK, deprecated=True, dependencies=[Depends(verify_api_key)])
async def get_legacy_drift(request: Request, response: Response) -> Dict[str, Any]:
    """Legacy drift endpoint. Deprecated: Use GET /drift/status."""
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</drift/status>; rel="successor-version"'
    ensure_initialized(request.app)
    return request.app.state.drift_buffer.get_latest_report() or {"status": "BUFFERING"}


@app.post(
    "/predict",
    response_model=FlowPredictionResponse,
    status_code=status.HTTP_200_OK,
    deprecated=True,
    dependencies=[Depends(verify_api_key)]
)
async def predict_flow(
    record: NetFlowRecord,
    request: Request,
    response: Response,
    supervised_threshold: float = 0.5
) -> FlowPredictionResponse:
    """Legacy single flow scoring endpoint. Deprecated: Use POST /score."""
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</score>; rel="successor-version"'
    ensure_initialized(request.app)
    state = request.app.state
    if state.bundle is None:
        raise HTTPException(status_code=503, detail="Production model not initialized.")

    t0 = time.perf_counter()
    flow_dict = record.model_dump()
    score = await asyncio.to_thread(
        state.bundle.score_single_flow,
        flow_dict,
        supervised_threshold=supervised_threshold
    )
    latency_ms = (time.perf_counter() - t0) * 1000.0

    state.telemetry.record_inference(latency_ms, score["detection_tier"], score["is_attack"])
    if state.drift_buffer is not None:
        X = await asyncio.to_thread(state.bundle.preprocessor.transform, flow_dict)
        state.drift_buffer.add_features(X)

    score["inference_latency_ms"] = round(latency_ms, 3)
    return FlowPredictionResponse(**score)


@app.post(
    "/predict/batch",
    status_code=status.HTTP_200_OK,
    deprecated=True,
    dependencies=[Depends(verify_api_key)]
)
async def predict_batch(
    req: BatchPredictionRequest,
    request: Request,
    response: Response
) -> Dict[str, Any]:
    """Legacy batch prediction endpoint. Deprecated: Use streaming POST /score."""
    response.headers["Deprecation"] = "true"
    ensure_initialized(request.app)
    state = request.app.state
    if state.bundle is None:
        raise HTTPException(status_code=503, detail="Production model not initialized.")

    t0 = time.perf_counter()
    df = pd.DataFrame(req.flows)
    thresh = req.supervised_threshold if req.supervised_threshold is not None else 0.5
    df_scored = await asyncio.to_thread(state.bundle.score_batch, df, supervised_threshold=thresh)
    total_time_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "num_scored": len(df),
        "total_time_ms": round(total_time_ms, 2),
        "mean_latency_per_flow_ms": round(total_time_ms / max(1, len(df)), 4),
        "num_attacks": int(df_scored["is_attack"].sum()),
        "results": df_scored[["supervised_prob", "reconstruction_loss", "is_attack"]].to_dict(orient="records")
    }


@app.post(
    "/explain",
    status_code=status.HTTP_200_OK,
    deprecated=True,
    dependencies=[Depends(verify_api_key)]
)
async def explain_flow(
    record: NetFlowRecord,
    request: Request,
    response: Response,
    top_k: int = 5
) -> Dict[str, Any]:
    """Legacy TreeSHAP incident triage endpoint. Deprecated: Explanations are bundled in POST /score and WebSocket alerts."""
    response.headers["Deprecation"] = "true"
    ensure_initialized(request.app)
    state = request.app.state
    if state.bundle is None or state.explainer is None:
        raise HTTPException(status_code=503, detail="Explainability engine not initialized.")

    flow_dict = record.model_dump()
    X = await asyncio.to_thread(state.bundle.preprocessor.transform, flow_dict)
    summary = await asyncio.to_thread(state.explainer.explain_flow, X, raw_flow_dict=flow_dict, top_k=top_k)

    return {
        "predicted_probability": summary.predicted_probability,
        "analyst_summary": summary.analyst_summary,
        "top_drivers": [
            {
                "feature": d.feature_name,
                "value": d.feature_value,
                "shap_attribution": round(d.shap_value, 4),
                "direction": d.impact_direction
            }
            for d in summary.top_drivers
        ]
    }


@app.post(
    "/graph/analyze",
    status_code=status.HTTP_200_OK,
    deprecated=True,
    dependencies=[Depends(verify_api_key)]
)
async def analyze_lateral_movement(
    flows: List[Dict[str, Any]],
    request: Request,
    response: Response
) -> Dict[str, Any]:
    """Legacy graph analyze endpoint. Deprecated: Use GET /graph/state."""
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</graph/state>; rel="successor-version"'
    ensure_initialized(request.app)
    if not flows:
        return {"flagged_pivots": []}

    df_window = pd.DataFrame(flows)
    report = await asyncio.to_thread(request.app.state.lateral_tracker.analyze_window, df_window)

    return {
        "num_nodes": report.num_nodes,
        "num_edges": report.num_edges,
        "num_flagged_pivots": len(report.flagged_pivots),
        "pivots": [
            {
                "host_ip": p.host_ip,
                "out_degree": p.out_degree,
                "zscore": round(p.degree_zscore, 2),
                "novelty": round(p.jaccard_novelty, 3),
                "pagerank_delta": round(p.pagerank_delta, 3),
                "reasons": p.reasons
            }
            for p in report.flagged_pivots
        ]
    }
