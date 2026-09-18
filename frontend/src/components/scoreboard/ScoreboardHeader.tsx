import React from 'react';
import { Sparkles, AlertCircle, AlertTriangle, Network, Cpu, Activity, Compass, GitGraph, Zap, Database } from 'lucide-react';
import type { DriftStatusResponse } from '@/lib/types';

export type AppRoute = '/overview' | '/topology' | '/adversarial' | '/drift';

interface ScoreboardHeaderProps {
  criticalCount: number;
  anomalyCount: number;
  pivotCount: number;
  totalFlows: number;
  drift: DriftStatusResponse | null;
  threatScore: number; // 0 to 100
  showHero: boolean;
  onToggleHero: () => void;
  activeRoute: AppRoute;
  onRouteChange: (route: AppRoute) => void;
}

export const ScoreboardHeader: React.FC<ScoreboardHeaderProps> = ({
  criticalCount,
  anomalyCount,
  pivotCount,
  totalFlows,
  drift,
  threatScore,
  showHero,
  onToggleHero,
  activeRoute,
  onRouteChange,
}) => {
  const isDrifted = drift?.retraining_recommended ?? false;
  const driftRatio = drift ? `${(drift.drift_feature_ratio * 100).toFixed(0)}%` : '0%';

  // Threat gauge color - intentional severity scale
  const threatColor =
    threatScore >= 60 ? '#f85149' : threatScore >= 25 ? '#d29922' : '#3fb950';

  const navItems: { route: AppRoute; label: string; icon: React.ReactNode; badge?: string | number }[] = [
    { route: '/overview', label: 'Overview', icon: <Compass className="w-3.5 h-3.5" />, badge: totalFlows },
    { route: '/topology', label: 'Network Topology', icon: <GitGraph className="w-3.5 h-3.5" />, badge: pivotCount ? `${pivotCount} pivots` : undefined },
    { route: '/adversarial', label: 'Adversarial Lab', icon: <Zap className="w-3.5 h-3.5" /> },
    { route: '/drift', label: 'Drift Observatory', icon: <Database className="w-3.5 h-3.5" />, badge: isDrifted ? 'Drift Alert' : 'Stable' },
  ];

  return (
    <header className="shrink-0 bg-[#060c14] border-b border-[#1f2937] flex flex-col z-30 select-none shadow-md">
      {/* Top Bar: Brand, Scoreboard, and Threat Strip */}
      <div className="px-4 py-2.5 flex items-center justify-between gap-4">
        {/* Brand / Logo */}
        <div className="flex items-center gap-3">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-heading text-lg font-black tracking-wider text-[#38bdf8] drop-shadow-[0_0_12px_rgba(56,189,248,0.35)]">
                SENTINELNET
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800 font-semibold tracking-wider">
                SOC v1.0
              </span>
            </div>
            <span className="text-[11px] font-mono text-slate-400 tracking-wider uppercase">
              Autonomous Cyber-Physical Defense Matrix
            </span>
          </div>
        </div>

        {/* Live Scoreboard Stats Strip (CyberWatch Reference Pattern) */}
        <div className="hidden md:flex items-center gap-6 font-mono">
          {/* Critical Alerts */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-red-950/60 border border-red-900/60 flex items-center justify-center">
              <AlertCircle className="w-4 h-4 text-[#f85149]" />
            </div>
            <div>
              <div className="font-heading text-lg font-extrabold leading-none text-[#f85149]">
                {criticalCount}
              </div>
              <div className="text-[10px] text-slate-400 font-sans uppercase tracking-wider font-semibold">
                Critical
              </div>
            </div>
          </div>

          {/* Active Anomalies */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-amber-950/60 border border-amber-900/60 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-[#d29922]" />
            </div>
            <div>
              <div className="font-heading text-lg font-extrabold leading-none text-[#d29922]">
                {anomalyCount}
              </div>
              <div className="text-[10px] text-slate-400 font-sans uppercase tracking-wider font-semibold">
                Anomalies
              </div>
            </div>
          </div>

          {/* Compromised Pivots */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-purple-950/60 border border-purple-900/60 flex items-center justify-center">
              <Network className="w-4 h-4 text-[#bc8cff]" />
            </div>
            <div>
              <div className="font-heading text-lg font-extrabold leading-none text-[#bc8cff]">
                {pivotCount}
              </div>
              <div className="text-[10px] text-slate-400 font-sans uppercase tracking-wider font-semibold">
                Pivot Hosts
              </div>
            </div>
          </div>

          {/* Flows Scored */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-sky-950/60 border border-sky-900/60 flex items-center justify-center">
              <Cpu className="w-4 h-4 text-[#38bdf8]" />
            </div>
            <div>
              <div className="font-heading text-lg font-extrabold leading-none text-[#38bdf8]">
                {totalFlows}
              </div>
              <div className="text-[10px] text-slate-400 font-sans uppercase tracking-wider font-semibold">
                Flows Synced
              </div>
            </div>
          </div>

          {/* Drift Status */}
          <div className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded flex items-center justify-center border ${
              isDrifted ? 'bg-red-950/60 border-red-900/60' : 'bg-emerald-950/60 border-emerald-900/60'
            }`}>
              <Activity className={`w-4 h-4 ${isDrifted ? 'text-[#f85149]' : 'text-[#3fb950]'}`} />
            </div>
            <div>
              <div className={`font-mono text-xs font-bold leading-tight ${isDrifted ? 'text-[#f85149]' : 'text-[#3fb950]'}`}>
                {isDrifted ? `ALERT (${driftRatio})` : 'NOMINAL'}
              </div>
              <div className="text-[10px] text-slate-400 font-sans uppercase tracking-wider font-semibold">
                MLOps Stability
              </div>
            </div>
          </div>
        </div>

        {/* Right Controls: Threat Meter & Mission Brief Toggle */}
        <div className="flex items-center gap-3">
          {/* Threat Gauge Meter */}
          <div className="flex items-center gap-2 font-sans text-xs text-slate-300">
            <span className="font-semibold uppercase tracking-wider text-[11px] text-slate-400">THREAT:</span>
            <div className="w-20 h-2.5 bg-slate-900 border border-slate-700 rounded-full overflow-hidden p-0.5">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${threatScore}%`,
                  backgroundColor: threatColor,
                  boxShadow: `0 0 8px ${threatColor}`,
                }}
              />
            </div>
            <span className="font-mono font-bold text-xs min-w-[32px] text-right" style={{ color: threatColor }}>
              {threatScore}%
            </span>
          </div>

          {/* Mission Brief Toggle */}
          <button
            type="button"
            onClick={onToggleHero}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-sans font-semibold transition-all cursor-pointer border ${
              showHero
                ? 'bg-sky-500/20 text-sky-400 border-sky-500/60 shadow-[0_0_10px_rgba(56,189,248,0.25)]'
                : 'bg-slate-900 text-slate-400 border-slate-700 hover:border-sky-500/50 hover:text-sky-300'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            <span>{showHero ? 'Close Brief' : 'Mission Brief'}</span>
          </button>
        </div>
      </div>

      {/* Navigation Route Bar */}
      <div className="bg-[#090e17] border-t border-[#1f2937] px-4 py-1.5 flex items-center justify-between gap-2 overflow-x-auto">
        <nav className="flex items-center gap-1.5">
          {navItems.map((item) => {
            const isActive = activeRoute === item.route;
            return (
              <button
                key={item.route}
                type="button"
                onClick={() => onRouteChange(item.route)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md font-sans text-xs font-semibold tracking-wide transition-all cursor-pointer whitespace-nowrap border ${
                  isActive
                    ? 'bg-sky-500/15 text-sky-400 border-sky-500/50 shadow-[0_0_12px_rgba(56,189,248,0.15)]'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border-transparent'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
                {item.badge !== undefined && (
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full font-bold ${
                      isActive
                        ? 'bg-sky-400 text-slate-950'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>AIR-GAPPED SOC // ARMED</span>
        </div>
      </div>
    </header>
  );
};
