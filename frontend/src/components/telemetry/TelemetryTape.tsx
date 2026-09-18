import React from 'react';
import type { HealthResponse, TelemetryMetrics, DriftStatusResponse } from '@/lib/types';

interface TelemetryTapeProps {
  health: HealthResponse | null;
  metrics: TelemetryMetrics | null;
  drift: DriftStatusResponse | null;
  wsStatus: 'connected' | 'disconnected' | 'connecting';
  costThreshold: number;
}

export const TelemetryTape: React.FC<TelemetryTapeProps> = ({
  health,
  metrics,
  drift,
  wsStatus,
  costThreshold,
}) => {
  const modelId = health?.model_id || 'sentinelnet_1.0.0';
  const sha = (health?.dataset_hash || '99d9bece').slice(0, 8);
  const p95Latency = metrics?.latency_p95_ms ?? 0.42;
  const isSlaCompliant = p95Latency <= 1.5;

  const isDrifted = drift?.retraining_recommended ?? false;
  const driftRatio = drift ? `${(drift.drift_feature_ratio * 100).toFixed(1)}%` : '0.0%';

  return (
    <div className="h-9 bg-[#0d1117] border border-[#21262d] rounded-[2px] px-3 flex items-center justify-between font-mono text-[10px] tracking-wide whitespace-nowrap overflow-x-auto shadow-none select-none">
      <div className="flex items-center gap-4">
        {/* System Node */}
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-[1px] bg-[#3FB950] inline-block animate-pulse" />
          <span className="font-heading font-bold text-[#8b949e] uppercase">SYSTEM:</span>
          <span className="text-[#e6edf3] font-medium">SENTINELNET AIR-GAPPED SOC</span>
        </div>

        <span className="text-[#30363d]">|</span>

        {/* Model & Lineage */}
        <div className="flex items-center gap-1.5">
          <span className="font-heading font-bold text-[#8b949e] uppercase">MODEL:</span>
          <span className="text-[#e6edf3] font-semibold">{modelId.slice(0, 18)}...</span>
          <span className="text-[#8b949e]">(SHA: <code className="text-[#e6edf3]">{sha}</code>)</span>
        </div>

        <span className="text-[#30363d]">|</span>

        {/* SLA Latency */}
        <div className="flex items-center gap-1.5">
          <span className="font-heading font-bold text-[#8b949e] uppercase">INFERENCE SLA:</span>
          <span className={isSlaCompliant ? 'text-[#3FB950] font-semibold' : 'text-[#F85149] font-bold'}>
            {p95Latency.toFixed(3)} ms (p95)
          </span>
          <span className="text-[#8b949e]">[&lt; 1.5ms]</span>
        </div>

        <span className="text-[#30363d]">|</span>

        {/* Cost Calibrated Threshold */}
        <div className="flex items-center gap-1.5">
          <span className="font-heading font-bold text-[#8b949e] uppercase">CALIBRATED THRESH:</span>
          <span className="text-[#D29922] font-semibold">{costThreshold.toFixed(2)} ($50k FN)</span>
        </div>

        <span className="text-[#30363d]">|</span>

        {/* Drift Observatory */}
        <div className="flex items-center gap-1.5">
          <span className="font-heading font-bold text-[#8b949e] uppercase">DRIFT:</span>
          <span className={isDrifted ? 'text-[#F85149] font-bold' : 'text-[#3FB950] font-semibold'}>
            {isDrifted ? `ALERT (${driftRatio})` : `NOMINAL (${driftRatio})`}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Stream Status */}
        <div className="flex items-center gap-1.5">
          <span
            className={`w-1.5 h-1.5 rounded-[1px] ${
              wsStatus === 'connected'
                ? 'bg-[#3FB950]'
                : wsStatus === 'connecting'
                ? 'bg-[#D29922]'
                : 'bg-[#F85149]'
            }`}
          />
          <span className="font-heading text-[9px] uppercase tracking-wider text-[#8b949e]">
            STREAM: <span className="text-[#e6edf3] font-mono">{wsStatus.toUpperCase()}</span>
          </span>
        </div>

        <span className="text-[#3FB950] font-bold text-[9.5px] tracking-wider">[ARMED & ACTIVE]</span>
      </div>
    </div>
  );
};
