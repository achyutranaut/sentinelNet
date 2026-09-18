import React from 'react';
import { AlertCircle, AlertTriangle, Network, Activity, ArrowRight } from 'lucide-react';
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
    <div className="space-y-6">
      {/* 1. Large Glanceable KPI Stat Cards Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Threat Level */}
        <div className="stat-card flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              System Threat Gauge
            </span>
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: threatColor }} />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono" style={{ color: threatColor }}>
              {threatScore}%
            </span>
            <span className="text-xs font-mono text-slate-400">
              {threatScore >= 60 ? 'CRITICAL RISK' : threatScore >= 25 ? 'ELEVATED' : 'NOMINAL'}
            </span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-3">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${threatScore}%`, backgroundColor: threatColor }}
            />
          </div>
        </div>

        {/* Critical Alerts */}
        <div className="stat-card flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Critical Attacks
            </span>
            <div className="w-6 h-6 rounded bg-red-950/60 border border-red-800/40 flex items-center justify-center">
              <AlertCircle className="w-3.5 h-3.5 text-[#f85149]" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-[#f85149]">
              {criticalCount}
            </span>
            <span className="text-xs font-mono text-slate-400">flagged flows</span>
          </div>
          <div className="text-xs text-slate-400 mt-2 font-sans">
            Tier 1 & Tier 2 combined triggers
          </div>
        </div>

        {/* Active Anomalies */}
        <div className="stat-card flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Active Anomalies
            </span>
            <div className="w-6 h-6 rounded bg-amber-950/60 border border-amber-800/40 flex items-center justify-center">
              <AlertTriangle className="w-3.5 h-3.5 text-[#d29922]" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-[#d29922]">
              {anomalyCount}
            </span>
            <span className="text-xs font-mono text-slate-400">elevated</span>
          </div>
          <div className="text-xs text-slate-400 mt-2 font-sans">
            Autoencoder MSE &gt; cutoff
          </div>
        </div>

        {/* Compromised Pivots */}
        <div
          onClick={() => onNavigate('/topology')}
          className="stat-card flex flex-col justify-between cursor-pointer hover:border-purple-500/50 group"
        >
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider group-hover:text-purple-400 transition-colors">
              Pivot Hosts
            </span>
            <div className="w-6 h-6 rounded bg-purple-950/60 border border-purple-800/40 flex items-center justify-center">
              <Network className="w-3.5 h-3.5 text-[#bc8cff]" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-[#bc8cff]">
              {pivotCount}
            </span>
            <span className="text-xs font-mono text-slate-400">infected</span>
          </div>
          <div className="text-xs text-purple-400 font-sans flex items-center gap-1 mt-2">
            <span>Inspect in Topology</span>
            <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Drift Status */}
        <div
          onClick={() => onNavigate('/drift')}
          className="stat-card flex flex-col justify-between cursor-pointer hover:border-sky-500/50 group"
        >
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider group-hover:text-sky-400 transition-colors">
              Covariate Drift
            </span>
            <div className={`w-6 h-6 rounded flex items-center justify-center ${
              isDrifted ? 'bg-red-950/60 border border-red-800/40' : 'bg-emerald-950/60 border border-emerald-800/40'
            }`}>
              <Activity className={`w-3.5 h-3.5 ${isDrifted ? 'text-[#f85149]' : 'text-[#3fb950]'}`} />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className={`text-3xl font-extrabold font-mono ${isDrifted ? 'text-[#f85149]' : 'text-[#3fb950]'}`}>
              {driftRatio}
            </span>
            <span className="text-xs font-mono text-slate-400">
              {isDrifted ? 'RETRAIN' : 'STABLE'}
            </span>
          </div>
          <div className="text-xs text-sky-400 font-sans flex items-center gap-1 mt-2">
            <span>View Drift Observatory</span>
            <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>
      </div>

      {/* 2. Spacious 2-Column Operational Grid: Alert Feed + TreeSHAP Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Live Flow Stream (7 cols) */}
        <div className="lg:col-span-7 flex flex-col">
          <div className="mb-2 flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-100 font-sans">
                Real-Time Ingestion & Scoring Stream
              </h2>
              <p className="text-xs text-slate-400 font-sans mt-0.5">
                Continuous packet flows scored via Tier 1 signatures & Tier 2 reconstruction loss
              </p>
            </div>
          </div>
          <LiveAlertStream
            alerts={alerts}
            selectedAlertId={selectedAlert?.alert_id ?? null}
            onSelectAlert={onSelectAlert}
            height={520}
          />
        </div>

        {/* TreeSHAP Incident Triage (5 cols) */}
        <div className="lg:col-span-5 flex flex-col">
          <div className="mb-2 flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-100 font-sans">
                TreeSHAP Incident Attribution
              </h2>
              <p className="text-xs text-slate-400 font-sans mt-0.5">
                Exact feature attribution waterfall explaining why this flow was flagged
              </p>
            </div>
          </div>
          <TreeShapInspector
            explanation={selectedAlert?.explanation ?? null}
            alertId={selectedAlert?.alert_id}
            targetEntity={
              selectedAlert
                ? `${selectedAlert.src_ip} (${selectedAlert.attack_type || 'FLOW'})`
                : undefined
            }
            height={520}
          />
        </div>
      </div>
    </div>
  );
};
