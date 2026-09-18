import React, { useEffect } from 'react';
import anime from 'animejs';
import type { SHAPExplanationPayload } from '@/lib/types';
import { HelpCircle } from 'lucide-react';

interface TreeShapInspectorProps {
  explanation: SHAPExplanationPayload | null;
  alertId?: string;
  targetEntity?: string;
  height?: number;
}

export const TreeShapInspector: React.FC<TreeShapInspectorProps> = ({
  explanation,
  alertId,
  targetEntity,
  height = 320,
}) => {
  const drivers = explanation?.top_drivers || [];
  const prob = explanation?.predicted_probability ?? 0.0;
  const analystText = explanation?.analyst_summary || 'No flow selected for TreeSHAP incident triage.';

  // Anime.js bar width expansion and row reveal on flow selection change
  useEffect(() => {
    if (drivers.length > 0) {
      // Row entrance micro-stagger
      anime({
        targets: '.shap-row-animate',
        opacity: [0, 1],
        translateX: [-6, 0],
        duration: 100,
        delay: anime.stagger(20),
        easing: 'easeOutQuad',
      });

      // Horizontal attribution bar animation
      document.querySelectorAll('.shap-bar-fill').forEach((el) => {
        const targetWidth = el.getAttribute('data-width') || '0%';
        anime({
          targets: el,
          width: ['0%', targetWidth],
          duration: 250,
          easing: 'easeOutQuad',
        });
      });
    }
  }, [alertId, targetEntity, drivers.length]);

  // Proportional bar scaling
  let maxAbsShap = 0.001;
  drivers.forEach((d) => {
    const a = Math.abs(d.shap_attribution);
    if (a > maxAbsShap) maxAbsShap = a;
  });

  const probPct = (prob * 100).toFixed(1);
  const isCritical = prob >= 0.5;
  const isElevated = !isCritical && prob >= 0.15;

  return (
    <div
      className="shap-inspector-panel bg-[#0d1117] border border-[#21262d] rounded-lg flex flex-col overflow-hidden flex-1"
      style={height ? { minHeight: `${height}px` } : undefined}
    >
      {/* Panel Header */}
      <div className="bg-[#161b22] border-b border-[#21262d] px-3.5 py-2.5 flex justify-between items-center font-heading text-xs font-bold tracking-wider uppercase text-[#8b949e] select-none">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-[2px] bg-[#38bdf8] inline-block shadow-[0_0_8px_#38bdf8]" />
          <span className="text-[#e6edf3]">COMPONENT 03 //</span>
          <span>TREESHAP INCIDENT ATTRIBUTION (TIER 5)</span>
          {targetEntity && (
            <span className="text-[#38bdf8] font-mono text-[11px] px-2 py-0.5 rounded bg-[#162b47] border border-[#23426e] tracking-tight font-semibold">
              {targetEntity}
            </span>
          )}
        </div>

        <div>
          {explanation ? (
            <span
              className={
                isCritical
                  ? 'badge-critical'
                  : isElevated
                  ? 'badge-warning'
                  : 'badge-secure'
              }
            >
              {isCritical ? 'CRITICAL RISK' : isElevated ? 'ELEVATED' : 'BENIGN'}: {probPct}%
            </span>
          ) : (
            <span className="badge-neutral">IDLE</span>
          )}
        </div>
      </div>

      {/* SOC Analyst Brief Banner */}
      <div className="bg-[#121924] border-b border-[#21262d] border-l-4 border-l-[#38bdf8] px-3.5 py-2.5 text-xs text-slate-200 leading-relaxed font-sans">
        <span className="font-heading font-extrabold text-[#38bdf8] tracking-wider uppercase mr-2 text-xs">
          ANALYST BRIEF:
        </span>
        <span className="analyst-brief-text font-mono text-xs">{analystText}</span>
      </div>

      {/* Table Column Headers */}
      <div className="grid grid-cols-[1fr_80px_180px_80px] items-center gap-3 px-3.5 py-2 bg-[#0c121a] border-b border-[#1f2937] font-mono text-xs font-semibold text-slate-400 uppercase tracking-wider select-none">
        <div className="text-left">Feature Name</div>
        <div className="text-right">Raw Value</div>
        <div className="text-center">Attribution (±SHAP)</div>
        <div className="text-right">Impact</div>
      </div>

      {/* Waterfall Rows */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2 select-text">
        {drivers.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-[#8b949e] font-mono text-xs gap-2">
            <HelpCircle className="w-6 h-6 text-slate-500" />
            <span>Select any flow or incident to inspect exact TreeSHAP feature attributions.</span>
          </div>
        ) : (
          drivers.map((driver, idx) => {
            const isThreat = driver.shap_attribution >= 0;
            const pctWidth = Math.min((Math.abs(driver.shap_attribution) / maxAbsShap) * 50.0, 50.0);
            const deltaSign = isThreat
              ? `+${driver.shap_attribution.toFixed(3)}`
              : driver.shap_attribution.toFixed(3);

            return (
              <div
                key={`shap-${driver.feature}-${idx}`}
                className="shap-row-animate grid grid-cols-[1fr_80px_180px_80px] items-center gap-3 px-3 py-2.5 min-h-[42px] bg-[#161b22] hover:bg-[#1a2330] border border-[#233044] rounded-md font-mono text-xs tabular-nums transition-colors shadow-xs"
              >
                {/* Feature Name */}
                <div className="truncate text-slate-200 font-medium font-sans text-xs" title={driver.feature}>
                  {driver.feature}
                </div>

                {/* Feature Raw Value (Right-aligned, monospace) */}
                <div className="text-right text-slate-400 font-mono text-xs font-semibold tabular-nums">
                  {typeof driver.value === 'number' ? driver.value.toFixed(2) : driver.value}
                </div>

                {/* Diverging Waterfall Bar (Wide, distinct center baseline, h-5) */}
                <div className="relative h-5 w-full bg-[#090e17] rounded border border-[#233044] flex items-center overflow-hidden">
                  {/* Center origin line */}
                  <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-slate-500 z-10" />

                  {isThreat ? (
                    <div
                      className="shap-bar-fill absolute left-1/2 h-full bg-[#f85149] rounded-r-xs shadow-[0_0_8px_rgba(248,81,73,0.4)]"
                      data-width={`${pctWidth}%`}
                      style={{ width: '0%' }}
                    />
                  ) : (
                    <div
                      className="shap-bar-fill absolute right-1/2 h-full bg-[#3fb950] rounded-l-xs shadow-[0_0_8px_rgba(63,185,80,0.4)]"
                      data-width={`${pctWidth}%`}
                      style={{ width: '0%' }}
                    />
                  )}
                </div>

                {/* Delta Sign (Right-aligned, monospace, colored) */}
                <div
                  className={`text-right font-mono text-xs font-bold tabular-nums ${
                    isThreat ? 'text-[#f85149]' : 'text-[#3fb950]'
                  }`}
                >
                  {deltaSign}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Axis Scale Legend */}
      <div className="bg-[#121822] border-t border-[#21262d] px-3.5 py-2 flex justify-between items-center font-mono text-xs text-slate-400 select-none">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#3fb950]" />
          <span>MITIGATING (DECREASES RISK)</span>
        </div>
        <div className="text-center font-bold text-slate-300">
          CENTER ZERO BASELINE
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#f85149]" />
          <span>SUSPICIOUS (INCREASES RISK)</span>
        </div>
      </div>
    </div>
  );
};
