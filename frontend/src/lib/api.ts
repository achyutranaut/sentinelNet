import type {
  AlertStreamItem,
  DriftStatusResponse,
  EvasionTestResponse,
  FlowScoreRequest,
  GraphStateResponse,
  HealthResponse,
  ScoreResponse,
  TelemetryMetrics,
} from './types';

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
export const WS_BASE = import.meta.env.VITE_WS_BASE || 'ws://localhost:8000';
export const API_KEY = import.meta.env.VITE_API_KEY || 'sentinel-dev-secret-key-32b';

const defaultHeaders = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY,
};

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`, { headers: defaultHeaders });
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function getMetrics(): Promise<TelemetryMetrics> {
  const res = await fetch(`${API_BASE}/metrics`, { headers: defaultHeaders });
  if (!res.ok) throw new Error(`Failed to fetch metrics: ${res.status}`);
  return res.json();
}

export async function getGraphState(): Promise<GraphStateResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/graph/state`, { headers: defaultHeaders });
  } catch (err: any) {
    throw new Error(`Unable to connect to backend at ${API_BASE} — is the service running? (${err?.message || 'Network error'})`);
  }

  if (!res.ok) {
    let errorDetail = '';
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || errorJson.message || JSON.stringify(errorJson);
    } catch {
      errorDetail = res.statusText;
    }
    throw new Error(`Failed to fetch graph state: HTTP ${res.status} (${errorDetail || 'Server Error'})`);
  }
  return res.json();
}

export async function getDriftStatus(): Promise<DriftStatusResponse> {
  const res = await fetch(`${API_BASE}/drift/status`, { headers: defaultHeaders });
  if (!res.ok) throw new Error(`Failed to fetch drift status: ${res.status}`);
  return res.json();
}

export async function testEvasion(budget: number, sampleSize: number = 30): Promise<EvasionTestResponse> {
  const res = await fetch(`${API_BASE}/evasion/test`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify({ perturbation_budget: budget, sample_size: sampleSize }),
  });
  if (!res.ok) throw new Error(`Adversarial test failed: ${res.status}`);
  return res.json();
}

export async function scoreFlow(flow: FlowScoreRequest): Promise<ScoreResponse> {
  const res = await fetch(`${API_BASE}/score`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(flow),
  });
  if (!res.ok) throw new Error(`Scoring failed: ${res.status}`);
  return res.json();
}

export function connectAlertsStream(
  onAlert: (alert: AlertStreamItem) => void,
  onStatusChange?: (status: 'connected' | 'disconnected' | 'connecting') => void
): () => void {
  let ws: WebSocket | null = null;
  let isClosedManually = false;
  let reconnectTimer: number | undefined;

  function connect() {
    if (isClosedManually) return;
    onStatusChange?.('connecting');
    ws = new WebSocket(`${WS_BASE}/alerts/stream?api_key=${encodeURIComponent(API_KEY)}`);

    ws.onopen = () => {
      onStatusChange?.('connected');
    };

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.alert_id && data.explanation) {
          onAlert(data as AlertStreamItem);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket alert message:', err);
      }
    };

    ws.onclose = () => {
      onStatusChange?.('disconnected');
      if (!isClosedManually) {
        reconnectTimer = window.setTimeout(connect, 2000);
      }
    };

    ws.onerror = (err) => {
      console.warn('Alerts WebSocket encountered error:', err);
      ws?.close();
    };
  }

  connect();

  return () => {
    isClosedManually = true;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    if (ws) {
      ws.close();
      ws = null;
    }
  };
}

/**
 * Creates realistic NetFlow records for injection into POST /score.
 * Note: Zero ML model evaluation happens here — the payload is sent directly to FastAPI /score.
 */
export function createScenarioFlowBatch(
  scenario: string,
  count: number,
  supervisedThreshold?: number
): FlowScoreRequest[] {
  const flows: FlowScoreRequest[] = [];
  const now = Date.now() / 1000;

  const sampleInternalServers = ['10.0.1.10', '10.0.1.20', '10.0.1.30', '10.0.1.50'];
  const sampleDMZ = ['192.168.1.100', '192.168.1.105', '192.168.1.200'];
  const sampleEndpoints = ['172.16.0.4', '172.16.0.12', '172.16.0.45', '172.16.0.88'];

  for (let i = 0; i < count; i++) {
    const timestamp = now + i * 0.05;
    let flow: FlowScoreRequest;

    if (scenario.includes('DDOS_SYN_FLOOD')) {
      flow = {
        timestamp,
        src_ip: `198.51.100.${10 + (i % 20)}`,
        dst_ip: '10.0.1.10',
        dst_port: 80,
        flow_duration_ms: 12.0 + Math.random() * 5.0,
        total_fwd_packets: 40 + Math.floor(Math.random() * 50),
        total_bwd_packets: 0,
        total_fwd_bytes: 2400 + Math.random() * 800,
        total_bwd_bytes: 0,
        fwd_syn_flags: 1,
        bwd_syn_flags: 0,
        flow_packets_per_sec: 3500.0,
        flow_bytes_per_sec: 180000.0,
        header_length_ratio: 0.95,
        attack_type: 'DDOS_SYN_FLOOD',
        label: 1,
      };
    } else if (scenario.includes('PORT_SCAN')) {
      flow = {
        timestamp,
        src_ip: '203.0.113.88',
        dst_ip: sampleDMZ[i % sampleDMZ.length],
        dst_port: 1024 + (i * 37) % 64000,
        flow_duration_ms: 2.5 + Math.random() * 3.0,
        total_fwd_packets: 2,
        total_bwd_packets: 0,
        total_fwd_bytes: 120.0,
        total_bwd_bytes: 0,
        fwd_syn_flags: 1,
        fwd_rst_flags: 0,
        flow_packets_per_sec: 800.0,
        attack_type: 'PORT_SCAN',
        label: 1,
      };
    } else if (scenario.includes('SSH_BRUTE_FORCE')) {
      flow = {
        timestamp,
        src_ip: '198.51.100.22',
        dst_ip: '192.168.1.100',
        dst_port: 22,
        flow_duration_ms: 320.0 + Math.random() * 150.0,
        total_fwd_packets: 18 + Math.floor(Math.random() * 10),
        total_bwd_packets: 16 + Math.floor(Math.random() * 8),
        total_fwd_bytes: 1800 + Math.random() * 500,
        total_bwd_bytes: 2400 + Math.random() * 600,
        fwd_psh_flags: 8,
        bwd_psh_flags: 7,
        attack_type: 'SSH_BRUTE_FORCE',
        label: 1,
      };
    } else if (scenario.includes('ZERO_DAY_C2_EXFILTRATION')) {
      flow = {
        timestamp,
        src_ip: sampleEndpoints[i % sampleEndpoints.length],
        dst_ip: '185.220.101.5',
        dst_port: 443,
        flow_duration_ms: 4500.0 + Math.random() * 3000.0,
        total_fwd_packets: 85 + Math.floor(Math.random() * 40),
        total_bwd_packets: 12 + Math.floor(Math.random() * 5),
        total_fwd_bytes: 95000 + Math.random() * 45000,
        total_bwd_bytes: 1400 + Math.random() * 400,
        packet_size_variance: 4200.0,
        flow_bytes_per_sec: 25000.0,
        attack_type: 'ZERO_DAY_C2_EXFILTRATION',
        label: 1,
      };
    } else if (scenario.includes('LATERAL_MOVEMENT')) {
      flow = {
        timestamp,
        src_ip: sampleEndpoints[0],
        dst_ip: sampleInternalServers[i % sampleInternalServers.length],
        dst_port: 445,
        flow_duration_ms: 180.0 + Math.random() * 80.0,
        total_fwd_packets: 24 + Math.floor(Math.random() * 12),
        total_bwd_packets: 22 + Math.floor(Math.random() * 10),
        total_fwd_bytes: 4200 + Math.random() * 1200,
        total_bwd_bytes: 3800 + Math.random() * 900,
        fwd_syn_flags: 1,
        fwd_ack_flags: 20,
        bwd_ack_flags: 18,
        attack_type: 'LATERAL_MOVEMENT',
        label: 1,
      };
    } else {
      // Enterprise Benign Baseline
      flow = {
        timestamp,
        src_ip: sampleEndpoints[i % sampleEndpoints.length],
        dst_ip: sampleDMZ[i % sampleDMZ.length],
        dst_port: (i % 2 === 0) ? 443 : 80,
        flow_duration_ms: 45.0 + Math.random() * 60.0,
        total_fwd_packets: 6 + Math.floor(Math.random() * 8),
        total_bwd_packets: 8 + Math.floor(Math.random() * 10),
        total_fwd_bytes: 520 + Math.random() * 400,
        total_bwd_bytes: 1400 + Math.random() * 1200,
        flow_iat_mean_ms: 12.0 + Math.random() * 5.0,
        attack_type: 'BENIGN',
        label: 0,
      };
    }

    if (supervisedThreshold !== undefined) {
      flow.supervised_threshold = supervisedThreshold;
    }

    flows.push(flow);
  }

  return flows;
}
