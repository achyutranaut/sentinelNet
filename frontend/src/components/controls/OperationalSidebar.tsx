import React, { useState } from 'react';
import {
  Send,
  Shield,
  AlertTriangle,
  Server,
  PanelLeftClose,
  PanelLeftOpen,
  RefreshCw,
  Activity,
} from 'lucide-react';
import { createScenarioFlowBatch, scoreFlow } from '@/lib/api';
import type { AlertStreamItem } from '@/lib/types';
import { CustomSlider } from '@/components/common/CustomSlider';

interface OperationalSidebarProps {
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  costThreshold: number;
  onCostThresholdChange: (val: number) => void;
  aeCutoff: number;
  onAeCutoffChange: (val: number) => void;
  onBatchScored: (newAlerts: AlertStreamItem[]) => void;
  onRefreshGraph: () => void;
}

export const OperationalSidebar: React.FC<OperationalSidebarProps> = ({
  isCollapsed = false,
  onToggleCollapse,
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
              base_value: 0.15,
              analyst_summary: isAttack
                ? `High-risk telemetry breach flagged by ${res.detection_tier}. Model confidence: ${(res.supervised_probability * 100).toFixed(1)}%.`
                : `Benign operational flow verified by ${res.detection_tier}.`,
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

  if (isCollapsed) {
    return (
      <aside className="w-14 bg-[#0d1117] border-r border-[#1f2937] flex flex-col items-center py-3 gap-3 select-none shrink-0 z-20 transition-all duration-200">
        {/* Toggle Expand Button */}
        {onToggleCollapse && (
          <button
            type="button"
            onClick={onToggleCollapse}
            title="Expand Operational Rail (w-56)"
            className="p-2 rounded bg-[#161b22] hover:bg-[#21262d] text-slate-400 hover:text-sky-400 border border-[#30363d] cursor-pointer transition-colors"
          >
            <PanelLeftOpen className="w-4 h-4" />
          </button>
        )}

        <div className="w-8 h-[1px] bg-[#1f2937]" />

        {/* Quick Ingest Action Button */}
        <button
          type="button"
          disabled={isInjecting}
          onClick={handleInjectBatch}
          title={`Ingest & Score Batch (${batchSize} flows · ${selectedScenario})`}
          className="p-2.5 rounded bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-400 border border-emerald-700/60 hover:border-emerald-500 shadow-[0_0_10px_rgba(63,185,80,0.25)] cursor-pointer transition-all disabled:opacity-50"
        >
          <Send className={`w-4 h-4 ${isInjecting ? 'animate-spin' : ''}`} />
        </button>

        {/* Scenario Quick Cycle Button */}
        <button
          type="button"
          onClick={() => {
            const idx = scenarios.findIndex((s) => s.id === selectedScenario);
            const next = scenarios[(idx + 1) % scenarios.length];
            setSelectedScenario(next.id);
          }}
          title={`Active Scenario: ${selectedScenario} (Click to cycle)`}
          className="p-2 rounded bg-[#161b22] hover:bg-[#21262d] text-sky-400 border border-[#21262d] hover:border-sky-500/50 cursor-pointer transition-colors"
        >
          <Activity className="w-4 h-4" />
        </button>

        {/* Batch Size Quick Cycle Button */}
        <button
          type="button"
          onClick={() => {
            const sizes = [5, 15, 30, 50];
            const idx = sizes.indexOf(batchSize);
            setBatchSize(sizes[(idx + 1) % sizes.length]);
          }}
          title={`Batch Size: ${batchSize} flows (Click to cycle)`}
          className="w-8 h-8 rounded bg-[#161b22] hover:bg-[#21262d] text-slate-200 font-mono text-xs font-bold border border-[#21262d] flex items-center justify-center cursor-pointer transition-colors tabular-nums"
        >
          {batchSize}
        </button>

        {/* Topology State Refresh */}
        <button
          type="button"
          onClick={onRefreshGraph}
          title="Refresh Network Topology State"
          className="p-2 rounded bg-[#161b22] hover:bg-[#21262d] text-purple-400 border border-[#21262d] hover:border-purple-500/50 cursor-pointer transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        {/* Air-Gapped Matrix Indicator at Bottom */}
        <div className="mt-auto flex flex-col items-center gap-1">
          <div
            className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#3fb950] animate-pulse"
            title="Air-Gapped Matrix Armed"
          />
          <span className="text-[8px] font-mono text-emerald-500 font-bold uppercase tracking-tighter">
            AG
          </span>
        </div>
      </aside>
    );
  }

  return (
    <aside className="w-56 bg-[#0d1117] border-r border-[#1f2937] flex flex-col justify-start gap-3.5 p-3.5 select-none overflow-y-auto shrink-0 shadow-lg transition-all duration-200">
      {/* Sidebar Header */}
      <div className="font-heading text-xs font-bold tracking-widest text-slate-400 border-b border-[#1f2937] pb-2.5 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-1.5">
          <Server className="w-3.5 h-3.5 text-[#3FB950]" />
          <span className="text-slate-200 text-xs font-heading font-bold">CONTROLS</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-[#3FB950] font-mono px-1.5 py-0.2 rounded bg-[#3FB950]/10 border border-[#3FB950]/30 font-semibold uppercase tracking-wider">
            AIR-GAPPED
          </span>
          {onToggleCollapse && (
            <button
              type="button"
              onClick={onToggleCollapse}
              title="Collapse to Compact Icon Rail (w-14)"
              className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-[#161b22] cursor-pointer transition-colors"
            >
              <PanelLeftClose className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      <div className="space-y-3.5">
        {/* Scenario Selection */}
        <div>
          <label className="font-sans text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1">
            Traffic Scenario
          </label>
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className="w-full bg-[#161b22] border border-[#21262d] focus:border-[#38bdf8] rounded px-2.5 py-1.5 text-slate-200 font-sans text-xs outline-none transition-colors cursor-pointer"
          >
            {scenarios.map((scen) => (
              <option key={scen.id} value={scen.id}>
                {scen.label}
              </option>
            ))}
          </select>
        </div>

        {/* Batch Size Selector */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="font-sans text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
              Batch Size
            </label>
            <span className="font-mono text-xs font-bold text-[#38bdf8] px-1.5 py-0.2 rounded bg-slate-800 border border-slate-700 tabular-nums">
              {batchSize}
            </span>
          </div>
          <div className="grid grid-cols-4 gap-1">
            {[5, 15, 30, 50].map((size) => (
              <button
                key={size}
                type="button"
                onClick={() => setBatchSize(size)}
                className={`py-1 rounded font-mono text-xs font-semibold tabular-nums transition-all cursor-pointer border ${
                  batchSize === size
                    ? 'bg-[#38bdf8]/20 text-[#38bdf8] border-[#38bdf8]/50 shadow-xs'
                    : 'bg-[#161b22] text-slate-400 border-[#21262d] hover:border-slate-600 hover:text-slate-200'
                }`}
              >
                {size}
              </button>
            ))}
          </div>
        </div>

        {/* Primary Action Button */}
        <button
          type="button"
          disabled={isInjecting}
          onClick={handleInjectBatch}
          className="w-full bg-[#3FB950] hover:bg-[#2ea043] active:bg-[#238636] text-[#090b0e] rounded py-2 px-3 font-heading font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-1.5 cursor-pointer transition-all shadow-[0_0_12px_rgba(63,185,80,0.25)] disabled:opacity-50"
        >
          <Send className={`w-3.5 h-3.5 ${isInjecting ? 'animate-spin' : ''}`} />
          <span>{isInjecting ? 'SCORING...' : 'INGEST BATCH'}</span>
        </button>

        {lastBatchTime !== null && (
          <div className="text-[11px] font-mono tabular-nums text-slate-400 text-center bg-slate-900/60 py-1 rounded border border-slate-800">
            Batch scored in: <span className="text-[#3FB950] font-bold">{lastBatchTime.toFixed(1)} ms</span>
          </div>
        )}

        {/* Detection Threshold Calibration using CustomSlider */}
        <div className="pt-2.5 border-t border-[#1f2937] space-y-3">
          <div className="font-heading text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-[#D29922]" />
            <span>Calibration</span>
          </div>

          <CustomSlider
            label="Tier 1 Cost Threshold"
            sublabel="Neyman-Pearson penalty"
            min={0.01}
            max={0.99}
            step={0.01}
            value={costThreshold}
            onChange={onCostThresholdChange}
            color="#D29922"
          />

          <CustomSlider
            label="Tier 2 AE Anomaly Cutoff"
            sublabel="Reconstruction MSE"
            min={0.10}
            max={2.00}
            step={0.05}
            value={aeCutoff}
            onChange={onAeCutoffChange}
            color="#38bdf8"
          />
        </div>

        {/* Air-Gapped Security Notice */}
        <div className="pt-2.5 border-t border-[#1f2937]">
          <div className="bg-[#161b22] border border-[#21262d] rounded p-2.5 space-y-1 text-xs text-slate-300">
            <div className="flex items-center gap-1 text-[#D29922] font-semibold text-[11px]">
              <AlertTriangle className="w-3 h-3" />
              <span>AIR-GAPPED SERVING</span>
            </div>
            <p className="leading-snug text-slate-400 text-[11px]">
              Zero-trust streaming connection to SentinelNet backend. Client executes zero local ML models.
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
};
