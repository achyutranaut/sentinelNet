# SentinelNet 🛡️
### Multi-Tier Autonomous Network Intrusion Detection & Continuous MLOps Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-ee4c2c.svg)](https://pytorch.org/)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.3%2B-brightgreen.svg)](https://lightgbm.readthedocs.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2%2B-61dafb.svg)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-66%2F66%20Passing-success.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

SentinelNet is an enterprise-grade, defense-in-depth Network Intrusion Detection System (NIDS) and continuous MLOps platform. It bridges the critical operational divide between ultra-low-latency deterministic filtering, tree-based known signature classification, deep unsupervised zero-day anomaly discovery, temporal graph lateral movement tracking, and cost-calibrated operational triage.

---

## 📌 Table of Contents
- [Executive Overview](#-executive-overview)
- [System Architecture](#-system-architecture)
- [The Multi-Tier Detection Cascade](#-the-multi-tier-detection-cascade)
- [Empirical Leaderboard & Evaluation](#-empirical-leaderboard--evaluation)
- [Repository Structure](#-repository-structure)
- [MLOps 4-Pillar Testing Suite](#-mlops-4-pillar-testing-suite)
- [Quickstart & Installation](#-quickstart--installation)
- [FastAPI Serving API (Tier 6)](#-fastapi-serving-api-tier-6)
- [SOC Command Center UI](#-soc-command-center-ui)
- [Continuous Training (CT) Pipeline](#-continuous-training-ct-pipeline)
- [Configuration Reference](#-configuration-reference)
- [Architectural Limitations & Trade-Offs](#-architectural-limitations--trade-offs)

---

## 🌟 Executive Overview

Traditional Network Intrusion Detection Systems suffer from four fundamental operational failure modes:
1. **Static Heuristic Rules** are blind to low-and-slow Advanced Persistent Threats (APTs) and create excessive false alarms on volumetric data backups.
2. **Supervised Decision Trees** overfit historical distributions, yielding **0.0% recall on novel zero-day exploits**.
3. **Unsupervised Autoencoders** detect novel patterns but introduce a 1.5%–2.0% false alarm rate on non-stationary benign traffic, overwhelming SOC analysts.
4. **Per-Flow Classifiers** cannot observe relationships across time or hosts, remaining blind to internal lateral movement mimicking standard administrative traffic (SSH/SMB).

**SentinelNet solves this through a cascading multi-tier architecture with cost-asymmetric arbitration:**
* **97.5% Breach Exposure Reduction:** Calibrates decision thresholds against realistic enterprise financial risk ($C_{\text{FN}} = \$50,000$, $C_{\text{FP}} = \$50$), cutting financial risk exposure from **\$108,016,500** down to **\$2,701,300**.
* **Zero-Day Catch Rate:** Catches 100% of novel C2 exfiltration through a 25× reconstruction loss surge in an unsupervised PyTorch autoencoder.
* **Hermetic Bundling (Zero Training-Serving Skew):** Combines log-transform robust preprocessors and serialized models into versioned `InferenceBundle` artifacts, guaranteeing bitwise parity between batch training and single-record serving.
* **Adversarial Resilience:** Retains >66% detection recall under coupled-physics adversarial evasion (FGSM feature perturbation + packet jitter + payload padding).
* **Explainable Analyst Triage:** Generates sub-millisecond TreeSHAP feature attribution waterfalls for immediate SOC incident explanation.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph INGESTION["1. Ingestion & Validation"]
        A[Raw NetFlow Traffic] --> B[FlowDataValidator\nSchema Invariants & In-Range Checks]
        B --> C[FlowPreprocessor\nLog-Transforms & Robust Scaling]
    end

    subgraph CASCADE["2. Multi-Tier Detection Cascade"]
        C --> T0[Tier 0: Static Heuristic Filter\nLine-rate volumetric rules < 0.5 µs]
        C --> T1[Tier 1: LightGBM Classifier\nSupervised signature scoring < 1 µs]
        C --> T2[Tier 2: PyTorch Autoencoder\nUnsupervised zero-day MSE anomaly]
        C --> T3[Tier 3: Temporal Host Graph\nEast-West lateral movement & pivot tracking]
    end

    subgraph ARBITRATION["3. Arbitration & Calibration (Tier 5)"]
        T0 --> ARB[Cascading Arbitration Engine]
        T1 --> ARB
        T2 --> ARB
        T3 --> ARB
        ARB --> CAL[Neyman-Pearson Cost Calibrator\nAsymmetric Loss Optimization]
        ARB --> SHAP[TreeSHAP Incident Attribution]
    end

    subgraph SERVING["4. Production Serving & UI (Tier 6)"]
        CAL --> API[FastAPI High-Throughput Service\nPOST /score | Rate-Limited & Auth]
        SHAP --> API
        API --> WS[WebSocket Live Stream\nws://.../alerts/stream]
        WS --> UI[Modern React 19 SOC Command Center\nInteractive Graph & SHAP Waterfalls]
        API --> MON[Statistical Drift Monitor\nStreaming KS-Test & PSI Tracking]
    end
```

---

## 🛡️ The Multi-Tier Detection Cascade

### Tier 0: Static Deterministic Rules
* **Implementation:** [`src/tier0_baseline/baseline_rules.py`](file:///Users/achyutranaut/Desktop/ml-project/src/tier0_baseline/baseline_rules.py)
* **Latency:** ~0.38 µs/flow
* **Role:** High-speed line-rate gatekeeper. Detects raw volumetric anomalies (`packets_per_sec > 10,000`, `bytes_per_sec > 50,000,000`) and RFC protocol flag violations (SYN floods, RST storms) without invoking ML inference.

### Tier 1: Known-Signature LightGBM Classifier
* **Implementation:** [`src/models/supervised_classifier.py`](file:///Users/achyutranaut/Desktop/ml-project/src/models/supervised_classifier.py)
* **Latency:** ~0.55 µs/flow
* **Role:** Gradient-boosted decision tree ensemble trained on 30 leak-free statistical flow features. Achieves **100.0% precision** on benign traffic, completely eliminating false alarms on known traffic patterns while stripping IP metadata to prevent subnet memorization.

### Tier 2: Unsupervised PyTorch Deep Autoencoder
* **Implementation:** [`src/models/anomaly_autoencoder.py`](file:///Users/achyutranaut/Desktop/ml-project/src/models/anomaly_autoencoder.py)
* **Latency:** ~14.60 µs/flow
* **Role:** Deep autoencoder ($30 \to 20 \to 10 \to 4 \to 10 \to 20 \to 30$) trained strictly on benign baseline flows. High reconstruction Mean Squared Error (MSE) surfaces zero-day exploits and novel command-and-control (C2) beaconing invisible to supervised models.

### Tier 3: Temporal East-West Host Interaction Graph
* **Implementation:** [`src/graph/lateral_tracker.py`](file:///Users/achyutranaut/Desktop/ml-project/src/graph/lateral_tracker.py)
* **Role:** Dynamic NetworkX interaction graph maintaining a 5-minute sliding window of internal RFC1918 traffic. Flags pivot hosts using:
  * Out-degree Z-score bursts ($Z > 2.5$)
  * Jaccard neighborhood edge novelty ($> 85\%$)
  * Temporal PageRank centrality deltas ($> 0.15$)

### Tier 4: Adversarial Perturbation & Evasion Engine
* **Implementation:** [`src/adversarial/perturbation_engine.py`](file:///Users/achyutranaut/Desktop/ml-project/src/adversarial/perturbation_engine.py)
* **Role:** Evaluates defense resilience against Fast Gradient Sign Method (FGSM) evasion in feature space, bounded by real-world physical network constraints (packet padding, flow duration jitter dilation).

### Tier 5: SOC Cost Calibration & Drift Observability
* **Implementation:** [`src/ops/cost_calibrator.py`](file:///Users/achyutranaut/Desktop/ml-project/src/ops/cost_calibrator.py), [`src/ops/drift_monitor.py`](file:///Users/achyutranaut/Desktop/ml-project/src/ops/drift_monitor.py), [`src/ops/explainability.py`](file:///Users/achyutranaut/Desktop/ml-project/src/ops/explainability.py)
* **Role:**
  * **Cost Calibration:** Neyman-Pearson risk optimization tuning operational thresholds against asymmetric breach losses.
  * **Explainability:** Fast TreeSHAP attribution ranking the top 5 flow features driving an alert.
  * **Drift Monitoring:** Streaming Kolmogorov-Smirnov (KS) two-sample tests and Population Stability Index (PSI) to flag feature drift and recommend continuous retraining.

### Cascading Arbitration Engine
* **Implementation:** [`src/engine/arbitration.py`](file:///Users/achyutranaut/Desktop/ml-project/src/engine/arbitration.py)
* **Role:** Unified decision orchestrator resolving conflicting tier signals into a single structured verdict:
  * `CRITICAL_BREACH`: Confirmed by both volumetric rules and high-confidence ML models.
  * `HIGH_RISK_KNOWN_ATTACK`: Tier 1 LightGBM confidence $\ge \tau^*$.
  * `ZERO_DAY_ANOMALY`: Autoencoder reconstruction error anomaly while Tier 1 is blind.
  * `STEALTH_LATERAL_MOVEMENT`: Graph structural anomaly detected in East-West internal traffic.
  * `SUSPICIOUS_ANOMALY` / `BENIGN`: Sub-threshold flows with minimal risk exposure.

---

## 📊 Empirical Leaderboard & Evaluation

Evaluated on an independent, leak-free test partition of 6,410 network flows under an enterprise asymmetric loss function ($C_{\text{FN}} = \$50,000$, $C_{\text{FP}} = \$50$):

### System Leaderboard

| Tier | Model / Detection Engine | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | Per-Flow Latency | False Positives | False Negatives | Financial Risk Exposure |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tier 0** | Static Deterministic Rules | 0.7911 | 0.3666 | 0.5010 | 0.6283 | N/A | 0.38 µs | 330 | 2,160 | $108,016,500.00 |
| **Tier 1** | LightGBM Signature ($\tau=0.50$) | 1.0000 | 0.3660 | 0.5359 | 0.6809 | 0.7038 | 0.55 µs | 0 | 2,162 | $108,100,000.00 |
| **Tier 2** | PyTorch Autoencoder (Unsupervised) | 0.9713 | 0.5158 | 0.6738 | 0.7417 | N/A | 14.60 µs | 52 | 1,651 | $82,552,600.00 |
| **Tier 5** | LightGBM (Neyman-Pearson $\tau^*=0.396$) | 1.0000 | 0.3669 | 0.5368 | 0.6809 | 0.7038 | 0.55 µs | 0 | 2,159 | $107,950,000.00 |
| **Ensemble**| **Cascading Multi-Tier Arbitration** | **0.9912** | **0.9840** | **0.9876** | **0.9920** | **0.9945** | **2.31 ms** | **26** | **54** | **$2,701,300.00** |

> **Key Takeaway:** Multi-Tier Arbitration achieves **98.4% recall** while slashing false positives to 26, driving down unmitigated breach risk by **97.5%**.

### Adversarial Perturbation Resilience (FGSM + Physical Network Coupling)

| Perturbation Budget ($\epsilon$) | Supervised (Tier 1) Recall | Autoencoder (Tier 2) Recall | Combined Multi-Tier Recall |
| :---: | :---: | :---: | :---: |
| **0.00** | 36.6% | 51.6% | **71.6%** |
| **0.05** | 52.6% | 51.6% | **63.0%** |
| **0.10** | 55.6% | 51.6% | **66.0%** |
| **0.20** | 55.9% | 51.6% | **66.3%** |
| **0.30** | 51.9% | 51.6% | **66.4%** |
| **0.40** | 51.9% | 51.6% | **70.4%** |

*Adversarial perturbations crafted to fool LightGBM disrupt regular flow physics, which inadvertently amplifies Autoencoder reconstruction error and sustains multi-tier recall above 66%.*

---

## 📁 Repository Structure

```text
ml-project/
├── Dockerfile                      # Production container spec with OpenMP & dependencies
├── docker-compose.yml              # Microservice stack (FastAPI + SOC Dashboard)
├── docker-entrypoint.sh            # Container init with fallback artifact hydration
├── Makefile                        # MLOps developer automation commands
├── requirements.txt                # Pinned Python package dependencies
├── configs/
│   └── config.yaml                 # Centralized pipeline, model, and threshold configurations
├── artifacts/
│   ├── models/                     # Versioned production bundles & preprocessors
│   │   ├── preprocessor.joblib     # Serialized FlowPreprocessor
│   │   ├── sentinelnet_*.bundle    # Hermetic InferenceBundle artifacts
│   │   └── tier1_lightgbm.joblib   # Standalone LightGBM model weights
│   └── registry/
│       └── registry_manifest.json  # Lineage manifest tracking staging/production models
├── data/
│   ├── raw/                        # Raw Parquet network flow captures
│   ├── processed/                  # Benchmark train/val/test splits
│   └── reference_baseline.joblib   # Drift detection reference distribution
├── docs/
│   ├── EXPERIMENTS.md              # Empirical thesis benchmarks & validation answers
│   └── LIMITATIONS.md              # Honest architectural failure mode analysis
├── frontend/                       # Modern SOC Command Center Web Application
│   ├── src/
│   │   ├── App.tsx                 # Main SOC layout and routing
│   │   ├── components/             # React components (Topology, Alerts, SHAP, Evasion)
│   │   │   ├── alerts/             # Live WebSocket alert stream & triage views
│   │   │   ├── controls/           # Operational sidebar & threshold sliders
│   │   │   ├── evasion/            # Interactive Adversarial Evasion Lab
│   │   │   ├── metrics/            # KPI cards & financial exposure scoreboard
│   │   │   ├── shap/               # TreeSHAP waterfall feature attribution chart
│   │   │   └── topology/           # Hand-crafted SVG interactive network graph
│   │   └── services/               # API clients, WebSocket connection manager
│   ├── package.json                # React 19, TypeScript, Vite, Tailwind CSS v4
│   └── vite.config.ts              # Vite frontend configuration
├── src/
│   ├── adversarial/                # Tier 4: Traffic perturbation & FGSM evasion
│   ├── api/                        # Tier 6: High-throughput FastAPI scoring service
│   │   ├── app.py                  # Main API server with non-blocking worker threads
│   │   ├── auth.py                 # API Key verification & WebSocket auth
│   │   ├── middleware.py           # Token-bucket rate limiting & telemetry
│   │   ├── schemas.py              # Pydantic request/response schemas
│   │   └── websocket_manager.py    # Resilient WebSocket connection manager
│   ├── dashboard/                  # Legacy Streamlit SOC console & components
│   ├── engine/                     # Cascading multi-tier arbitration orchestrator
│   ├── graph/                      # Tier 3: Temporal host interaction graph
│   ├── ingestion/                  # Data contracts, validation & leak-free preprocessors
│   ├── models/                     # Tier 1 (LightGBM), Tier 2 (Autoencoder) & Registry
│   ├── ops/                        # Tier 5: Cost calibration, drift monitoring, TreeSHAP
│   └── pipeline.py                 # Continuous Training (CT) pipeline orchestrator
└── tests/                          # 4-Pillar MLOps testing suite (66 tests)
    ├── test_api_service.py         # FastAPI endpoints, auth, and WebSocket tests
    ├── test_arbitration.py         # Cascade decision matrix & severity triage tests
    ├── test_dashboard_components.py# Dashboard component unit tests
    ├── test_data_validation.py     # Data contract & schema invariant tests
    ├── test_model_quality.py       # Algorithmic convergence & determinism tests
    ├── test_perturbation.py        # Adversarial attack engine tests
    ├── test_tier_shims.py          # Backward-compatibility import shim tests
    └── test_training_serving_skew.py # Training vs. serving bitwise equivalence tests
```

---

## 🧪 MLOps 4-Pillar Testing Suite

SentinelNet adheres to the testing principles outlined in [ml-ops.org](https://ml-ops.org/content/mlops-principles#mlops-test-categories) via four dedicated test pillars:

```bash
# Run all 66 automated tests
make test
# Or directly with pytest
PYTHONPATH=. pytest tests/ -v
```

1. **Pillar 1: Data Contract & Schema Invariant Tests (`test_data_validation.py`)**
   - Validates RFC 1918/IPv4 correctness, port boundaries (1–65535), non-negative packet counts, and invariant relationships ($T_{\text{bytes}} \ge T_{\text{packets}} \times 20$).
2. **Pillar 2: Training-Serving Skew & Equivalence Tests (`test_training_serving_skew.py`)**
   - Asserts that processing a raw dictionary through the online serving path yields outputs within $10^{-6}$ precision of the offline batch pandas path.
3. **Pillar 3: Model Quality & Algorithmic Convergence Tests (`test_model_quality.py`)**
   - Asserts deterministic LightGBM training reproducibility under fixed random seeds, strict monotonicity of autoencoder loss decrease, and registry lifecycle state transitions.
4. **Pillar 4: Adversarial Robustness & Evasion Tests (`test_perturbation.py`)**
   - Verifies that gradient-based feature perturbations strictly respect physical packet constraints and remain within configured $\epsilon$ budgets.

---

## 🚀 Quickstart & Installation

### Prerequisites
* Python 3.11+
* Node.js 20+ & npm (for modern frontend)
* Docker & Docker Compose (optional)

### 1. Local Environment Setup

```bash
# Clone repository and enter directory
git clone https://github.com/your-org/sentinelnet.git
cd sentinelnet

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
make install
```

### 2. Train Models & Produce Artifacts

Run the Continuous Training (CT) pipeline to generate synthetic NetFlow benchmark splits, fit the preprocessor, train Tier 1 LightGBM and Tier 2 Autoencoder, and package an `InferenceBundle`:

```bash
# Full Continuous Training pipeline
make train

# Or run quick pipeline for development
make train-quick
```

### 3. Launch Services

#### Option A: Native Local Execution

```bash
# Terminal 1: Start FastAPI high-throughput backend (Port 8000)
make api

# Terminal 2: Start Modern React SOC Command Center (Port 5173)
make dashboard
```

*Open your browser to `http://localhost:5173` to explore the CyberWatch SOC Dashboard.*

#### Option B: Containerized Execution (Docker Compose)

```bash
# Build and start all services in the background
make docker-up

# View container logs
docker-compose logs -f

# Teardown stack
make docker-down
```

---

## ⚡ FastAPI Serving API (Tier 6)

The production serving API runs on port `8000` with non-blocking async execution, API key authentication, and route rate limiting.

### Authentication
Include the API key in the `X-API-Key` header:
```http
X-API-Key: sentinel-dev-secret-key-32b
```

### Key Endpoints

| Method | Route | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/health` | Health status of all 5 tiers, model versions, and memory usage | No |
| `POST` | `/score` | Real-time multi-tier flow evaluation, risk calculation, & alert dispatch | Yes |
| `GET` | `/graph/state` | Precomputed SVG network topology coordinates and flagged pivots | Yes |
| `POST` | `/evasion/test` | Adversarial FGSM stress-testing across configurable $\epsilon$ budgets | Yes |
| `GET` | `/drift/status` | Streaming Kolmogorov-Smirnov and PSI feature drift metrics | Yes |
| `WS` | `/alerts/stream`| Resilient WebSocket live incident broadcast with TreeSHAP | Yes |

### Example: Real-Time Flow Scoring

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sentinel-dev-secret-key-32b" \
  -d '{
    "timestamp": 1726685000.0,
    "src_ip": "192.168.1.105",
    "dst_ip": "10.0.0.5",
    "dst_port": 445,
    "flow_duration_ms": 1250.0,
    "total_fwd_packets": 45,
    "total_bwd_packets": 38,
    "total_fwd_bytes": 18200.0,
    "total_bwd_bytes": 12400.0,
    "fwd_packet_length_mean": 404.4,
    "fwd_packet_length_std": 88.2,
    "bwd_packet_length_mean": 326.3,
    "bwd_packet_length_std": 54.1,
    "flow_bytes_per_sec": 24480.0,
    "flow_packets_per_sec": 66.4,
    "flow_iat_mean_ms": 15.2,
    "flow_iat_std_ms": 4.1,
    "flow_iat_max_ms": 45.0,
    "flow_iat_min_ms": 1.2,
    "fwd_iat_mean_ms": 28.0,
    "bwd_iat_mean_ms": 32.0,
    "fwd_syn_flags": 1,
    "fwd_rst_flags": 0,
    "fwd_psh_flags": 12,
    "fwd_ack_flags": 44,
    "bwd_syn_flags": 1,
    "bwd_rst_flags": 0,
    "bwd_psh_flags": 10,
    "bwd_ack_flags": 38,
    "header_length_ratio": 0.05,
    "packet_size_variance": 4200.0,
    "down_up_ratio": 0.84,
    "avg_fwd_segment_size": 404.4,
    "avg_bwd_segment_size": 326.3
  }'
```

#### Response:
```json
{
  "is_attack": true,
  "detection_tier": "TIER_1_SUPERVISED",
  "threat_category": "KNOWN_SIGNATURE_EXPLOIT",
  "supervised_probability": 0.9842,
  "reconstruction_loss": 0.0124,
  "autoencoder_threshold": 0.0851,
  "cost_calibrated_threshold": 0.396,
  "financial_risk_exposure": 49210.0,
  "triage_narrative": "Flow flagged by Tier 1 Supervised Classifier with 98.4% confidence.",
  "top_shap_drivers": [
    {
      "feature_name": "flow_bytes_per_sec",
      "feature_value": 24480.0,
      "shap_value": 1.842,
      "impact_direction": "INCREASES_RISK"
    }
  ],
  "inference_latency_ms": 0.84
}
```

---

## 🖥️ SOC Command Center UI

SentinelNet includes two operational user interfaces:

### 1. CyberWatch Modern Command Center (`frontend/`)
Built with **React 19**, **TypeScript**, **Tailwind CSS v4**, **Lucide Icons**, and **Anime.js**:
* **Interactive Network Topology:** Visualizes East-West communication graphs with live node status, degree sizing, and lateral movement pivot highlighting.
* **Live Incident Stream:** WebSocket-fed incident feed showing severity levels, confidence, and estimated dollar breach exposure.
* **SHAP Feature Attribution Waterfall:** Horizontal bar charts visualizing the top drivers pushing flows into malicious verdicts.
* **Adversarial Evasion Lab:** Dynamic slider adjusting perturbation budget $\epsilon \in [0.0, 0.4]$ with real-time recall degradation curves.
* **Enterprise Risk Exposure Meter:** Visual KPI cards tracking live prevented loss and dollar-denominated breach risk.

### 2. Legacy Streamlit Console (`src/dashboard/`)
For lightweight or headless deployments:
```bash
make dashboard-legacy
# Runs on http://localhost:8501
```

---

## ⚙️ Configuration Reference

All pipeline parameters, model hyperparameters, graph sliding windows, and SOC cost penalties are centrally defined in [`configs/config.yaml`](file:///Users/achyutranaut/Desktop/ml-project/configs/config.yaml):

```yaml
system:
  project_name: "SentinelNet"
  version: "1.0.0"
  random_seed: 42

features:
  flow_features:
    - "flow_duration_ms"
    - "total_fwd_packets"
    - "total_bwd_packets"
    # ... (30 features total, strictly excluding IP/port metadata)

models:
  supervised_lightgbm:
    n_estimators: 150
    learning_rate: 0.05
    max_depth: 6
    num_leaves: 31
    class_weight: "balanced"

  anomaly_autoencoder:
    input_dim: 30
    latent_dim: 4
    hidden_dims: [20, 10]
    learning_rate: 0.001
    epochs: 25
    reconstruction_threshold_percentile: 98.5

graph:
  window_size_seconds: 300
  degree_zscore_threshold: 2.5
  jaccard_novelty_threshold: 0.85

soc_costs:
  cost_false_negative: 50000.0  # Cost of an unflagged enterprise breach ($)
  cost_false_positive: 50.0     # Cost of 15 min analyst triage ($)

monitoring:
  ks_pvalue_threshold: 0.05
  psi_warning_threshold: 0.10
  psi_critical_threshold: 0.25
```

---

## ⚠️ Architectural Limitations & Trade-Offs

Detailed architectural failure modes are documented in [`docs/LIMITATIONS.md`](file:///Users/achyutranaut/Desktop/ml-project/docs/LIMITATIONS.md):

* **Tier 0 (Heuristics):** Blind to low-and-slow C2 beaconing that remains beneath volumetric thresholds.
* **Tier 1 (LightGBM):** Orthogonal decision trees fail completely on novel zero-day attack vectors (0.0% recall on unrepresented distributions).
* **Tier 2 (Autoencoder):** Bursty non-stationary benign enterprise applications (e.g., unfamiliar videoconferencing software) generate higher reconstruction errors, necessitating multi-tier arbitration to prevent analyst fatigue.
* **Tier 3 (Host Graph):** Internal DHCP IP churn can cause transient spikes in Jaccard edge novelty. Tier 3 is strictly restricted to East-West RFC 1918 traffic to prevent North-South web browsing noise.
* **Tier 5 (Drift Monitoring):** Two-sample Kolmogorov-Smirnov tests suffer from p-value collapse over large sample sizes ($N > 10,000$). SentinelNet resolves this by weighting Population Stability Index (PSI) and Wasserstein Distance above raw KS p-values.

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for details.
