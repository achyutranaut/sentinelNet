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
          <span>STATISTICAL DRIFT OBSERVATORY &amp; RETRAINING STATUS (KS / PSI)</span>
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
        <div className="p-3 space-y-3 font-mono">
          {/* KPI Metrics Row */}
          <div className="grid grid-cols-4 gap-2">
            <div className="bg-[#161b22] border border-[#21262d] rounded-[2px] p-2.5">
              <div className="font-heading text-[9px] uppercase tracking-wider text-[#8b949e]">
                Features Evaluated
              </div>
              <div className="text-base font-bold text-[#e6edf3] mt-1">{totalFeatures}</div>
            </div>

            <div className="bg-[#161b22] border border-[#21262d] rounded-[2px] p-2.5">
              <div className="font-heading text-[9px] uppercase tracking-wider text-[#8b949e]">
                Drifted Features
              </div>
              <div
                className={`text-base font-bold mt-1 ${
                  numDrifted > 0 ? 'text-[#F85149]' : 'text-[#3FB950]'
                }`}
              >
                {numDrifted}
              </div>
            </div>

            <div className="bg-[#161b22] border border-[#21262d] rounded-[2px] p-2.5">
              <div className="font-heading text-[9px] uppercase tracking-wider text-[#8b949e]">
                Drift Feature Ratio
              </div>
              <div
                className={`text-base font-bold mt-1 ${
                  parseFloat(driftRatio) > 0.1 ? 'text-[#F85149]' : 'text-[#3FB950]'
                }`}
              >
                {driftRatio}%
              </div>
            </div>

            <div className="bg-[#161b22] border border-[#21262d] rounded-[2px] p-2.5">
              <div className="font-heading text-[9px] uppercase tracking-wider text-[#8b949e]">
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

          {/* Feature Distribution Matrix Grid */}
          <div>
            <div className="font-heading text-[9.5px] font-bold text-[#8b949e] uppercase tracking-wider mb-1.5">
              Feature Stability Matrix (30 Features)
            </div>
            <div className="grid grid-cols-6 sm:grid-cols-10 gap-1 bg-[#090b0e] border border-[#21262d] rounded-[2px] p-2">
              {sortedFeatures.map((feat) => {
                const isCrit = feat.severity.toLowerCase() === 'critical';
                const isWarn = feat.severity.toLowerCase() === 'moderate';
                const cellBg = isCrit
                  ? 'bg-[#F85149] text-[#0d1117]'
                  : isWarn
                  ? 'bg-[#D29922] text-[#0d1117]'
                  : 'bg-[#161b22] text-[#8b949e] border border-[#21262d]';

                return (
                  <div
                    key={feat.feature_name}
                    title={`${feat.feature_name}\nPSI: ${feat.psi_score.toFixed(4)}\nKS: ${feat.ks_statistic.toFixed(4)} (p=${feat.ks_pvalue.toExponential(2)})\nSeverity: ${feat.severity.toUpperCase()}`}
                    className={`h-7 px-1 rounded-[1px] flex flex-col justify-center items-center text-[8px] font-mono cursor-pointer transition-transform hover:scale-105 select-none ${cellBg}`}
                  >
                    <span className="truncate w-full text-center font-semibold">
                      {feat.feature_name.slice(0, 7)}
                    </span>
                    <span className="text-[7.5px] opacity-80">{feat.psi_score.toFixed(2)}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top Drifted Features Monospace Table */}
          <div>
            <div className="font-heading text-[9.5px] font-bold text-[#8b949e] uppercase tracking-wider mb-1.5">
              Top Drifted Features (Ranked by Population Stability Index)
            </div>
            <div className="border border-[#21262d] rounded-[2px] overflow-hidden overflow-x-auto">
              <table className="w-full border-collapse text-left font-mono text-[10px]">
                <thead className="bg-[#161b22] text-[#8b949e] font-medium text-[9px] uppercase tracking-wider border-b border-[#21262d]">
                  <tr>
                    <th className="py-1 px-3">FEATURE NAME</th>
                    <th className="py-1 px-3">PSI SCORE</th>
                    <th className="py-1 px-3">KS STATISTIC</th>
                    <th className="py-1 px-3">KS P-VALUE</th>
                    <th className="py-1 px-3">SEVERITY</th>
                    <th className="py-1 px-3">DISTRIBUTION ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#161b22] bg-[#0d1117]">
                  {sortedFeatures.slice(0, 8).map((feat) => {
                    const isCrit = feat.severity.toLowerCase() === 'critical';
                    const isWarn = feat.severity.toLowerCase() === 'moderate';

                    return (
                      <tr key={feat.feature_name} className="hover:bg-[#161b22] whitespace-nowrap">
                        <td className="py-1 px-3 text-[#e6edf3] font-medium">{feat.feature_name}</td>
                        <td className="py-1 px-3 text-[#e6edf3]">{feat.psi_score.toFixed(4)}</td>
                        <td className="py-1 px-3 text-[#e6edf3]">{feat.ks_statistic.toFixed(4)}</td>
                        <td className="py-1 px-3 text-[#8b949e]">{feat.ks_pvalue.toExponential(2)}</td>
                        <td className="py-1 px-3">
                          {isCrit ? (
                            <span className="badge-critical">CRITICAL</span>
                          ) : isWarn ? (
                            <span className="badge-warning">MODERATE</span>
                          ) : (
                            <span className="badge-secure">NOMINAL</span>
                          )}
                        </td>
                        <td className="py-1 px-3 font-semibold">
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
