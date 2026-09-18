import React from 'react';
import { Sparkles, AlertCircle, AlertTriangle, Network, Cpu } from 'lucide-react';
import type { DriftStatusResponse } from '@/lib/types';

interface ScoreboardHeaderProps {
  criticalCount: number;
  anomalyCount: number;
  pivotCount: number;
  totalFlows: number;
  drift: DriftStatusResponse | null;
  threatScore: number; // 0 to 100
  showHero: boolean;
  onToggleHero: () => void;
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
}) => {
  const isDrifted = drift?.retraining_recommended ?? false;
  const driftRatio = drift ? `${(drift.drift_feature_ratio * 100).toFixed(0)}%` : '0%';

  // Threat gauge color
  const threatColor =
    threatScore >= 60 ? '#f85149' : threatScore >= 25 ? '#d29922' : '#3fb950';

  return (
    <header className="shrink-0 bg-[#060c14] border-b border-[#1b2738] px-4 py-2 flex items-center justify-between z-30 select-none">
      {/* Brand / Logo */}
      <div className="flex items-center gap-3">
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="font-heading text-[15px] font-black tracking-[0.2em] text-[#58a6ff] drop-shadow-[0_0_12px_rgba(88,166,255,0.4)]">
              SENTINELNET
            </span>
            <span className="text-[8px] font-mono px-1.5 py-0.5 rounded-[2px] bg-[#162b47] text-[#58a6ff] border border-[#23426e] tracking-wider">
              v1.0-SOC
            </span>
          </div>
          <span className="text-[8px] font-mono text-[#527194] tracking-[0.16em] uppercase">
            // MULTI-TIER REAL-TIME DEFENSE MATRIX · AIR-GAPPED
          </span>
        </div>
      </div>

      {/* Vertical Divider */}
      <div className="hidden md:block w-px h-8 bg-[#162b47] mx-2" />

      {/* Live Scoreboard Stats Strip (CyberWatch Reference Pattern) */}
      <div className="flex items-center gap-4 sm:gap-6 font-mono">
        {/* Critical Alerts */}
        <div className="text-center group cursor-default">
          <div className="font-heading text-lg sm:text-xl font-extrabold leading-none text-[#f85149] drop-shadow-[0_0_8px_rgba(248,81,73,0.35)]">
            {criticalCount}
          </div>
          <div className="text-[7px] text-[#527194] tracking-[0.18em] font-semibold mt-0.5 flex items-center justify-center gap-1">
            <AlertCircle className="w-2.5 h-2.5 text-[#f85149]" />
            <span>CRITICAL</span>
          </div>
        </div>

        {/* High Risk / Active Anomalies */}
        <div className="text-center group cursor-default">
          <div className="font-heading text-lg sm:text-xl font-extrabold leading-none text-[#d29922]">
            {anomalyCount}
          </div>
          <div className="text-[7px] text-[#527194] tracking-[0.18em] font-semibold mt-0.5 flex items-center justify-center gap-1">
            <AlertTriangle className="w-2.5 h-2.5 text-[#d29922]" />
            <span>ANOMALIES</span>
          </div>
        </div>

        {/* Compromised Lateral Pivots */}
        <div className="text-center group cursor-default">
          <div className="font-heading text-lg sm:text-xl font-extrabold leading-none text-[#bc8cff] drop-shadow-[0_0_8px_rgba(188,140,255,0.3)]">
            {pivotCount}
          </div>
          <div className="text-[7px] text-[#527194] tracking-[0.18em] font-semibold mt-0.5 flex items-center justify-center gap-1">
            <Network className="w-2.5 h-2.5 text-[#bc8cff]" />
            <span>PIVOT HOSTS</span>
          </div>
        </div>

        {/* Flows Scored */}
        <div className="text-center group cursor-default">
          <div className="font-heading text-lg sm:text-xl font-extrabold leading-none text-[#58a6ff]">
            {totalFlows}
          </div>
          <div className="text-[7px] text-[#527194] tracking-[0.18em] font-semibold mt-0.5 flex items-center justify-center gap-1">
            <Cpu className="w-2.5 h-2.5 text-[#58a6ff]" />
            <span>FLOWS SCORED</span>
          </div>
        </div>

        {/* Drift Status Pill */}
        <div className="hidden lg:flex flex-col items-center justify-center">
          <div
            className={`font-mono text-[11px] font-bold px-2 py-0.5 rounded-[2px] border ${
              isDrifted
                ? 'bg-[#f85149]/10 text-[#f85149] border-[#f85149]/40'
                : 'bg-[#3fb950]/10 text-[#3fb950] border-[#3fb950]/40'
            }`}
          >
            {isDrifted ? `DRIFT ${driftRatio}` : `DRIFT NOMINAL`}
          </div>
          <div className="text-[7px] text-[#527194] tracking-[0.18em] font-semibold mt-0.5">
            MLOPS STABILITY
          </div>
        </div>
      </div>

      {/* Vertical Divider */}
      <div className="hidden md:block w-px h-8 bg-[#162b47] mx-2" />

      {/* Right Controls: Threat Meter & Mission Brief Toggle */}
      <div className="flex items-center gap-4">
        {/* Threat Gauge Meter */}
        <div className="hidden sm:flex items-center gap-2 font-mono text-[8px] text-[#527194] tracking-wider">
          <span className="font-semibold uppercase">THREAT LEVEL</span>
          <div className="w-16 h-2 bg-[#0a1422] border border-[#162b47] rounded-[2px] overflow-hidden">
            <div
              className="h-full transition-all duration-700 rounded-[1px]"
              style={{
                width: `${threatScore}%`,
                backgroundColor: threatColor,
                boxShadow: `0 0 6px ${threatColor}`,
              }}
            />
          </div>
          <span className="font-bold text-[#e6edf3] min-w-[28px] text-right">
            {threatScore}%
          </span>
        </div>

        {/* Mission Brief / Hero Toggle Button */}
        <button
          onClick={onToggleHero}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-[2px] font-mono text-[9px] tracking-wider border transition-all cursor-pointer ${
            showHero
              ? 'bg-[#58a6ff]/20 text-[#58a6ff] border-[#58a6ff]/60 shadow-[0_0_8px_rgba(88,166,255,0.2)]'
              : 'bg-[#0a1422] text-[#8b949e] border-[#162b47] hover:border-[#58a6ff] hover:text-[#58a6ff]'
          }`}
          title="Toggle Context & Architecture Hero Brief"
        >
          <Sparkles className="w-3 h-3 text-[#58a6ff]" />
          <span>{showHero ? 'CLOSE BRIEF' : 'MISSION BRIEF'}</span>
        </button>

        {/* Live Sentinel Heartbeat */}
        <div className="flex items-center gap-1.5 px-2 py-1 rounded-[2px] bg-[#3fb950]/10 border border-[#3fb950]/30 font-mono text-[8px] text-[#3fb950] tracking-wider">
          <span className="w-2 h-2 rounded-full bg-[#3fb950] animate-ping" />
          <span className="font-bold">DEFENSE ARMED</span>
        </div>
      </div>
    </header>
  );
};
