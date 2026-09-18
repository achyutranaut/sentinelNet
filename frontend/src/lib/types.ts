export interface SHAPFeatureDriver {
  feature: string;
  value: number;
  shap_attribution: number;
  direction: string;
}

export interface SHAPExplanationPayload {
  predicted_probability: number;
  base_value: number;
  analyst_summary: string;
  top_drivers: SHAPFeatureDriver[];
}

export interface AlertStreamItem {
  alert_id: string;
  timestamp: number;
  src_ip: string;
  dst_ip: string;
  dst_port: number;
  attack_type?: string;
  detection_tier: string;
  supervised_probability: number;
  reconstruction_loss: number;
  is_attack: boolean;
  explanation: SHAPExplanationPayload;
}

export interface FlowScoreRequest {
  timestamp: number;
  src_ip: string;
  dst_ip: string;
  dst_port: number;
  flow_duration_ms: number;
  total_fwd_packets: number;
  total_bwd_packets: number;
  total_fwd_bytes: number;
  total_bwd_bytes: number;
  fwd_packet_length_mean?: number;
  fwd_packet_length_std?: number;
  bwd_packet_length_mean?: number;
  bwd_packet_length_std?: number;
  flow_bytes_per_sec?: number;
  flow_packets_per_sec?: number;
  flow_iat_mean_ms?: number;
  flow_iat_std_ms?: number;
  flow_iat_max_ms?: number;
  flow_iat_min_ms?: number;
  fwd_iat_mean_ms?: number;
  bwd_iat_mean_ms?: number;
  fwd_syn_flags?: number;
  fwd_rst_flags?: number;
  fwd_psh_flags?: number;
  fwd_ack_flags?: number;
  bwd_syn_flags?: number;
  bwd_rst_flags?: number;
  bwd_psh_flags?: number;
  bwd_ack_flags?: number;
  header_length_ratio?: number;
  packet_size_variance?: number;
  down_up_ratio?: number;
  avg_fwd_segment_size?: number;
  avg_bwd_segment_size?: number;
  attack_type?: string;
  label?: number;
  supervised_threshold?: number;
}

export interface ScoreResponse {
  is_attack: boolean;
  calibrated_verdict: boolean;
  detection_tier: string;
  supervised_probability: number;
  supervised_score: number;
  supervised_prediction: number;
  reconstruction_loss: number;
  reconstruction_threshold: number;
  autoencoder_prediction: number;
  cost_calibrated_threshold: number;
  model_version: string;
  latency_ms: number;
}

export interface GraphNode {
  id: string;
  label: string;
  x: number;
  y: number;
  r: number;
  color: string;
  role: string;
  is_pivot: boolean;
  out_degree: number;
  in_degree: number;
  degree_zscore: number;
  jaccard_novelty: number;
  pagerank: number;
  pagerank_delta: number;
  reasons: string[];
}

export interface GraphEdge {
  source: string;
  target: string;
  source_x: number;
  source_y: number;
  target_x: number;
  target_y: number;
  weight: number;
  color: string;
}

export interface GraphMetricsSummary {
  window_start: number;
  window_end: number;
  num_nodes: number;
  num_edges: number;
  num_pivots: number;
  max_degree_zscore: number;
  max_jaccard_novelty: number;
  max_pagerank_delta: number;
}

export interface GraphStateResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  metrics: GraphMetricsSummary;
  num_nodes: number;
  num_edges: number;
  flagged_pivots: string[];
}

export interface EvasionTestRequest {
  perturbation_budget: number;
  padding_ratio?: number;
  jitter_ms?: number;
  sample_size?: number;
}

export interface EvasionTestResponse {
  perturbation_budget: number;
  recall: number;
  supervised_recall: number;
  autoencoder_recall: number;
  combined_recall: number;
  samples_tested: number;
}

export interface FeatureDriftStat {
  feature_name: string;
  ks_statistic: number;
  ks_pvalue: number;
  psi_score: number;
  is_drifted: boolean;
  severity: string;
}

export interface DriftStatusResponse {
  status: string;
  retraining_recommended: boolean;
  drift_feature_ratio: number;
  num_drifted_features: number;
  total_features_evaluated: number;
  dataset_drift_detected: boolean;
  feature_details: FeatureDriftStat[];
}

export interface TelemetryMetrics {
  uptime_seconds: number;
  total_requests: number;
  total_attacks_flagged: number;
  attack_rate: number;
  tier1_detections: number;
  tier2_detections: number;
  sla_violations: number;
  sla_compliance_rate: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  latency_p99_ms: number;
  latency_mean_ms: number;
}

export interface HealthTierDetails {
  tier0_preprocessor: boolean;
  tier1_supervised: boolean;
  tier2_autoencoder: boolean;
  tier3_lateral_graph: boolean;
  tier4_adversarial_engine: boolean;
  tier5_cost_calibrator: boolean;
  tier5_shap_explainer: boolean;
  tier5_drift_monitor: boolean;
}

export interface HealthResponse {
  status: string;
  all_tiers_loaded: boolean;
  model_id?: string;
  version?: string;
  dataset_hash?: string;
  model_status?: string;
  tiers: HealthTierDetails;
}
