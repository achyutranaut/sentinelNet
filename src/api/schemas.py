"""Pydantic Request and Response Schemas for SentinelNet Serving Layer (API Contracts).

Defines strict validation invariants, ML-security constraints, and standardized
Pydantic contracts across all HTTP and WebSocket endpoints.
"""

from ipaddress import ip_address
import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FlowScoreRequest(BaseModel):
    """Pydantic schema for scoring a single NetFlow record on POST /score."""
    model_config = ConfigDict(extra="ignore")

    timestamp: float = Field(..., description="UNIX epoch timestamp in seconds")
    src_ip: str = Field(..., description="Source IPv4 address")
    dst_ip: str = Field(..., description="Destination IPv4 address")
    dst_port: int = Field(..., ge=1, le=65535, description="Destination TCP/UDP port (1-65535)")
    flow_duration_ms: float = Field(..., ge=0.0, le=86400000.0, description="Flow duration in milliseconds (max 24h)")
    total_fwd_packets: int = Field(..., ge=0, description="Total forward packets")
    total_bwd_packets: int = Field(..., ge=0, description="Total backward packets")
    total_fwd_bytes: float = Field(..., ge=0.0, description="Total forward bytes")
    total_bwd_bytes: float = Field(..., ge=0.0, description="Total backward bytes")
    fwd_packet_length_mean: float = Field(0.0, ge=0.0)
    fwd_packet_length_std: float = Field(0.0, ge=0.0)
    bwd_packet_length_mean: float = Field(0.0, ge=0.0)
    bwd_packet_length_std: float = Field(0.0, ge=0.0)
    flow_bytes_per_sec: float = Field(0.0, ge=0.0)
    flow_packets_per_sec: float = Field(0.0, ge=0.0)
    flow_iat_mean_ms: float = Field(0.0, ge=0.0)
    flow_iat_std_ms: float = Field(0.0, ge=0.0)
    flow_iat_max_ms: float = Field(0.0, ge=0.0)
    flow_iat_min_ms: float = Field(0.0, ge=0.0)
    fwd_iat_mean_ms: float = Field(0.0, ge=0.0)
    bwd_iat_mean_ms: float = Field(0.0, ge=0.0)
    fwd_syn_flags: int = Field(0, ge=0)
    fwd_rst_flags: int = Field(0, ge=0)
    fwd_psh_flags: int = Field(0, ge=0)
    fwd_ack_flags: int = Field(0, ge=0)
    bwd_syn_flags: int = Field(0, ge=0)
    bwd_rst_flags: int = Field(0, ge=0)
    bwd_psh_flags: int = Field(0, ge=0)
    bwd_ack_flags: int = Field(0, ge=0)
    header_length_ratio: float = Field(0.0, ge=0.0)
    packet_size_variance: float = Field(0.0, ge=0.0)
    down_up_ratio: float = Field(0.0, ge=0.0)
    avg_fwd_segment_size: float = Field(0.0, ge=0.0)
    avg_bwd_segment_size: float = Field(0.0, ge=0.0)
    attack_type: Optional[str] = Field("UNKNOWN", description="Ground truth or suspected attack tag")
    label: Optional[int] = Field(0, ge=0, le=1, description="Ground truth binary label")
    supervised_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Optional override threshold")

    @field_validator("src_ip", "dst_ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        s = str(v).strip()
        try:
            ip_address(s)
            return s
        except ValueError:
            raise ValueError(f"Invalid IP address format: {v}")

    @field_validator(
        "timestamp", "flow_duration_ms", "total_fwd_bytes", "total_bwd_bytes",
        "fwd_packet_length_mean", "fwd_packet_length_std", "bwd_packet_length_mean",
        "bwd_packet_length_std", "flow_bytes_per_sec", "flow_packets_per_sec",
        "flow_iat_mean_ms", "flow_iat_std_ms", "flow_iat_max_ms", "flow_iat_min_ms",
        "fwd_iat_mean_ms", "bwd_iat_mean_ms", "header_length_ratio",
        "packet_size_variance", "down_up_ratio", "avg_fwd_segment_size", "avg_bwd_segment_size",
        mode="before",
        check_fields=False
    )
    @classmethod
    def validate_finite_number(cls, v: Any) -> float:
        if v is None:
            return 0.0
        try:
            val = float(v)
        except (ValueError, TypeError):
            raise ValueError("Numeric feature must be a valid float")
        if math.isnan(val) or math.isinf(val):
            raise ValueError("Numeric feature cannot be NaN or Infinite")
        return val

    @model_validator(mode="after")
    def validate_packets_and_duration(self) -> "FlowScoreRequest":
        if self.total_fwd_packets + self.total_bwd_packets < 1:
            raise ValueError("A flow must have at least 1 total packet (forward or backward).")
        return self


class ScoreResponse(BaseModel):
    """Pydantic schema for multi-tier scoring response on POST /score."""
    is_attack: bool = Field(..., description="Final binary classification verdict")
    calibrated_verdict: bool = Field(..., description="Tier 5 cost-weighted calibrated verdict")
    detection_tier: str = Field(..., description="Triggered tier: TIER_1_SUPERVISED, TIER_2_ZERO_DAY_ANOMALY, TIER_1_AND_TIER_2, or BENIGN")
    supervised_probability: float = Field(..., description="Tier 1 LightGBM attack probability")
    supervised_score: float = Field(..., description="Alias for Tier 1 probability")
    supervised_prediction: int = Field(..., description="Binary prediction under calibrated threshold")
    reconstruction_loss: float = Field(..., description="Tier 2 Autoencoder anomaly reconstruction MSE")
    reconstruction_threshold: float = Field(..., description="Tier 2 Autoencoder decision threshold")
    autoencoder_prediction: int = Field(..., description="Binary anomaly prediction from autoencoder")
    cost_calibrated_threshold: float = Field(..., description="Tier 5 optimal cost-weighted decision threshold")
    model_version: str = Field(..., description="Version of inference bundle deployed")
    latency_ms: float = Field(..., description="Inference latency in milliseconds")


class GraphNode(BaseModel):
    """Graph node prepared with precalculated SVG coordinates and centrality metrics."""
    id: str = Field(..., description="Unique host identifier / IP")
    label: str = Field(..., description="Host IP label")
    x: float = Field(..., description="SVG canvas X coordinate for direct SVG rendering")
    y: float = Field(..., description="SVG canvas Y coordinate for direct SVG rendering")
    r: float = Field(12.0, description="Node circle radius (px)")
    color: str = Field(..., description="Hex color for SVG rendering")
    role: str = Field(..., description="Role: PIVOT_HOST, INTERNAL_SERVER, DMZ_SERVER, or ENDPOINT")
    is_pivot: bool = Field(..., description="True if host was flagged as lateral pivot")
    out_degree: int = Field(..., description="Host out-degree in window")
    in_degree: int = Field(0, description="Host in-degree in window")
    degree_zscore: float = Field(..., description="Degree burst z-score")
    jaccard_novelty: float = Field(..., description="Jaccard edge novelty to baseline")
    pagerank: float = Field(..., description="PageRank centrality")
    pagerank_delta: float = Field(..., description="PageRank shift from baseline")
    reasons: List[str] = Field(default_factory=list, description="Reasons flagged as pivot")


class GraphEdge(BaseModel):
    """Graph edge prepared with source and target SVG coordinates for direct line drawing."""
    source: str = Field(..., description="Source host IP")
    target: str = Field(..., description="Destination host IP")
    source_x: float = Field(..., description="Source node SVG X")
    source_y: float = Field(..., description="Source node SVG Y")
    target_x: float = Field(..., description="Target node SVG X")
    target_y: float = Field(..., description="Target node SVG Y")
    weight: int = Field(1, description="Flow count along edge")
    color: str = Field("#475569", description="SVG edge stroke color")


class GraphMetricsSummary(BaseModel):
    """Top-level network metrics for current graph temporal window."""
    window_start: float
    window_end: float
    num_nodes: int
    num_edges: int
    num_pivots: int
    max_degree_zscore: float
    max_jaccard_novelty: float
    max_pagerank_delta: float


class GraphStateResponse(BaseModel):
    """Direct SVG-ready graph state response for GET /graph/state."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metrics: GraphMetricsSummary
    num_nodes: int
    num_edges: int
    flagged_pivots: List[str]


class EvasionTestRequest(BaseModel):
    """Request model for POST /evasion/test."""
    perturbation_budget: float = Field(..., ge=0.0, le=1.0, description="Perturbation budget epsilon (e.g., 0.0 to 0.4)")
    padding_ratio: Optional[float] = Field(0.0, ge=0.0, le=2.0, description="Packet padding ratio")
    jitter_ms: Optional[float] = Field(0.0, ge=0.0, le=2000.0, description="Timing jitter in ms")
    sample_size: Optional[int] = Field(50, ge=1, le=500, description="Sample batch size")

    @model_validator(mode="before")
    @classmethod
    def handle_epsilon_alias(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "perturbation_budget" not in data and "epsilon" in data:
                data["perturbation_budget"] = data["epsilon"]
        return data


class EvasionTestResponse(BaseModel):
    """Response model for POST /evasion/test."""
    perturbation_budget: float
    recall: float
    supervised_recall: float
    autoencoder_recall: float
    combined_recall: float
    samples_tested: int


class SHAPFeatureDriver(BaseModel):
    """Single feature contribution from TreeSHAP."""
    feature: str
    value: float
    shap_attribution: float
    direction: str


class SHAPExplanationPayload(BaseModel):
    """Full TreeSHAP explanation payload for incident response."""
    predicted_probability: float
    base_value: float
    analyst_summary: str
    top_drivers: List[SHAPFeatureDriver]


class AlertStreamItem(BaseModel):
    """Alert streaming model broadcast over WebSocket GET /alerts/stream."""
    alert_id: str
    timestamp: float
    src_ip: str
    dst_ip: str
    dst_port: int
    attack_type: Optional[str] = "UNKNOWN"
    detection_tier: str
    supervised_probability: float
    reconstruction_loss: float
    is_attack: bool
    explanation: SHAPExplanationPayload


class FeatureDriftStat(BaseModel):
    """Statistical drift metrics for a single feature."""
    feature_name: str
    ks_statistic: float
    ks_pvalue: float
    psi_score: float
    is_drifted: bool
    severity: str


DriftFeatureStat = FeatureDriftStat


class DriftStatusResponse(BaseModel):
    """Drift status and retraining recommendation for GET /drift/status."""
    status: str
    retraining_recommended: bool
    drift_feature_ratio: float
    num_drifted_features: int
    total_features_evaluated: int
    dataset_drift_detected: bool
    feature_details: List[FeatureDriftStat] = Field(default_factory=list)


class HealthTierDetails(BaseModel):
    """Status flags for all 5 tiers of the SentinelNet ML pipeline."""
    tier0_preprocessor: bool
    tier1_supervised: bool
    tier2_autoencoder: bool
    tier3_lateral_graph: bool
    tier4_adversarial_engine: bool
    tier5_cost_calibrator: bool
    tier5_shap_explainer: bool
    tier5_drift_monitor: bool


class HealthResponse(BaseModel):
    """Health check response for GET /health."""
    status: str
    all_tiers_loaded: bool
    model_id: Optional[str] = None
    version: Optional[str] = None
    dataset_hash: Optional[str] = None
    model_status: Optional[str] = None
    tiers: HealthTierDetails
