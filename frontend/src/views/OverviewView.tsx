import React, { useState } from 'react';
import { AlertCircle, AlertTriangle, Network, Activity, ArrowRight, Eye, X } from 'lucide-react';
import type { AlertStreamItem, DriftStatusResponse, GraphStateResponse } from '@/lib/types';
import { LiveAlertStream } from '@/components/alerts/LiveAlertStream';
import { TreeShapInspector } from '@/components/explainability/TreeShapInspector';

interface OverviewViewProps {
  alerts: AlertStreamItem[];
  selectedAlert: AlertStreamItem | null;
  onSelectAlert: (alert: AlertStreamItem) => void;
  graphState: GraphStateResponse | null;
  drift: DriftStatusResponse | null;
  threatScore: number;
  onNavigate: (route: '/overview' | '/topology' | '/adversarial' | '/drift') => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  alerts,
  selectedAlert,
  onSelectAlert,
  graphState,
  drift,
  threatScore,
  onNavigate,
}) => {
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const criticalCount = alerts.filter((a) => a.is_attack || a.supervised_probability >= 0.5).length;
  const anomalyCount = alerts.filter(
    (a) => !a.is_attack && (a.reconstruction_loss >= 0.8 || a.supervised_probability >= 0.15)
  ).length;
  const pivotCount =
    graphState?.flagged_pivots?.length ||
    graphState?.nodes?.filter((n) => n.is_pivot)?.length ||
    0;
  const isDrifted = drift?.retraining_recommended ?? false;
  const driftRatio = drift ? `${(drift.drift_feature_ratio * 100).toFixed(0)}%` : '0%';

  const threatColor =
    threatScore >= 60 ? '#f85149' : threatScore >= 25 ? '#d29922' : '#3fb950';

  return (
    <div className="space-y-4 flex flex-col">
      {/* 1. Large Glanceable KPI Stat Cards Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
        {/* Threat Level */}
        <div className="stat-card flex flex-col justify-between p-4">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              System Threat Gauge
            </span>
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: threatColor }} />
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono tabular-nums" style={{ color: threatColor }}>
              {threatScore}%
            </span>
            <span className="text-xs font-mono text-slate-400">
              {threatScore >= 60 ? 'CRITICAL RISK' : threatScore >= 25 ? 'ELEVATED' : 'NOMINAL'}
            </span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-2.5">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${threatScore}%`, backgroundColor: threatColor }}
            />
          </div>
        </div>

        {/* Critical Alerts */}
        <div className="stat-card flex flex-col justify-between p-4">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Critical Attacks
            </span>
            <div className="w-7 h-7 rounded bg-red-950/60 border border-red-800/40 flex items-center justify-center">
              <AlertCircle className="w-4 h-4 text-[#f85149]" />
            </div>
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-[#f85149] tabular-nums">
              {criticalCount}
            </span>
            <span className="text-xs font-mono text-slate-400">flagged flows</span>
          </div>
          <div className="text-xs text-slate-400 mt-1.5 font-sans">
            Tier 1 & Tier 2 combined triggers
          </div>
        </div>

        {/* Active Anomalies */}
        <div className="stat-card flex flex-col justify-between p-4">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Active Anomalies
            </span>
            <div className="w-7 h-7 rounded bg-amber-950/60 border border-amber-800/40 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-[#d29922]" />
            </div>
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-[#d29922] tabular-nums">
              {anomalyCount}
            </span>
            <span className="text-xs font-mono text-slate-400">elevated</span>
          </div>
          <div className="text-xs text-slate-400 mt-1.5 font-sans">
            Autoencoder MSE &gt; cutoff
          </div>
        </div>

        {/* Compromised Pivots */}
        <div
          onClick={() => onNavigate('/topology')}
          className="stat-card flex flex-col justify-between p-4 cursor-pointer hover:border-purple-500/50 group"
        >
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider group-hover:text-purple-400 transition-colors">
              Pivot Hosts
            </span>
            <div className="w-7 h-7 rounded bg-purple-950/60 border border-purple-800/40 flex items-center justify-center">
              <Network className="w-4 h-4 text-[#bc8cff]" />
            </div>
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-[#bc8cff] tabular-nums">
              {pivotCount}
            </span>
            <span className="text-xs font-mono text-slate-400">infected</span>
          </div>
          <div className="text-xs text-purple-400 font-sans flex items-center gap-1 mt-1.5">
            <span>Inspect in Topology</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Drift Status */}
        <div
          onClick={() => onNavigate('/drift')}
          className="stat-card flex flex-col justify-between p-4 cursor-pointer hover:border-sky-500/50 group"
        >
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider group-hover:text-sky-400 transition-colors">
              Covariate Drift
            </span>
            <div className={`w-7 h-7 rounded flex items-center justify-center ${
              isDrifted ? 'bg-red-950/60 border border-red-800/40' : 'bg-emerald-950/60 border border-emerald-800/40'
            }`}>
              <Activity className={`w-4 h-4 ${isDrifted ? 'text-[#f85149]' : 'text-[#3fb950]'}`} />
            </div>
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className={`text-3xl font-extrabold font-mono tabular-nums ${isDrifted ? 'text-[#f85149]' : 'text-[#3fb950]'}`}>
              {driftRatio}
            </span>
            <span className="text-xs font-mono text-slate-400">
              {isDrifted ? 'RETRAIN' : 'STABLE'}
            </span>
          </div>
          <div className="text-xs text-sky-400 font-sans flex items-center gap-1 mt-1.5">
            <span>View Drift Observatory</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>
      </div>

      {/* 2. Responsive Operational Workspace: Full-Width Stream + Contextual SHAP Attribution */}
      <div className="relative flex flex-1 min-h-0 gap-4">
        {/* Live Flow Stream (Primary Task: Full Width on < 1440px, balanced split on >= 1440px) */}
        <div className="flex-1 min-w-0 flex flex-col">
          <div className="mb-2 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-100 font-sans">
                Real-Time Ingestion & Scoring Stream
              </h2>
              <p className="text-xs text-slate-400 font-sans mt-0.5">
                Continuous packet flows scored via Tier 1 signatures & Tier 2 reconstruction loss
              </p>
            </div>

            <button
              type="button"
              onClick={() => setIsInspectorOpen(!isInspectorOpen)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded font-sans text-xs cursor-pointer transition-colors border shrink-0 ${
                isInspectorOpen
                  ? 'bg-sky-500/20 text-sky-400 border-sky-500/60 shadow-xs'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-600'
              }`}
            >
              <Eye className="w-3.5 h-3.5 text-sky-400" />
              <span>{isInspectorOpen ? 'Hide Attribution' : 'Attribution Dock'}</span>
              {selectedAlert && (
                <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse ml-0.5" />
              )}
            </button>
          </div>

          <LiveAlertStream
            alerts={alerts}
            selectedAlertId={selectedAlert?.alert_id ?? null}
            onSelectAlert={(alert) => {
              setIsInspectorOpen(true);
              onSelectAlert(alert);
            }}
            height={540}
          />
        </div>

        {/* TreeSHAP Contextual Slide-Over Drawer (<1440px) & Widescreen Dock (>=1440px) */}
        {isInspectorOpen && (
          <>
            {/* Backdrop Blur on screens < 1440px */}
            <div
              className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 2xl:hidden"
              onClick={() => setIsInspectorOpen(false)}
            />

            <div className="fixed top-0 right-0 h-full w-[440px] max-w-[90vw] z-50 bg-[#0d1117]/95 backdrop-blur-md border-l border-[#1f2937] p-4 flex flex-col shadow-2xl overflow-y-auto 2xl:relative 2xl:top-auto 2xl:right-auto 2xl:h-auto 2xl:w-[420px] 2xl:max-w-none 2xl:z-auto 2xl:bg-[#0d1117] 2xl:border 2xl:border-[#1f2937] 2xl:rounded-lg 2xl:shadow-sm 2xl:backdrop-blur-none shrink-0">
              <div className="flex items-center justify-between pb-2.5 border-b border-slate-800 mb-3">
                <div className="flex items-center gap-2">
                  <Eye className="w-4 h-4 text-sky-400" />
                  <span className="text-sm font-bold text-slate-200 font-heading">
                    TreeSHAP Incident Attribution
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setIsInspectorOpen(false)}
                  title="Close Inspector"
                  className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-[#161b22] cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <p className="text-xs text-slate-400 font-sans mb-3">
                {selectedAlert
                  ? `Flow ${selectedAlert.alert_id} | ${selectedAlert.src_ip} -> ${selectedAlert.dst_ip}:${selectedAlert.dst_port}`
                  : 'Select any flow in the real-time stream to inspect exact feature attribution waterfall.'}
              </p>
              <TreeShapInspector
                explanation={selectedAlert?.explanation ?? null}
                alertId={selectedAlert?.alert_id}
                targetEntity={
                  selectedAlert
                    ? `${selectedAlert.src_ip} (${selectedAlert.attack_type || 'FLOW'})`
                    : undefined
                }
                height={540}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
};
