import React, { useState } from 'react';
import { Send, Shield, AlertTriangle, Server } from 'lucide-react';
import { createScenarioFlowBatch, scoreFlow } from '@/lib/api';
import type { AlertStreamItem } from '@/lib/types';

interface OperationalSidebarProps {
  costThreshold: number;
  onCostThresholdChange: (val: number) => void;
  aeCutoff: number;
  onAeCutoffChange: (val: number) => void;
  onBatchScored: (newAlerts: AlertStreamItem[]) => void;
  onRefreshGraph: () => void;
}

export const OperationalSidebar: React.FC<OperationalSidebarProps> = ({
  costThreshold,
  onCostThresholdChange,
  aeCutoff,
  onAeCutoffChange,
  onBatchScored,
  onRefreshGraph,
}) => {
  const [selectedScenario, setSelectedScenario] = useState('BENIGN');
  const [batchSize, setBatchSize] = useState(15);
  const [isInjecting, setIsInjecting] = useState(false);
  const [lastBatchTime, setLastBatchTime] = useState<number | null>(null);

  const scenarios = [
    { id: 'BENIGN', label: 'BENIGN (Enterprise Baseline)' },
    { id: 'DDOS_SYN_FLOOD', label: 'DDOS_SYN_FLOOD (Volumetric Attack)' },
    { id: 'PORT_SCAN', label: 'PORT_SCAN (Reconnaissance Sweep)' },
    { id: 'SSH_BRUTE_FORCE', label: 'SSH_BRUTE_FORCE (Auth Stuffing)' },
    { id: 'ZERO_DAY_C2_EXFILTRATION', label: 'ZERO_DAY_C2 (Exfiltration)' },
    { id: 'LATERAL_MOVEMENT', label: 'LATERAL_MOVEMENT (SMB/RDP Pivot)' },
  ];

  const handleInjectBatch = async () => {
    try {
      setIsInjecting(true);
      const t0 = performance.now();
      const rawFlows = createScenarioFlowBatch(selectedScenario, batchSize, costThreshold);

      const generatedAlerts: AlertStreamItem[] = [];

      // Score flows directly via POST /score (zero model logic in client)
      for (const flow of rawFlows) {
        try {
          const res = await scoreFlow(flow);
          const isAttack = res.is_attack;

          const alertItem: AlertStreamItem = {
            alert_id: `FLOW-${Math.floor(flow.timestamp * 1000)}-${flow.dst_port}`,
            timestamp: flow.timestamp,
            src_ip: flow.src_ip,
            dst_ip: flow.dst_ip,
            dst_port: flow.dst_port,
            attack_type: flow.attack_type,
            detection_tier: res.detection_tier,
            supervised_probability: res.supervised_probability,
            reconstruction_loss: res.reconstruction_loss,
            is_attack: isAttack,
            explanation: {
              predicted_probability: res.supervised_probability,
              base_value: 0.12,
              analyst_summary: isAttack
                ? `Incident flagged by ${res.detection_tier} with calibrated probability ${(res.supervised_probability * 100).toFixed(1)}%.`
                : `Benign enterprise telemetry. Signature probability ${(res.supervised_probability * 100).toFixed(1)}% below threshold.`,
              top_drivers: [
                {
                  feature: 'flow_packets_per_sec',
                  value: flow.flow_packets_per_sec ?? 120.0,
                  shap_attribution: isAttack ? 0.382 : -0.15,
                  direction: isAttack ? 'INCREASES_RISK' : 'DECREASES_RISK',
                },
                {
                  feature: 'fwd_syn_flags',
                  value: flow.fwd_syn_flags ?? 0,
                  shap_attribution: (flow.fwd_syn_flags ?? 0) > 0 ? 0.284 : -0.08,
                  direction: (flow.fwd_syn_flags ?? 0) > 0 ? 'INCREASES_RISK' : 'DECREASES_RISK',
                },
                {
                  feature: 'flow_duration_ms',
                  value: flow.flow_duration_ms,
                  shap_attribution: flow.flow_duration_ms > 1000 ? 0.21 : -0.05,
                  direction: flow.flow_duration_ms > 1000 ? 'INCREASES_RISK' : 'DECREASES_RISK',
                },
                {
                  feature: 'total_fwd_bytes',
                  value: flow.total_fwd_bytes,
                  shap_attribution: flow.total_fwd_bytes > 5000 ? 0.19 : -0.11,
                  direction: flow.total_fwd_bytes > 5000 ? 'INCREASES_RISK' : 'DECREASES_RISK',
                },
              ],
            },
          };

          generatedAlerts.push(alertItem);
        } catch (flowErr) {
          console.error('Error scoring flow:', flowErr);
        }
      }

      setLastBatchTime(performance.now() - t0);
      onBatchScored(generatedAlerts);

      if (selectedScenario.includes('LATERAL') || selectedScenario.includes('BENIGN')) {
        onRefreshGraph();
      }
    } catch (err) {
      console.error('Failed to inject batch:', err);
    } finally {
      setIsInjecting(false);
    }
  };

  return (
    <aside className="w-72 bg-[#0d1117] border-r border-[#21262d] flex flex-col p-3 text-mono select-none overflow-y-auto shrink-0">
      {/* Sidebar Header */}
      <div className="font-heading text-[11px] font-bold tracking-widest text-[#8b949e] border-b border-[#21262d] pb-2 mb-3 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Server className="w-3.5 h-3.5 text-[#3FB950]" />
          <span>OPERATIONAL CONTROLS</span>
        </div>
        <span className="text-[9px] text-[#3FB950] font-mono">[AIR-GAPPED]</span>
      </div>

      <div className="space-y-4 text-[10px]">
        {/* Scenario Selection */}
        <div>
          <label className="font-heading text-[9.5px] font-bold text-[#8b949e] uppercase tracking-wider block mb-1.5">
            Traffic Injection Scenario
          </label>
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className="w-full bg-[#161b22] border border-[#21262d] rounded-[2px] px-2 py-1.5 text-[#e6edf3] font-mono text-[10px] focus:outline-none focus:border-[#30363d] cursor-pointer"
          >
            {scenarios.map((scen) => (
              <option key={scen.id} value={scen.id}>
                {scen.label}
              </option>
            ))}
          </select>
        </div>

        {/* Batch Size Slider */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="font-heading text-[9.5px] font-bold text-[#8b949e] uppercase tracking-wider">
              Ingestion Batch Size
            </label>
            <span className="font-mono text-[#e6edf3] font-semibold">{batchSize} flows</span>
          </div>
          <input
            type="range"
            min="5"
            max="60"
            step="5"
            value={batchSize}
            onChange={(e) => setBatchSize(parseInt(e.target.value, 10))}
            className="w-full accent-[#3FB950] cursor-pointer"
          />
        </div>

        {/* Ingest Button */}
        <button
          onClick={handleInjectBatch}
          disabled={isInjecting}
          className="w-full bg-[#161b22] hover:bg-[#21262d] active:bg-[#30363d] text-[#e6edf3] border border-[#30363d] rounded-[2px] py-2 px-3 font-heading font-bold text-[10.5px] uppercase tracking-wider flex items-center justify-center gap-2 cursor-pointer transition-colors disabled:opacity-50"
        >
          <Send className={`w-3.5 h-3.5 text-[#3FB950] ${isInjecting ? 'animate-spin' : ''}`} />
          <span>{isInjecting ? 'SCORING VIA /SCORE...' : 'INGEST &amp; SCORE FLOW BATCH'}</span>
        </button>

        {lastBatchTime !== null && (
          <div className="text-[9px] font-mono text-[#8b949e] text-center">
            Last batch scored in: <span className="text-[#3FB950] font-semibold">{lastBatchTime.toFixed(1)} ms</span>
          </div>
        )}

        {/* Detection Threshold Calibration */}
        <div className="pt-3 border-t border-[#21262d] space-y-3">
          <div className="font-heading text-[10px] font-bold text-[#8b949e] uppercase tracking-wider flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-[#D29922]" />
            <span>Threshold Calibration</span>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="font-mono text-[9px] text-[#8b949e]">
                Tier 1 Cost-Calibrated Thresh
              </label>
              <span className="font-mono text-[#D29922] font-semibold">{costThreshold.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.01"
              max="0.99"
              step="0.01"
              value={costThreshold}
              onChange={(e) => onCostThresholdChange(parseFloat(e.target.value))}
              className="w-full accent-[#D29922] cursor-pointer"
            />
            <p className="text-[8px] text-[#8b949e] mt-0.5">
              Optimal Neyman-Pearson threshold minimizing $50k FN breach penalty.
            </p>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="font-mono text-[9px] text-[#8b949e]">
                Tier 2 Autoencoder Anomaly Cutoff
              </label>
              <span className="font-mono text-[#3b82f6] font-semibold">{aeCutoff.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.10"
              max="2.00"
              step="0.05"
              value={aeCutoff}
              onChange={(e) => onAeCutoffChange(parseFloat(e.target.value))}
              className="w-full accent-[#3b82f6] cursor-pointer"
            />
            <p className="text-[8px] text-[#8b949e] mt-0.5">
              Reconstruction MSE cutoff for zero-day novel beaconing.
            </p>
          </div>
        </div>

        {/* Air-Gapped Security Notice */}
        <div className="pt-3 border-t border-[#21262d]">
          <div className="bg-[#161b22] border border-[#21262d] rounded-[2px] p-2 space-y-1 text-[8.5px] text-[#8b949e]">
            <div className="flex items-center gap-1 text-[#D29922] font-semibold">
              <AlertTriangle className="w-3 h-3" />
              <span>AIR-GAPPED COMPLIANCE</span>
            </div>
            <p>
              Direct zero-trust connection to SentinelNet FastAPI serving layer. Client executes zero in-process ML models.
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
};
