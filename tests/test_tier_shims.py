"""Tests verifying that all Tier 0 through Tier 5 package shims export valid classes."""

import pytest


def test_tier0_baseline_exports():
    from src.tier0_baseline import Tier0HeuristicDetector, run_tier0_benchmark
    from src.tier0_baseline.baseline_rules import Tier0HeuristicDetector as DirectDetector

    assert Tier0HeuristicDetector is DirectDetector
    detector = Tier0HeuristicDetector()
    assert hasattr(detector, "predict_record")
    assert hasattr(detector, "predict_dataframe")


def test_tier1_supervised_exports():
    from src.tier1_supervised import ClassifierMetrics, SupervisedFlowClassifier
    from src.tier1_supervised.supervised_classifier import SupervisedFlowClassifier as ShimClf
    from src.models.supervised_classifier import SupervisedFlowClassifier as DirectClf

    assert SupervisedFlowClassifier is DirectClf
    assert ShimClf is DirectClf


def test_tier2_anomaly_exports():
    from src.tier2_anomaly import AnomalyAutoencoder, AutoencoderMetrics, AutoencoderNet
    from src.tier2_anomaly.anomaly_autoencoder import AnomalyAutoencoder as ShimAE
    from src.models.anomaly_autoencoder import AnomalyAutoencoder as DirectAE

    assert AnomalyAutoencoder is DirectAE
    assert ShimAE is DirectAE


def test_tier3_graph_exports():
    from src.tier3_graph import GraphAnomalyReport, HostThreatScore, TemporalLateralTracker
    from src.tier3_graph.lateral_tracker import TemporalLateralTracker as ShimTracker
    from src.graph.lateral_tracker import TemporalLateralTracker as DirectTracker

    assert TemporalLateralTracker is DirectTracker
    assert ShimTracker is DirectTracker


def test_tier4_adversarial_exports():
    from src.tier4_adversarial import RobustnessCurvePoint, TrafficPerturbationEngine
    from src.tier4_adversarial.perturbation_engine import TrafficPerturbationEngine as ShimEngine
    from src.adversarial.perturbation_engine import TrafficPerturbationEngine as DirectEngine

    assert TrafficPerturbationEngine is DirectEngine
    assert ShimEngine is DirectEngine


def test_tier5_calibration_exports():
    from src.tier5_calibration import (
        CostCalibrationResult,
        DataDriftReport,
        FeatureDriftDetail,
        FlowFeatureExplanation,
        IncidentExplainabilityEngine,
        IncidentTriageSummary,
        SOCCostCalibrator,
        StatisticalDriftMonitor,
    )
    from src.tier5_calibration.cost_calibrator import SOCCostCalibrator as ShimCalibrator
    from src.tier5_calibration.drift_monitor import StatisticalDriftMonitor as ShimMonitor
    from src.tier5_calibration.explainability import IncidentExplainabilityEngine as ShimExplainer
    from src.ops.cost_calibrator import SOCCostCalibrator as DirectCalibrator
    from src.ops.drift_monitor import StatisticalDriftMonitor as DirectMonitor
    from src.ops.explainability import IncidentExplainabilityEngine as DirectExplainer

    assert SOCCostCalibrator is DirectCalibrator
    assert ShimCalibrator is DirectCalibrator
    assert StatisticalDriftMonitor is DirectMonitor
    assert ShimMonitor is DirectMonitor
    assert IncidentExplainabilityEngine is DirectExplainer
    assert ShimExplainer is DirectExplainer


def test_serving_and_engine_exports():
    from src.serving import app
    from src.api.app import app as direct_app
    from src.engine import InferenceBundle, TrafficPerturbationEngine

    assert app is direct_app
    assert InferenceBundle is not None
    assert TrafficPerturbationEngine is not None
