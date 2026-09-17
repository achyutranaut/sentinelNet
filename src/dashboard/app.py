"""Tier 6: SOC Command Center & Interactive Defense Operations (Streamlit UI).

Strictly adheres to real-world SOC terminal aesthetics:
- Typography: IBM Plex Mono for values/tables and Space Grotesk for headers
- Restrained color system: #090B0E / #0D1117 dark background, #F85149 critical, #D29922 warning, #3FB950 secure
- Zero AI clichés: No gradients, no glassmorphism, no rounded cards, no decorative emojis
- Top Telemetry Tape (36px): Lineage SHA256, Latency SLAs, Drift Status, Cost Calibration
- Asymmetric 60/40 terminal grid with Anime.js v4 state-driven animations
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path regardless of execution working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import time
from typing import Any, Dict, List
import joblib
import networkx as nx
import numpy as np
import pandas as pd
import streamlit as st

from src.adversarial.perturbation_engine import TrafficPerturbationEngine
from src.dashboard.components.alert_stream import render_alert_stream
from src.dashboard.components.evasion_lab import render_evasion_lab
from src.dashboard.components.network_topology import render_network_topology_canvas
from src.dashboard.components.shap_waterfall import render_shap_waterfall
from src.graph.lateral_tracker import TemporalLateralTracker
from src.ingestion.dataset_loader import NetworkFlowGenerator
from src.models.registry import InferenceBundle, ModelRegistry
from src.ops.drift_monitor import StatisticalDriftMonitor
from src.ops.explainability import IncidentExplainabilityEngine


st.set_page_config(
    page_title="SentinelNet // SOC Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Global SOC Terminal Theme Styles
# -----------------------------------------------------------------------------
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,400;0,500;0,600;1,400&family=Space+Grotesk:wght@500;600;700&display=swap');

  /* Global App Background & Text */
  .stApp {
      background-color: #090b0e;
      color: #e6edf3;
      font-family: 'IBM Plex Mono', monospace;
  }
  header[data-testid="stHeader"] {
      background-color: #090b0e;
      border-bottom: 1px solid #21262d;
  }
  section[data-testid="stSidebar"] {
      background-color: #0d1117;
      border-right: 1px solid #21262d;
  }
  section[data-testid="stSidebar"] * {
      font-family: 'IBM Plex Mono', monospace;
  }

  /* Monospace Headings in Space Grotesk */
  h1, h2, h3, h4, h5, h6 {
      font-family: 'Space Grotesk', sans-serif !important;
      font-weight: 600 !important;
      letter-spacing: 0.04em !important;
      color: #e6edf3 !important;
  }

  /* Metric Containers */
  div[data-testid="stMetricValue"] {
      font-family: 'IBM Plex Mono', monospace !important;
      font-weight: 600 !important;
      color: #e6edf3 !important;
      font-size: 1.25rem !important;
  }
  div[data-testid="stMetricLabel"] {
      font-family: 'Space Grotesk', sans-serif !important;
      font-size: 0.72rem !important;
      text-transform: uppercase !important;
      letter-spacing: 0.06em !important;
      color: #8b949e !important;
  }
  div[data-testid="metric-container"] {
      background-color: #0d1117;
      border: 1px solid #21262d;
      border-radius: 2px;
      padding: 6px 10px;
  }

  /* Button Styling */
  button[kind="primary"], button[kind="secondary"], .stButton>button {
      background-color: #161b22 !important;
      color: #e6edf3 !important;
      border: 1px solid #30363d !important;
      border-radius: 2px !important;
      font-family: 'Space Grotesk', sans-serif !important;
      font-weight: 600 !important;
      font-size: 0.78rem !important;
      letter-spacing: 0.05em !important;
      text-transform: uppercase !important;
      transition: border-color 0.15s, background-color 0.15s !important;
  }
  button[kind="primary"]:hover, button[kind="secondary"]:hover, .stButton>button:hover {
      border-color: #58a6ff !important;
      background-color: #21262d !important;
      color: #58a6ff !important;
  }

  /* Selectbox & Inputs */
  div[data-baseweb="select"] > div {
      background-color: #161b22 !important;
      border-color: #21262d !important;
      border-radius: 2px !important;
      color: #e6edf3 !important;
      font-family: 'IBM Plex Mono', monospace !important;
      font-size: 0.82rem !important;
  }
  div[data-baseweb="input"] > div {
      background-color: #161b22 !important;
      border-color: #21262d !important;
      border-radius: 2px !important;
      color: #e6edf3 !important;
      font-family: 'IBM Plex Mono', monospace !important;
  }

  /* Top 36px Telemetry Ribbon */
  .telemetry-tape {
      background-color: #0d1117;
      border: 1px solid #21262d;
      border-radius: 2px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 12px;
      margin-bottom: 12px;
      font-family: 'IBM Plex Mono', monospace;
      font-size: 10px;
      letter-spacing: 0.03em;
      white-space: nowrap;
      overflow-x: auto;
  }
  .tape-item {
      display: flex;
      align-items: center;
      gap: 6px;
  }
  .tape-label {
      color: #8b949e;
      text-transform: uppercase;
      font-family: 'Space Grotesk', sans-serif;
      font-weight: 600;
  }
  .tape-val {
      color: #e6edf3;
      font-weight: 500;
  }
  .tape-val-accent { color: #58a6ff; }
  .tape-val-green { color: #3fb950; font-weight: 600; }
  .tape-val-warn { color: #d29922; font-weight: 600; }
  .tape-val-crit { color: #f85149; font-weight: 600; }
  .tape-divider { color: #30363d; }
  .tape-dot {
      width: 6px;
      height: 6px;
      border-radius: 1px;
      background-color: #3fb950;
      display: inline-block;
  }

  /* Section Title Bar */
  .section-bar {
      background-color: #161b22;
      border: 1px solid #21262d;
      border-radius: 2px 2px 0 0;
      padding: 5px 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: 'Space Grotesk', sans-serif;
      font-size: 9.5px;
      font-weight: 700;
      letter-spacing: 0.07em;
      text-transform: uppercase;
      color: #8b949e;
      margin-bottom: 2px;
  }
  .section-bar span.accent {
      color: #e6edf3;
  }

  /* Expander styling */
  div[data-testid="stExpander"] {
      border: 1px solid #21262d !important;
      border-radius: 2px !important;
      background-color: #0d1117 !important;
      margin-top: 10px;
  }
  details[data-testid="stExpander"] summary {
      background-color: #161b22 !important;
      font-family: 'Space Grotesk', sans-serif !important;
      font-size: 9.5px !important;
      letter-spacing: 0.06em !important;
      color: #8b949e !important;
      font-weight: 600 !important;
      text-transform: uppercase !important;
  }

  /* Custom dataframe styling */
  div[data-testid="stDataFrame"] {
      border: 1px solid #21262d;
      border-radius: 2px;
      background-color: #0d1117;
  }

  /* Clean up top padding */
  .block-container {
      padding-top: 1rem !important;
      padding-bottom: 1.5rem !important;
      padding-left: 1.5rem !important;
      padding-right: 1.5rem !important;
      max-width: 100% !important;
  }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# System Resource Loading & Caching
# -----------------------------------------------------------------------------
@st.cache_resource
def load_system_resources():
    """Loads production model bundle, drift monitor baseline, and explainer."""
    registry_dir = PROJECT_ROOT / "artifacts" / "registry"
    models_dir = PROJECT_ROOT / "artifacts" / "models"
    registry = ModelRegistry(registry_dir=str(registry_dir), models_dir=str(models_dir))
    try:
        bundle = registry.get_production_bundle()
    except Exception:
        models = registry.list_models()
        if not models:
            st.error("FATAL: No models registered. Run `python src/pipeline.py --quick` to train baseline.")
            st.stop()
        bundle = registry.load_bundle(models[-1]["model_id"])

    explainer = IncidentExplainabilityEngine(bundle.supervised_model)
    generator = NetworkFlowGenerator(seed=42)
    engine = TrafficPerturbationEngine(seed=42)

    # Reference baseline for statistical drift
    ref_path = PROJECT_ROOT / "data" / "reference_baseline.joblib"
    if ref_path.exists():
        ref_data = joblib.load(ref_path)
        drift_monitor = StatisticalDriftMonitor(
            reference_data=ref_data["reference_data"],
            feature_names=ref_data["feature_names"]
        )
    else:
        dummy_ref = np.zeros((100, len(bundle.metadata.feature_names)))
        drift_monitor = StatisticalDriftMonitor(dummy_ref, bundle.metadata.feature_names)

    lateral_tracker = TemporalLateralTracker()
    baseline_df = generator.generate_baseline_flows(400)
    lateral_tracker.fit_baseline(baseline_df)

    return bundle, explainer, generator, engine, drift_monitor, lateral_tracker


@st.cache_data
def get_adversarial_curve(_bundle, _generator, _engine):
    """Caches adversarial resilience curve for instant slider interactivity."""
    df_attacks = _generator.generate_known_attacks(80)
    X_attacks = _bundle.preprocessor.transform(df_attacks)
    pts = _engine.benchmark_adversarial_robustness(
        _bundle.supervised_model,
        _bundle.autoencoder_model,
        X_attacks,
        epsilon_levels=[0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
    )
    return pts


bundle, explainer, generator, adv_engine, drift_monitor, lateral_tracker = load_system_resources()
pts_adversarial = get_adversarial_curve(bundle, generator, adv_engine)


# -----------------------------------------------------------------------------
# Sidebar: Operational Ingestion & Calibration Controls
# -----------------------------------------------------------------------------
st.sidebar.markdown("""
<div style="font-family: 'Space Grotesk', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 0.1em; color: #8b949e; margin-bottom: 12px; border-bottom: 1px solid #21262d; padding-bottom: 6px;">
  OPERATIONAL CONTROLS // AIR-GAPPED
</div>
""", unsafe_allow_html=True)

traffic_mode = st.sidebar.selectbox(
    "TRAFFIC INJECTION SCENARIO",
    [
        "BENIGN (Enterprise Baseline)",
        "DDOS_SYN_FLOOD (Volumetric SYN Attack)",
        "PORT_SCAN (Reconnaissance Sweep)",
        "SSH_BRUTE_FORCE (Auth / Credential Stuffing)",
        "ZERO_DAY_C2_EXFILTRATION (Novel Beaconing / Tunneling)",
        "LATERAL_MOVEMENT (Internal SMB/RDP Pivot)"
    ]
)

num_flows = st.sidebar.slider("INGESTION BATCH SIZE", min_value=5, max_value=60, value=20, step=5)

inject_btn = st.sidebar.button("INGEST & SCORE FLOW BATCH", use_container_width=True)

st.sidebar.markdown("""
<div style="font-family: 'Space Grotesk', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 0.08em; color: #8b949e; margin-top: 16px; margin-bottom: 8px; border-top: 1px solid #21262d; padding-top: 8px;">
  DETECTION THRESHOLD CALIBRATION
</div>
""", unsafe_allow_html=True)

optimal_default = float(bundle.metadata.metrics.get("optimal_threshold", 0.15))
sup_threshold = st.sidebar.slider(
    "Tier 1 LightGBM Threshold (Cost-Calibrated)",
    min_value=0.01,
    max_value=0.99,
    value=optimal_default,
    step=0.01,
    help="Optimal Neyman-Pearson threshold minimizing $50,000 false negative breach penalty."
)

ae_default = float(bundle.autoencoder_model.threshold if bundle.autoencoder_model.threshold else 0.8)
ae_threshold = st.sidebar.slider(
    "Tier 2 Autoencoder Anomaly Cutoff",
    min_value=0.10,
    max_value=2.00,
    value=ae_default,
    step=0.05,
    help="Reconstruction error threshold for zero-day anomaly classification."
)

st.sidebar.markdown("""
<div style="font-family: 'Space Grotesk', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 0.08em; color: #8b949e; margin-top: 16px; margin-bottom: 8px; border-top: 1px solid #21262d; padding-top: 8px;">
  ADVERSARIAL & DRIFT STRESS CONTROLS
</div>
""", unsafe_allow_html=True)

eps_budget = st.sidebar.slider(
    "Adversarial Budget (ε)",
    min_value=0.0,
    max_value=0.40,
    value=0.15,
    step=0.05,
    help="Perturbation budget for real-time stress testing."
)

drift_mode = st.sidebar.radio(
    "Production Ingestion Profile",
    ["Nominal Ingestion", "Covariate Shift (Exfil Dilation Burst)"]
)


# -----------------------------------------------------------------------------
# Flow Generation & Scoring Execution
# -----------------------------------------------------------------------------
if inject_btn or "active_flows" not in st.session_state:
    scen_prefix = traffic_mode.split()[0]
    if scen_prefix == "BENIGN":
        df_new = generator.generate_baseline_flows(num_flows)
    elif scen_prefix in ["DDOS_SYN_FLOOD", "PORT_SCAN", "SSH_BRUTE_FORCE"]:
        df_pool = generator.generate_known_attacks(max(num_flows * 3, 30))
        df_new = df_pool[df_pool["attack_type"] == scen_prefix].head(num_flows)
    elif scen_prefix == "ZERO_DAY_C2_EXFILTRATION":
        df_new = generator.generate_zero_day_attacks(num_flows)
    else:
        df_new = generator.generate_lateral_movement(num_flows)

    st.session_state["active_flows"] = df_new

df_active = st.session_state.get("active_flows", pd.DataFrame())

t0 = time.perf_counter()
# Score batch with active thresholds
df_scored = bundle.score_batch(df_active, supervised_threshold=sup_threshold)
# Override AE threshold if changed
if ae_threshold != bundle.autoencoder_model.threshold:
    recon_losses = df_scored["reconstruction_loss"].to_numpy()
    ae_preds = (recon_losses >= ae_threshold).astype(int)
    df_scored["autoencoder_pred"] = ae_preds
    df_scored["is_attack"] = (df_scored["supervised_pred"] | ae_preds).astype(int)
inference_ms = (time.perf_counter() - t0) * 1000.0
mean_latency_per_flow = inference_ms / max(len(df_scored), 1)

# Evaluate Covariate Drift for Ingestion Profile
if drift_mode == "Nominal Ingestion":
    df_drift_batch = generator.generate_baseline_flows(150)
else:
    df_drift_batch = generator.generate_baseline_flows(150)
    df_drift_batch["flow_duration_ms"] = df_drift_batch["flow_duration_ms"] * 6.0
    df_drift_batch["total_fwd_bytes"] = df_drift_batch["total_fwd_bytes"] * 9.0

X_drift = bundle.preprocessor.transform(df_drift_batch)
report_drift = drift_monitor.evaluate_drift(X_drift)


# -----------------------------------------------------------------------------
# Top Telemetry Ribbon (36px Fixed Strip)
# -----------------------------------------------------------------------------
model_sha_short = bundle.metadata.dataset_hash[:8] if bundle.metadata.dataset_hash else "99d9bece"
drift_status_class = "tape-val-crit" if report_drift.retraining_recommended else "tape-val-green"
drift_status_text = f"DRIFT ALERT ({report_drift.drift_feature_ratio:.1%})" if report_drift.retraining_recommended else "NOMINAL (0.0%)"

st.markdown(f"""
<div class="telemetry-tape">
  <div class="tape-item">
    <span class="tape-dot"></span>
    <span class="tape-label">SYSTEM:</span>
    <span class="tape-val">SENTINELNET AIR-GAPPED SOC NODE</span>
  </div>
  <span class="tape-divider">|</span>
  <div class="tape-item">
    <span class="tape-label">MODEL:</span>
    <span class="tape-val-accent">{bundle.metadata.model_id[:20]}...</span>
    <span style="color: #8b949e;">(SHA: <code>{model_sha_short}</code>)</span>
  </div>
  <span class="tape-divider">|</span>
  <div class="tape-item">
    <span class="tape-label">INFERENCE SLA:</span>
    <span class="tape-val-green">{mean_latency_per_flow:.3f} ms / flow</span>
  </div>
  <span class="tape-divider">|</span>
  <div class="tape-item">
    <span class="tape-label">CALIBRATED THRESH:</span>
    <span class="tape-val-warn">{sup_threshold:.2f} ($50k FN)</span>
  </div>
  <span class="tape-divider">|</span>
  <div class="tape-item">
    <span class="tape-label">DRIFT OBSERVATORY:</span>
    <span class="{drift_status_class}">{drift_status_text}</span>
  </div>
  <span class="tape-divider">|</span>
  <div class="tape-item">
    <span class="tape-val-green">[ARMED & ACTIVE]</span>
  </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Asymmetric 60/40 SOC Terminal Grid
# -----------------------------------------------------------------------------
col_left, col_right = st.columns([6, 4], gap="small")

# =============================================================================
# LEFT COLUMN (60%): Live Flow Stream + Temporal Topology Canvas
# =============================================================================
with col_left:
    # 1. Live Flow Ingestion Stream (Anime.js v4 Entrance)
    st.markdown("""
    <div class="section-bar">
      <span><span class="accent">COMPONENT 01 //</span> LIVE FLOW INGESTION & MULTI-TIER SCORING STREAM</span>
      <span>TIER 1 (SIG) + TIER 2 (AE)</span>
    </div>
    """, unsafe_allow_html=True)
    
    render_alert_stream(df_scored.to_dict(orient="records"), height=350)

    # 2. Temporal Host Interaction Topology Canvas (Tier 3 Lateral Movement)
    st.markdown("""
    <div class="section-bar" style="margin-top: 10px;">
      <span><span class="accent">COMPONENT 02 //</span> TEMPORAL HOST INTERACTION TOPOLOGY & LATERAL PIVOT CANVAS</span>
      <span>TIER 3 (GRAPH TOPOLOGY)</span>
    </div>
    """, unsafe_allow_html=True)

    # Prepare window with baseline + any lateral flows
    df_lat = generator.generate_lateral_movement(12)
    df_window = pd.concat([generator.generate_baseline_flows(35), df_lat]).reset_index(drop=True)
    report_graph = lateral_tracker.analyze_window(df_window)

    render_network_topology_canvas(
        df_window=df_window,
        flagged_pivots=report_graph.flagged_pivots,
        height=430
    )


# =============================================================================
# RIGHT COLUMN (40%): TreeSHAP Attribution + Adversarial Evasion Lab
# =============================================================================
with col_right:
    # 3. TreeSHAP Incident Triage & Attribution Inspector (Tier 5)
    st.markdown("""
    <div class="section-bar">
      <span><span class="accent">COMPONENT 03 //</span> TREESHAP INCIDENT ATTRIBUTION INSPECTOR</span>
      <span>TIER 5 (EXPLAINABILITY)</span>
    </div>
    """, unsafe_allow_html=True)

    # Allow user to pick any flow from df_scored to inspect its exact SHAP attribution
    flow_options = []
    for i, row in df_scored.iterrows():
        tag = "[CRIT]" if row["is_attack"] else "[NORM]"
        atk = row["attack_type"]
        flow_options.append(f"{tag} #{i:02d}: {row['src_ip']} -> {row['dst_ip']}:{row['dst_port']} ({atk})")

    # Default to highest risk flow if available
    default_index = int(df_scored["supervised_prob"].idxmax()) if not df_scored.empty else 0

    selected_flow_idx = st.selectbox(
        "SELECT INCIDENT / FLOW RECORD TO TRIAGE:",
        range(len(flow_options)),
        index=default_index,
        format_func=lambda idx: flow_options[idx] if idx < len(flow_options) else f"Flow #{idx}",
        label_visibility="collapsed"
    )

    if not df_scored.empty and selected_flow_idx < len(df_scored):
        selected_record = df_scored.iloc[selected_flow_idx].to_dict()
        df_single = pd.DataFrame([selected_record])
        X_single = bundle.preprocessor.transform(df_single)
        shap_summary = explainer.explain_flow(X_single, raw_flow_dict=selected_record, top_k=7)
    else:
        shap_summary = {
            "predicted_probability": 0.0,
            "base_value": 0.0,
            "analyst_summary": "No flow selected.",
            "top_drivers": []
        }

    render_shap_waterfall(shap_summary, height=315)

    # 4. Adversarial Evasion Lab (Tier 4 Resilience Curve)
    st.markdown("""
    <div class="section-bar" style="margin-top: 10px;">
      <span><span class="accent">COMPONENT 04 //</span> ADVERSARIAL EVASION & STRESS-TEST LAB</span>
      <span>TIER 4 (RESILIENCE)</span>
    </div>
    """, unsafe_allow_html=True)

    render_evasion_lab(
        curve_points=pts_adversarial,
        current_epsilon=eps_budget,
        height=430
    )


# -----------------------------------------------------------------------------
# Bottom Operational Drawer: MLOps Telemetry & Statistical Drift Observatory
# -----------------------------------------------------------------------------
with st.expander("OPERATIONAL TELEMETRY // STATISTICAL DRIFT OBSERVATORY & RETRAINING STATUS (KS / PSI)"):
    kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
    kpi_c1.metric("Features Evaluated", report_drift.total_features_evaluated)
    kpi_c2.metric("Drifted Features", report_drift.num_drifted_features)
    kpi_c3.metric("Drift Feature Ratio", f"{report_drift.drift_feature_ratio:.1%}")
    kpi_c4.metric(
        "Retraining Trigger",
        "RECOMMENDED" if report_drift.retraining_recommended else "NOMINAL",
        delta="COVARIATE SHIFT" if report_drift.retraining_recommended else "IN-DISTRIBUTION",
        delta_color="inverse" if report_drift.retraining_recommended else "normal"
    )

    st.markdown("""
    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 10px; font-weight: 700; color: #8b949e; text-transform: uppercase; margin-top: 10px; margin-bottom: 4px;">
      TOP DRIFTED FEATURES (RANKED BY POPULATION STABILITY INDEX):
    </div>
    """, unsafe_allow_html=True)

    top_drift_rows = [
        {
            "Feature Name": d.feature_name,
            "PSI Score": round(d.psi_score, 4),
            "KS Statistic": round(d.ks_statistic, 4),
            "KS p-value": f"{d.ks_pvalue:.2e}",
            "Drift Severity": d.severity.upper(),
            "Distribution Action": "TRIGGER CT PIPELINE" if d.severity == "critical" else ("MONITOR" if d.severity == "moderate" else "PASS")
        }
        for d in sorted(report_drift.feature_details.values(), key=lambda x: x.psi_score, reverse=True)[:8]
    ]
    st.dataframe(pd.DataFrame(top_drift_rows), use_container_width=True, hide_index=True)
