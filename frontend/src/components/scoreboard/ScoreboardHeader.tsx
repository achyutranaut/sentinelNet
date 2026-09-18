import React from 'react';
import {
  Sparkles,
  AlertCircle,
  AlertTriangle,
  Network,
  Cpu,
  Activity,
  Compass,
  GitGraph,
  Zap,
  Database,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';
import type { DriftStatusResponse, HealthResponse, TelemetryMetrics } from '@/lib/types';

export type AppRoute = '/overview' | '/topology' | '/adversarial' | '/drift';

export interface ScoreboardHeaderProps {
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
  health?: HealthResponse | null;
  metrics?: TelemetryMetrics | null;
  wsStatus?: 'connected' | 'disconnected' | 'connecting';
  isSidebarOpen?: boolean;
  onToggleSidebar?: () => void;
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
  health,
  metrics,
  wsStatus = 'connected',
  isSidebarOpen = true,
  onToggleSidebar,
}) => {
  const isDrifted = drift?.retraining_recommended ?? false;
  const driftRatio = drift ? `${(drift.drift_feature_ratio * 100).toFixed(0)}%` : '0%';

  const sha = (health?.dataset_hash || '99d9bece').slice(0, 8);
  const p95Latency = metrics?.latency_p95_ms ?? 0.42;

  // Threat gauge color - intentional severity scale
  const threatColor =
    threatScore >= 60 ? '#f85149' : threatScore >= 25 ? '#d29922' : '#3fb950';

  const navItems: {
    route: AppRoute;
    label: string;
    icon: React.ReactNode;
    badge?: string | number;
    badgeType?: 'count' | 'danger' | 'purple' | 'success';
  }[] = [
    {
      route: '/overview',
      label: 'Overview',
      icon: <Compass className="w-4 h-4" />,
      badge: totalFlows > 0 ? totalFlows : undefined,
      badgeType: 'count',
    },
    {
      route: '/topology',
      label: 'Network Topology',
      icon: <GitGraph className="w-4 h-4" />,
      badge: pivotCount > 0 ? `${pivotCount} pivots` : undefined,
      badgeType: 'purple',
    },
    {
      route: '/adversarial',
      label: 'Adversarial Lab',
      icon: <Zap className="w-4 h-4" />,
    },
    {
      route: '/drift',
      label: 'Drift Observatory',
      icon: <Database className="w-4 h-4" />,
      badge: isDrifted ? 'Drift Alert' : 'Stable',
      badgeType: isDrifted ? 'danger' : 'success',
    },
  ];

  return (
    <header className="shrink-0 bg-[#060c14] border-b border-[#1f2937] flex flex-col z-30 select-none shadow-md">
      {/* Tier 1 Bar: Brand Logo, Mission Status & Compact Scoreboard KPIs (<44px) */}
      <div className="px-4 py-1.5 flex items-center justify-between gap-3 min-h-[42px]">
        {/* Brand / Logo + Mission Badge */}
        <div className="flex items-center gap-2.5 shrink-0">
          <div className="flex items-center gap-2">
            <span className="font-heading text-base font-black tracking-wider text-[#38bdf8] drop-shadow-[0_0_12px_rgba(56,189,248,0.35)]">
              SENTINEL.NET
            </span>
            <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800 font-semibold tracking-wider">
              SOC COMMAND
            </span>
            <span className="hidden xl:inline text-[11px] font-mono text-slate-400 tracking-wider uppercase">
              // AIR-GAPPED MATRIX
            </span>
          </div>
        </div>

        {/* Live Scoreboard Quick-Status KPIs */}
        <div className="hidden md:flex items-center gap-2 font-mono flex-wrap justify-center">
          {/* Critical Alerts */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#161b22] border border-[#21262d]">
            <AlertCircle className="w-3.5 h-3.5 text-[#f85149] shrink-0" />
            <span className="font-mono text-xs font-bold text-[#f85149] tabular-nums">
              {criticalCount}
            </span>
            <span className="text-[10px] text-slate-400 font-heading uppercase tracking-wider font-semibold">
              CRITICAL
            </span>
          </div>

          {/* Active Anomalies */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#161b22] border border-[#21262d]">
            <AlertTriangle className="w-3.5 h-3.5 text-[#d29922] shrink-0" />
            <span className="font-mono text-xs font-bold text-[#d29922] tabular-nums">
              {anomalyCount}
            </span>
            <span className="text-[10px] text-slate-400 font-heading uppercase tracking-wider font-semibold">
              ANOMALIES
            </span>
          </div>

          {/* Compromised Hosts / Pivots */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#161b22] border border-[#21262d]">
            <Network className="w-3.5 h-3.5 text-[#bc8cff] shrink-0" />
            <span className="font-mono text-xs font-bold text-[#bc8cff] tabular-nums">
              {pivotCount}
            </span>
            <span className="text-[10px] text-slate-400 font-heading uppercase tracking-wider font-semibold">
              HOSTS
            </span>
          </div>

          {/* Synced Flows */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#161b22] border border-[#21262d]">
            <Cpu className="w-3.5 h-3.5 text-[#38bdf8] shrink-0" />
            <span className="font-mono text-xs font-bold text-[#38bdf8] tabular-nums">
              {totalFlows}
            </span>
            <span className="text-[10px] text-slate-400 font-heading uppercase tracking-wider font-semibold">
              SYNCED
            </span>
          </div>

          {/* Drift Status */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#161b22] border border-[#21262d]">
            <Activity className={`w-3.5 h-3.5 shrink-0 ${isDrifted ? 'text-[#f85149]' : 'text-[#3fb950]'}`} />
            <span className={`font-mono text-xs font-bold tabular-nums ${isDrifted ? 'text-[#f85149]' : 'text-[#3fb950]'}`}>
              {isDrifted ? `DRIFT (${driftRatio})` : 'NOMINAL'}
            </span>
            <span className="text-[10px] text-slate-400 font-heading uppercase tracking-wider font-semibold">
              STABILITY
            </span>
          </div>
        </div>

        {/* Right Controls: Threat Meter & Mission Brief Toggle */}
        <div className="flex items-center gap-2.5 shrink-0">
          {/* Threat Gauge Meter */}
          <div className="flex items-center gap-2 font-sans text-xs text-slate-300 bg-[#161b22] px-2.5 py-1 rounded border border-[#21262d]">
            <span className="font-semibold uppercase tracking-wider text-[11px] text-slate-400">THREAT:</span>
            <div className="w-16 h-2 bg-slate-900 border border-slate-700 rounded-full overflow-hidden p-0.5">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${threatScore}%`,
                  backgroundColor: threatColor,
                  boxShadow: `0 0 8px ${threatColor}`,
                }}
              />
            </div>
            <span className="font-mono font-bold text-xs tabular-nums min-w-[28px] text-right" style={{ color: threatColor }}>
              {threatScore}%
            </span>
          </div>

          {/* Mission Brief Toggle */}
          <button
            type="button"
            onClick={onToggleHero}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-sans font-semibold transition-all cursor-pointer border ${
              showHero
                ? 'bg-sky-500/20 text-sky-400 border-sky-500/60 shadow-[0_0_10px_rgba(56,189,248,0.25)]'
                : 'bg-slate-900 text-slate-400 border-slate-700 hover:border-sky-500/50 hover:text-sky-300'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            <span>{showHero ? 'Close' : 'Mission Brief'}</span>
          </button>
        </div>
      </div>

      {/* Tier 2 Bar: Controls Toggle, Tab Navigation & Streamlined Model Telemetry (<40px) */}
      <div className="bg-[#090e17] border-t border-[#1f2937] px-4 py-1 flex items-center justify-between gap-3 overflow-x-auto min-h-[38px]">
        {/* Left Side: Controls Sidebar Toggle + Tab Navigation */}
        <div className="flex items-center gap-2">
          {onToggleSidebar && (
            <button
              type="button"
              onClick={onToggleSidebar}
              title={isSidebarOpen ? 'Collapse Controls Sidebar' : 'Expand Controls Sidebar'}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] text-xs font-mono text-slate-300 hover:text-white transition-colors shrink-0 cursor-pointer select-none"
            >
              {isSidebarOpen ? (
                <PanelLeftClose className="w-3.5 h-3.5 text-[#38bdf8]" />
              ) : (
                <PanelLeftOpen className="w-3.5 h-3.5 text-[#38bdf8]" />
              )}
              <span className="hidden sm:inline text-[11px] font-semibold tracking-wider uppercase">
                {isSidebarOpen ? 'CONTROLS' : 'EXPAND'}
              </span>
            </button>
          )}

          <nav className="flex items-center gap-1.5">
            {navItems.map((item) => {
              const isActive = activeRoute === item.route;
              return (
                <button
                  key={item.route}
                  type="button"
                  onClick={() => onRouteChange(item.route)}
                  className={`flex items-center gap-2 px-3 py-1 min-h-[30px] rounded font-sans text-xs font-semibold tracking-wide transition-all duration-150 cursor-pointer whitespace-nowrap border select-none ${
                    isActive
                      ? 'bg-[#0c2438] text-[#38bdf8] border-[#38bdf8] shadow-[0_0_12px_rgba(56,189,248,0.2)]'
                      : 'bg-[#101722] text-slate-300 border-[#222e40] hover:bg-[#182230] hover:text-white hover:border-slate-500'
                  }`}
                >
                  {item.icon}
                  <span className="font-heading uppercase text-xs tracking-wider">{item.label}</span>
                  {item.badge !== undefined && (
                    <span
                      className={`ml-1 px-1.5 py-0.2 rounded-full text-[11px] font-mono font-bold tracking-tight inline-flex items-center justify-center border shadow-xs ${
                        item.badgeType === 'danger'
                          ? 'bg-red-950 text-red-300 border-red-700/80 animate-pulse'
                          : item.badgeType === 'purple'
                          ? 'bg-purple-950 text-purple-300 border-purple-700/80'
                          : item.badgeType === 'success'
                          ? 'bg-emerald-950 text-emerald-300 border-emerald-700/80'
                          : isActive
                          ? 'bg-sky-400 text-slate-950 border-sky-300'
                          : 'bg-[#1e293b] text-sky-300 border-[#334155]'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Right Side: Merged Model Badge Telemetry */}
        <div className="hidden lg:flex items-center gap-2 font-mono text-xs text-slate-300 shrink-0">
          {/* Model Badge */}
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#161b22] border border-[#21262d]">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">MODEL:</span>
            <span className="text-[#38bdf8] font-bold">SENTINEL-E2E-X</span>
            <span className="text-slate-500">|</span>
            <span className="text-emerald-400 font-bold tabular-nums">96.7%</span>
            <span className="text-slate-500 text-[10px] font-mono tabular-nums">(SHA:{sha})</span>
          </div>

          {/* Inference SLA */}
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#161b22] border border-[#21262d]">
            <span className="text-[11px] text-slate-400 uppercase font-semibold">INFERENCE NLA:</span>
            <span className={p95Latency <= 1.5 ? 'text-[#3fb950] font-bold tabular-nums' : 'text-[#f85149] font-bold tabular-nums'}>
              {p95Latency.toFixed(2)}ms
            </span>
            <span className="text-[10px] text-slate-500 font-semibold">[&lt; 1.5ms]</span>
          </div>

          {/* Stream Status */}
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#161b22] border border-[#21262d]">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                wsStatus === 'connected'
                  ? 'bg-[#3fb950] animate-pulse'
                  : wsStatus === 'connecting'
                  ? 'bg-[#d29922]'
                  : 'bg-[#f85149]'
              }`}
            />
            <span className="text-[11px] text-slate-400 uppercase font-semibold">STREAM:</span>
            <span className="font-bold text-slate-200 text-[11px]">{wsStatus.toUpperCase()}</span>
          </div>

          <span className="hidden xl:inline text-xs font-mono font-bold text-[#3fb950] tracking-wider">
            [ARMED]
          </span>
        </div>
      </div>
    </header>
  );
};
