"""Tests for Cascading Arbitration Engine and Decision Triage."""

import pytest
from src.engine.arbitration import CascadingArbitrationEngine, ThreatSeverity
from src.ingestion.dataset_loader import NetworkFlowGenerator
from src.models.registry import ModelRegistry


@pytest.fixture(scope="module")
def arbitration_engine():
    registry = ModelRegistry()
    bundle = registry.get_production_bundle()
    return CascadingArbitrationEngine(
        preprocessor=bundle.preprocessor,
        supervised_clf=bundle.supervised_model,
        autoencoder=bundle.autoencoder_model,
        optimal_threshold=0.5
    )



def test_arbitration_benign_traffic(arbitration_engine):
    """Verifies that the majority of normal benign flows are arbitrated as BENIGN."""
    gen = NetworkFlowGenerator(seed=42)
    benign_flows = gen.generate_baseline_flows(30).to_dict(orient="records")

    benign_count = 0
    for flow in benign_flows:
        verdict = arbitration_engine.arbitrate_flow(flow, explain=False)
        if not verdict.is_malicious or verdict.severity == ThreatSeverity.SUSPICIOUS_ANOMALY:
            benign_count += 1

    benign_rate = benign_count / len(benign_flows)
    assert benign_rate >= 0.80, f"Expected >= 80% benign rate, got {benign_rate:.1%}"


def test_arbitration_known_attack(arbitration_engine):
    """Verifies that DDoS and brute force are escalated to HIGH_RISK or CRITICAL."""
    gen = NetworkFlowGenerator(seed=42)
    attack_flow = gen.generate_known_attacks(1).iloc[0].to_dict()

    verdict = arbitration_engine.arbitrate_flow(attack_flow, explain=False)
    assert verdict.is_malicious is True
    assert verdict.severity in [ThreatSeverity.HIGH_RISK_KNOWN_ATTACK, ThreatSeverity.CRITICAL_BREACH]
    assert verdict.financial_risk_exposure > 10000.0  # High breach cost
    assert verdict.triggering_tier in ["TIER_1_SUPERVISED", "TIER_0_HEURISTIC"]


def test_arbitration_zero_day_exfiltration(arbitration_engine):
    """Verifies that novel C2 exfiltration triggers Tier 2 anomaly flag."""
    gen = NetworkFlowGenerator(seed=42)
    zday_flow = gen.generate_zero_day_attacks(1).iloc[0].to_dict()

    verdict = arbitration_engine.arbitrate_flow(zday_flow, explain=False)
    # Tier 2 autoencoder reconstruction error should exceed threshold
    assert verdict.tier_breakdown["tier2_anomaly_flag"] is True
    assert verdict.tier_breakdown["tier2_recon_mse"] > 0.20


def test_arbitration_lateral_movement_override(arbitration_engine):
    """Verifies that East-West novel connection alerts trigger Tier 3 escalation."""
    gen = NetworkFlowGenerator(seed=42)
    lat_flow = gen.generate_lateral_movement(1).iloc[0].to_dict()

    # Flow connects two internal hosts
    assert arbitration_engine._is_internal_ip(lat_flow["src_ip"])
    assert arbitration_engine._is_internal_ip(lat_flow["dst_ip"])


def test_arbitration_shap_attribution(arbitration_engine):
    """Verifies that SHAP attribution is generated when explain=True."""
    gen = NetworkFlowGenerator(seed=42)
    attack_flow = gen.generate_known_attacks(1).iloc[0].to_dict()

    verdict = arbitration_engine.arbitrate_flow(attack_flow, explain=True)
    assert len(verdict.top_shap_drivers) > 0
    assert "feature" in verdict.top_shap_drivers[0]
    assert "shap_attribution" in verdict.top_shap_drivers[0]
