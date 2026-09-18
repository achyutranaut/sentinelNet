"""SentinelNet Cascading Arbitration & Multi-Tier Threat Triage Engine.

Arbitrates verdicts across Tier 0 (Heuristics), Tier 1 (LightGBM),
Tier 2 (Autoencoder Anomaly), and Tier 3 (Graph Lateral Movement) into a single,
cohesive security operations incident record with dollar risk exposure and SHAP attribution.
"""

from dataclasses import asdict, dataclass
from enum import Enum
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.graph.lateral_tracker import TemporalLateralTracker
from src.ingestion.preprocessor import FlowPreprocessor
from src.models.anomaly_autoencoder import AnomalyAutoencoder
from src.models.supervised_classifier import SupervisedFlowClassifier
from src.ops.cost_calibrator import SOCCostCalibrator
from src.ops.explainability import IncidentExplainabilityEngine
from src.tier0_baseline.baseline_rules import Tier0HeuristicDetector


class ThreatSeverity(str, Enum):
    BENIGN = "BENIGN"
    SUSPICIOUS_ANOMALY = "SUSPICIOUS_ANOMALY"
    ZERO_DAY_ANOMALY = "ZERO_DAY_ANOMALY"
    STEALTH_LATERAL_MOVEMENT = "STEALTH_LATERAL_MOVEMENT"
    HIGH_RISK_KNOWN_ATTACK = "HIGH_RISK_KNOWN_ATTACK"
    CRITICAL_BREACH = "CRITICAL_BREACH"


@dataclass
class FlowTriageVerdict:
    flow_id: str
    timestamp: float
    src_ip: str
    dst_ip: str
    dst_port: int
    severity: ThreatSeverity
    is_malicious: bool
    triggering_tier: str
    primary_threat_category: str
    confidence_score: float
    financial_risk_exposure: float
    tier_breakdown: Dict[str, Any]
    triage_narrative: str
    top_shap_drivers: List[Dict[str, Any]]
    processing_latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


class CascadingArbitrationEngine:
    """Unified arbitration engine integrating Tiers 0, 1, 2, 3, and 5."""

    def __init__(
        self,
        preprocessor: FlowPreprocessor,
        supervised_clf: SupervisedFlowClassifier,
        autoencoder: AnomalyAutoencoder,
        lateral_tracker: Optional[TemporalLateralTracker] = None,
        optimal_threshold: float = 0.15,
        cost_fn: float = 50000.0,
        cost_fp: float = 50.0
    ):
        self.preprocessor = preprocessor
        self.supervised_clf = supervised_clf
        self.autoencoder = autoencoder
        self.lateral_tracker = lateral_tracker
        self.optimal_threshold = optimal_threshold
        self.cost_fn = cost_fn
        self.cost_fp = cost_fp

        self.tier0 = Tier0HeuristicDetector()
        self.explainer = IncidentExplainabilityEngine(supervised_clf)

    def arbitrate_flow(
        self,
        flow_record: Dict[str, Any],
        flow_id: Optional[str] = None,
        explain: bool = False
    ) -> FlowTriageVerdict:
        """Evaluates a single raw flow record through the multi-tier cascade."""
        t0 = time.perf_counter()
        fid = flow_id or f"flow-{int(t0 * 1e6) % 1000000:06d}"
        ts = float(flow_record.get("timestamp", time.time()))
        src_ip = str(flow_record.get("src_ip", "0.0.0.0"))
        dst_ip = str(flow_record.get("dst_ip", "0.0.0.0"))
        dst_port = int(flow_record.get("dst_port", 0))

        # ------------------------------------------------------------------
        # Tier 0: Fast Heuristic Filter
        # ------------------------------------------------------------------
        t0_flag = bool(self.tier0.predict_record(flow_record))

        # Transform features for ML tiers
        if hasattr(self.preprocessor, "transform_record"):
            X_norm = self.preprocessor.transform_record(flow_record)
        else:
            X_norm = self.preprocessor.transform([flow_record])

        # ------------------------------------------------------------------
        # Tier 1: Supervised LightGBM Signature Classifier
        # ------------------------------------------------------------------
        t1_prob = float(self.supervised_clf.predict_proba(X_norm)[0])
        t1_calibrated_flag = bool(t1_prob >= self.optimal_threshold)

        # ------------------------------------------------------------------
        # Tier 2: Unsupervised Deep Autoencoder Reconstruction
        # ------------------------------------------------------------------
        t2_loss = float(self.autoencoder.compute_reconstruction_error(X_norm)[0])
        t2_threshold = float(self.autoencoder.threshold or 0.8)
        t2_flag = bool(t2_loss >= t2_threshold)

        # ------------------------------------------------------------------
        # Tier 3: Graph Lateral Movement Tracking
        # ------------------------------------------------------------------
        t3_flag = False
        t3_reasons: List[str] = []
        if self.lateral_tracker is not None and self._is_internal_ip(src_ip) and self._is_internal_ip(dst_ip):
            # Check single flow edge novelty
            if (src_ip, dst_ip) not in self.lateral_tracker.baseline_edges:
                t3_flag = True
                t3_reasons.append(f"Novel East-West pivot: {src_ip} -> {dst_ip}")

        # ------------------------------------------------------------------
        # Decision Arbitration Hierarchy
        # ------------------------------------------------------------------
        severity = ThreatSeverity.BENIGN
        is_malicious = False
        triggering_tier = "NONE"
        threat_category = "BENIGN_TRAFFIC"
        confidence = 1.0 - t1_prob

        # Case 1: Active Lateral Movement Pivot (Tier 3 override)
        if t3_flag:
            severity = ThreatSeverity.STEALTH_LATERAL_MOVEMENT
            is_malicious = True
            triggering_tier = "TIER_3_GRAPH"
            threat_category = "LATERAL_MOVEMENT"
            confidence = max(0.85, t1_prob)

        # Case 2: Known Signature Attack (Tier 1 threshold exceeded)
        elif t1_calibrated_flag:
            is_malicious = True
            confidence = t1_prob
            triggering_tier = "TIER_1_SUPERVISED"
            if t0_flag:
                severity = ThreatSeverity.CRITICAL_BREACH
                threat_category = "VOLUMETRIC_OR_BRUTE_ATTACK"
            else:
                severity = ThreatSeverity.HIGH_RISK_KNOWN_ATTACK
                threat_category = "KNOWN_SIGNATURE_EXPLOIT"

        # Case 3: Tier 0 Heuristic Triggered (while Tier 1 might be uncertain)
        elif t0_flag:
            severity = ThreatSeverity.HIGH_RISK_KNOWN_ATTACK
            is_malicious = True
            triggering_tier = "TIER_0_HEURISTIC"
            threat_category = "RULE_BASED_DETECTION"
            confidence = 0.90

        # Case 4: Zero-Day / Novel Anomaly (Tier 2 triggers while Tier 1 is blind)
        elif t2_flag:
            severity = ThreatSeverity.ZERO_DAY_ANOMALY
            is_malicious = True
            triggering_tier = "TIER_2_AUTOENCODER"
            threat_category = "ZERO_DAY_ANOMALY"
            confidence = float(min(0.99, 0.70 + (t2_loss / max(0.01, t2_threshold) - 1.0) * 0.1))

        # Case 5: Borderline Suspicious
        elif t1_prob >= 0.05:
            severity = ThreatSeverity.SUSPICIOUS_ANOMALY
            is_malicious = False
            triggering_tier = "TIER_1_BORDERLINE"
            threat_category = "BORDERLINE_TRAFFIC"
            confidence = t1_prob

        # Calculate Financial Risk Exposure
        if is_malicious:
            risk_exposure = self.cost_fn * confidence
        else:
            risk_exposure = self.cost_fp if severity == ThreatSeverity.SUSPICIOUS_ANOMALY else 0.0

        # Narrative generation
        if is_malicious:
            narrative = (
                f"INCIDENT ALERT [{severity.value}] triggered by {triggering_tier} with "
                f"{confidence:.1%} confidence. Estimated potential breach exposure: ${risk_exposure:,.2f}."
            )
        else:
            narrative = f"Flow classified as {severity.value}. Normal traffic pattern (Confidence: {confidence:.1%})."

        # SHAP attribution (computed if requested or on alerts)
        top_drivers: List[Dict[str, Any]] = []
        if explain:
            try:
                triage = self.explainer.explain_flow(X_norm, flow_record, top_k=3)
                for d in triage.top_drivers:
                    top_drivers.append({
                        "feature": d.feature_name,
                        "value": d.feature_value,
                        "shap_attribution": d.shap_value,
                        "impact": d.impact_direction
                    })
            except Exception:
                pass

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        tier_breakdown = {
            "tier0_heuristic_flag": t0_flag,
            "tier1_signature_probability": round(t1_prob, 4),
            "tier1_calibrated_threshold": self.optimal_threshold,
            "tier2_recon_mse": round(t2_loss, 4),
            "tier2_recon_threshold": round(t2_threshold, 4),
            "tier2_anomaly_flag": t2_flag,
            "tier3_lateral_flag": t3_flag,
            "tier3_notes": t3_reasons
        }

        return FlowTriageVerdict(
            flow_id=fid,
            timestamp=ts,
            src_ip=src_ip,
            dst_ip=dst_ip,
            dst_port=dst_port,
            severity=severity,
            is_malicious=is_malicious,
            triggering_tier=triggering_tier,
            primary_threat_category=threat_category,
            confidence_score=round(confidence, 4),
            financial_risk_exposure=round(risk_exposure, 2),
            tier_breakdown=tier_breakdown,
            triage_narrative=narrative,
            top_shap_drivers=top_drivers,
            processing_latency_ms=round(elapsed_ms, 3)
        )

    @staticmethod
    def _is_internal_ip(ip: str) -> bool:
        """Determines if an IPv4 address is an enterprise internal RFC1918 host."""
        return (
            ip.startswith("10.") or
            ip.startswith("192.168.") or
            (ip.startswith("172.") and 16 <= int(ip.split(".")[1]) <= 31)
        )
