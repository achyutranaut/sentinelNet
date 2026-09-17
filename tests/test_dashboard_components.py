"""Unit tests for Tier 6 SOC Command Center UI components and Anime.js v4 integration."""

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.dashboard.components.alert_stream import render_alert_stream
from src.dashboard.components.evasion_lab import render_evasion_lab
from src.dashboard.components.network_topology import render_network_topology_canvas
from src.dashboard.components.shap_waterfall import render_shap_waterfall
from src.graph.lateral_tracker import HostThreatScore
from src.ops.explainability import FlowFeatureExplanation, IncidentTriageSummary


@patch("streamlit.components.v1.html")
def test_render_alert_stream_html_and_anime_v4(mock_html):
    """Verifies that alert stream generates dense terminal table and anime.v4 animate call."""
    mock_flows = [
        {
            "timestamp": 1234.56,
            "src_ip": "192.168.1.50",
            "dst_ip": "10.0.1.10",
            "dst_port": 443,
            "attack_type": "DDOS_SYN_FLOOD",
            "supervised_prob": 0.88,
            "reconstruction_loss": 0.45,
            "reconstruction_threshold": 0.31,
            "is_attack": 1
        },
        {
            "timestamp": 1234.57,
            "src_ip": "10.0.1.20",
            "dst_ip": "10.0.1.2",
            "dst_port": 80,
            "attack_type": "BENIGN",
            "supervised_prob": 0.02,
            "reconstruction_loss": 0.05,
            "reconstruction_threshold": 0.31,
            "is_attack": 0
        }
    ]

    render_alert_stream(mock_flows, height=300)
    mock_html.assert_called_once()
    html_arg = mock_html.call_args[0][0]

    assert "LIVE FLOW INGESTION & TIER SCORING STREAM" in html_arg
    assert "IBM Plex Mono" in html_arg
    assert "window.anime.animate" in html_arg
    assert "192.168.1.50" in html_arg
    assert "CRITICAL" in html_arg


@patch("streamlit.components.v1.html")
def test_render_network_topology_canvas_with_dataclasses(mock_html):
    """Verifies SVG topology canvas handles HostThreatScore dataclasses and anime.v4 stagger."""
    df_window = pd.DataFrame([
        {"src_ip": "192.168.1.10", "dst_ip": "10.0.1.5"},
        {"src_ip": "10.0.1.5", "dst_ip": "10.0.1.6"},
        {"src_ip": "10.0.1.5", "dst_ip": "10.0.1.7"}
    ])
    pivots = [
        HostThreatScore(
            host_ip="10.0.1.5",
            out_degree=2,
            degree_zscore=3.2,
            jaccard_novelty=0.95,
            pagerank=0.25,
            pagerank_delta=0.15,
            is_suspicious_pivot=True,
            reasons=["High out-degree burst", "High novel edge ratio"]
        )
    ]

    render_network_topology_canvas(df_window, pivots, height=400)
    mock_html.assert_called_once()
    html_arg = mock_html.call_args[0][0]

    assert "TEMPORAL HOST INTERACTION TOPOLOGY" in html_arg
    assert "10.0.1.5" in html_arg
    assert "stagger(45" in html_arg
    assert "edge-threat" in html_arg


@patch("streamlit.components.v1.html")
def test_render_evasion_lab_timeline_sync(mock_html):
    """Verifies adversarial evasion lab generates synchronized anime.v4 timeline."""
    points = [
        {"epsilon": 0.0, "supervised_recall": 1.0, "autoencoder_recall": 0.95, "combined_recall": 1.0},
        {"epsilon": 0.15, "supervised_recall": 0.45, "autoencoder_recall": 0.88, "combined_recall": 0.90},
        {"epsilon": 0.40, "supervised_recall": 0.10, "autoencoder_recall": 0.82, "combined_recall": 0.84}
    ]

    render_evasion_lab(points, current_epsilon=0.15, height=340)
    mock_html.assert_called_once()
    html_arg = mock_html.call_args[0][0]

    assert "ADVERSARIAL EVASION & STRESS-TEST LAB" in html_arg
    assert "createTimeline" in html_arg
    assert "budget-cursor-line" in html_arg


@patch("streamlit.components.v1.html")
def test_render_shap_waterfall_inspector(mock_html):
    """Verifies TreeSHAP waterfall inspector handles IncidentTriageSummary and anime.v4 reveals."""
    summary = IncidentTriageSummary(
        predicted_probability=0.942,
        base_value=-2.85,
        top_drivers=[
            FlowFeatureExplanation(
                feature_name="dst_port",
                feature_value=4444.0,
                shap_value=0.48,
                impact_direction="INCREASES_ATTACK_RISK"
            ),
            FlowFeatureExplanation(
                feature_name="flow_duration_ms",
                feature_value=12.5,
                shap_value=-0.12,
                impact_direction="REDUCES_ATTACK_RISK"
            )
        ],
        analyst_summary="High confidence alert triggered by destination port."
    )

    render_shap_waterfall(summary, height=320)
    mock_html.assert_called_once()
    html_arg = mock_html.call_args[0][0]

    assert "TREESHAP INCIDENT ATTRIBUTION INSPECTOR" in html_arg
    assert "dst_port" in html_arg
    assert "flow_duration_ms" in html_arg
    assert "stagger" in html_arg
    assert "shap-bar-fill" in html_arg
