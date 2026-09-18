import React, { useState } from 'react';
import type { DriftStatusResponse } from '@/lib/types';
import { ChevronDown, ChevronUp, DatabaseZap, RefreshCw } from 'lucide-react';

interface DriftObservatoryProps {
  drift: DriftStatusResponse | null;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export const DriftObservatory: React.FC<DriftObservatoryProps> = ({
  drift,
  onRefresh,
  isLoading = false,
}) => {
  const [isOpen, setIsOpen] = useState(true);

  const isDriftDetected = drift?.dataset_drift_detected ?? false;
  const isRetrainRecommended = drift?.retraining_recommended ?? false;
  const totalFeatures = drift?.total_features_evaluated ?? 30;
  const numDrifted = drift?.num_drifted_features ?? 0;
  const driftRatio = drift ? (drift.drift_feature_ratio * 100).toFixed(1) : '0.0';

  const featureDetails = drift?.feature_details || [];
  const sortedFeatures = [...featureDetails].sort((a, b) => b.psi_score - a.psi_score);

  return (
    <div className="bg-[#0d1117] border border-[#21262d] rounded-[2px] flex flex-col overflow-hidden shadow-none">
      {/* Drawer Header Toggle */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="bg-[#161b22] border-b border-[#21262d] px-3 py-2 flex justify-between items-center cursor-pointer select-none font-heading text-[10px] font-bold tracking-wider uppercase text-[#8b949e] hover:bg-[#1c2128] transition-colors"
      >
        <div className="flex items-center gap-2">
          <DatabaseZap className="w-3.5 h-3.5 text-[#e6edf3]" />
          <span className="text-[#e6edf3]">OPERATIONAL TELEMETRY //</span>
          <span>STATISTICAL DRIFT OBSERVATORY & RETRAINING STATUS (KS / PSI)</span>
        </div>

        <div className="flex items-center gap-3">
          <span
            className={
              isRetrainRecommended
                ? 'badge-critical'
                : isDriftDetected
                ? 'badge-warning'
                : 'badge-secure'
            }
          >
            {isRetrainRecommended ? 'RETRAINING TRIGGERED' : isDriftDetected ? 'DRIFT DETECTED' : 'STABLE'}
          </span>

          {onRefresh && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRefresh();
              }}
              disabled={isLoading}
              className="p-1 text-[#8b949e] hover:text-[#e6edf3] rounded-[2px] border border-[#30363d] cursor-pointer disabled:opacity-50"
              title="Refresh drift statistics"
            >
              <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          )}

          {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </div>

      {isOpen && (
        <div className="p-3.5 space-y-4 font-mono">
          {/* KPI Metrics Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-[#161b22] border border-[#21262d] rounded p-3">
              <div className="font-heading text-xs uppercase tracking-wider text-[#8b949e] font-semibold">
                Features Evaluated
              </div>
              <div className="text-xl font-bold text-[#e6edf3] mt-1 tabular-nums">{totalFeatures}</div>
            </div>

            <div className="bg-[#161b22] border border-[#21262d] rounded p-3">
              <div className="font-heading text-xs uppercase tracking-wider text-[#8b949e] font-semibold">
                Drifted Features
              </div>
              <div
                className={`text-xl font-bold mt-1 tabular-nums ${
                  numDrifted > 0 ? 'text-[#F85149]' : 'text-[#3FB950]'
                }`}
              >
                {numDrifted}
              </div>
            </div>

            <div className="bg-[#161b22] border border-[#21262d] rounded p-3">
              <div className="font-heading text-xs uppercase tracking-wider text-[#8b949e] font-semibold">
                Drift Feature Ratio
              </div>
              <div
                className={`text-xl font-bold mt-1 tabular-nums ${
                  parseFloat(driftRatio) > 10 ? 'text-[#F85149]' : 'text-[#3FB950]'
                }`}
              >
                {driftRatio}%
              </div>
            </div>

            <div className="bg-[#161b22] border border-[#21262d] rounded p-3">
              <div className="font-heading text-xs uppercase tracking-wider text-[#8b949e] font-semibold">
                Retraining Trigger
              </div>
              <div
                className={`text-sm font-bold mt-1 ${
                  isRetrainRecommended ? 'text-[#F85149]' : 'text-[#3FB950]'
                }`}
              >
                {isRetrainRecommended ? 'RECOMMENDED' : 'NOMINAL'}
              </div>
            </div>
          </div>

          {/* Feature Distribution Matrix Grid - grid-cols-2 md:grid-cols-4 lg:grid-cols-6 */}
          <div>
            <div className="font-heading text-xs font-bold text-[#8b949e] uppercase tracking-wider mb-2">
              Feature Stability Matrix (30 Features)
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2 bg-[#090b0e] border border-[#21262d] rounded p-3">
              {sortedFeatures.map((feat) => {
                const isCrit = feat.severity.toLowerCase() === 'critical';
                const isWarn = feat.severity.toLowerCase() === 'moderate';
                const cellBg = isCrit
                  ? 'bg-[#F85149] text-[#0d1117]'
                  : isWarn
                  ? 'bg-[#D29922] text-[#0d1117]'
                  : 'bg-[#161b22] text-[#e6edf3] border border-[#21262d]';

                return (
                  <div
                    key={feat.feature_name}
                    title={`${feat.feature_name}\nPSI: ${feat.psi_score.toFixed(4)}\nKS: ${feat.ks_statistic.toFixed(4)} (p=${feat.ks_pvalue.toExponential(2)})\nSeverity: ${feat.severity.toUpperCase()}`}
                    className={`h-9 px-2 rounded flex flex-col justify-center items-center text-xs font-mono tabular-nums cursor-pointer transition-transform hover:scale-105 select-none ${cellBg}`}
                  >
                    <span className="truncate w-full text-center font-medium">
                      {feat.feature_name.slice(0, 10)}
                    </span>
                    <span className="text-[11px] opacity-85 font-semibold">{feat.psi_score.toFixed(3)}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top Drifted Features Monospace Table */}
          <div>
            <div className="font-heading text-xs font-bold text-[#8b949e] uppercase tracking-wider mb-2">
              Top Drifted Features (Ranked by Population Stability Index)
            </div>
            <div className="border border-[#21262d] rounded overflow-hidden overflow-x-auto w-full">
              <table className="w-full border-collapse text-left font-mono text-xs tabular-nums">
                <thead className="bg-[#161b22] text-[#8b949e] font-semibold text-xs uppercase tracking-wider border-b border-[#21262d]">
                  <tr>
                    <th className="py-2.5 px-3">FEATURE NAME</th>
                    <th className="py-2.5 px-3">PSI SCORE</th>
                    <th className="py-2.5 px-3">KS STATISTIC</th>
                    <th className="py-2.5 px-3">KS P-VALUE</th>
                    <th className="py-2.5 px-3">SEVERITY</th>
                    <th className="py-2.5 px-3">DISTRIBUTION ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#161b22] bg-[#0d1117]">
                  {sortedFeatures.slice(0, 8).map((feat) => {
                    const isCrit = feat.severity.toLowerCase() === 'critical';
                    const isWarn = feat.severity.toLowerCase() === 'moderate';

                    return (
                      <tr key={feat.feature_name} className="hover:bg-[#161b22] whitespace-nowrap transition-colors">
                        <td className="py-2 px-3 text-[#e6edf3] font-medium">{feat.feature_name}</td>
                        <td className="py-2 px-3 text-[#e6edf3] font-bold">{feat.psi_score.toFixed(4)}</td>
                        <td className="py-2 px-3 text-[#e6edf3]">{feat.ks_statistic.toFixed(4)}</td>
                        <td className="py-2 px-3 text-[#8b949e]">{feat.ks_pvalue.toExponential(2)}</td>
                        <td className="py-2 px-3">
                          {isCrit ? (
                            <span className="badge-critical">CRITICAL</span>
                          ) : isWarn ? (
                            <span className="badge-warning">MODERATE</span>
                          ) : (
                            <span className="badge-secure">NOMINAL</span>
                          )}
                        </td>
                        <td className="py-2 px-3 font-semibold">
                          {isCrit ? (
                            <span className="text-[#F85149]">TRIGGER CT PIPELINE</span>
                          ) : isWarn ? (
                            <span className="text-[#D29922]">MONITOR</span>
                          ) : (
                            <span className="text-[#3FB950]">PASS</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
