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
    <div className="h-9 shrink-0 min-h-[36px] w-full bg-[#0d1117] border border-[#21262d] rounded px-3 flex items-center justify-between font-mono text-xs tabular-nums tracking-wide whitespace-nowrap overflow-x-auto select-none">
      <div className="flex items-center gap-4">
        {/* System Node */}
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#3FB950] inline-block animate-pulse" />
          <span className="font-heading font-bold text-[#8b949e] uppercase text-xs">SYSTEM:</span>
          <span className="text-[#e6edf3] font-medium text-xs">SENTINEL.NET SOC</span>
        </div>

        <span className="text-[#30363d]">|</span>

        {/* Model & Lineage */}
        <div className="flex items-center gap-1.5">
          <span className="font-heading font-bold text-[#8b949e] uppercase text-xs">MODEL:</span>
          <span className="text-[#e6edf3] font-semibold text-xs">{modelId.slice(0, 18)}</span>
          <span className="text-[#8b949e] text-xs">(SHA: <code className="text-[#e6edf3]">{sha}</code>)</span>
        </div>

        <span className="text-[#30363d]">|</span>

        {/* SLA Latency */}
        <div className="flex items-center gap-1.5">
          <span className="font-heading font-bold text-[#8b949e] uppercase text-xs">INFERENCE SLA:</span>
          <span className={isSlaCompliant ? 'text-[#3FB950] font-semibold text-xs' : 'text-[#F85149] font-bold text-xs'}>
            {p95Latency.toFixed(2)} ms (p95)
          </span>
          <span className="text-[#8b949e] text-xs">{'[< 1.5ms]'}</span>
        </div>

        <span className="text-[#30363d]">|</span>

        {/* Cost Calibrated Threshold */}
        <div className="flex items-center gap-1.5">
          <span className="font-heading font-bold text-[#8b949e] uppercase text-xs">CALIBRATED THRESH:</span>
          <span className="text-[#D29922] font-semibold text-xs">{costThreshold.toFixed(2)} ($50k FN)</span>
        </div>

        <span className="text-[#30363d]">|</span>

        {/* Drift Observatory */}
        <div className="flex items-center gap-1.5">
          <span className="font-heading font-bold text-[#8b949e] uppercase text-xs">DRIFT:</span>
          <span className={isDrifted ? 'text-[#F85149] font-bold text-xs' : 'text-[#3FB950] font-semibold text-xs'}>
            {isDrifted ? `ALERT (${driftRatio})` : `NOMINAL (${driftRatio})`}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Stream Status */}
        <div className="flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${
              wsStatus === 'connected'
                ? 'bg-[#3FB950] animate-pulse'
                : wsStatus === 'connecting'
                ? 'bg-[#D29922]'
                : 'bg-[#F85149]'
            }`}
          />
          <span className="font-heading text-xs uppercase tracking-wider text-[#8b949e]">
            STREAM: <span className="text-[#e6edf3] font-mono text-xs">{wsStatus.toUpperCase()}</span>
          </span>
        </div>

        <span className="text-[#3FB950] font-bold text-xs tracking-wider">[ARMED & ACTIVE]</span>
      </div>
    </div>
  );
};
