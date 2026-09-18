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
      className="shap-inspector-panel bg-[#0d1117] border border-[#21262d] rounded-[2px] flex flex-col overflow-hidden"
      style={{ height: `${height}px` }}
    >
      {/* Panel Header */}
      <div className="bg-[#161b22] border-b border-[#21262d] px-2.5 py-1.5 flex justify-between items-center font-heading text-[10px] font-bold tracking-wider uppercase text-[#8b949e] select-none">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-[1px] bg-[#3b82f6] inline-block" />
          <span className="text-[#e6edf3]">COMPONENT 03 //</span>
          <span>TREESHAP INCIDENT ATTRIBUTION INSPECTOR (TIER 5)</span>
          {targetEntity && (
            <span className="text-[#58a6ff] font-mono text-[9px] px-1.5 py-0.2 rounded-[2px] bg-[#162b47] border border-[#23426e] tracking-tight">
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
      <div className="bg-[#161b22] border-b border-[#21262d] border-l-2 border-l-[#3b82f6] px-2.5 py-1.5 font-mono text-[9.5px] text-[#c9d1d9] leading-tight">
        <span className="font-heading font-bold text-[#3b82f6] tracking-wider uppercase mr-1">
          ANALYST BRIEF:
        </span>
        <span className="analyst-brief-text">{analystText}</span>
      </div>

      {/* Waterfall Rows */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1 select-text">
        {drivers.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-[#8b949e] font-mono text-xs gap-1.5">
            <HelpCircle className="w-5 h-5 text-[#8b949e]" />
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
                className="shap-row-animate grid grid-cols-[140px_60px_1fr_60px] items-center gap-2 px-2 py-1 bg-[#161b22] border border-[#21262d] rounded-[2px] font-mono text-[9.5px]"
              >
                {/* Feature Name */}
                <div className="truncate text-[#e6edf3] font-medium" title={driver.feature}>
                  {driver.feature}
                </div>

                {/* Feature Raw Value */}
                <div className="text-right text-[#8b949e] text-[9px]">
                  {driver.value.toFixed(2)}
                </div>

                {/* Diverging Waterfall Bar */}
                <div className="relative h-3.5 bg-[#090b0e] rounded-[1px] flex items-center overflow-hidden">
                  {/* Center origin line */}
                  <div className="absolute left-1/2 top-0 bottom-0 w-px bg-[#30363d] z-10" />

                  {isThreat ? (
                    <div
                      className="shap-bar-fill absolute left-1/2 h-full bg-[#F85149]"
                      data-width={`${pctWidth}%`}
                      style={{ width: '0%' }}
                    />
                  ) : (
                    <div
                      className="shap-bar-fill absolute right-1/2 h-full bg-[#3FB950]"
                      data-width={`${pctWidth}%`}
                      style={{ width: '0%' }}
                    />
                  )}
                </div>

                {/* Delta Sign */}
                <div
                  className={`text-right font-semibold ${
                    isThreat ? 'text-[#F85149]' : 'text-[#3FB950]'
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
      <div className="bg-[#161b22] border-t border-[#21262d] px-2.5 py-1 flex justify-between items-center font-mono text-[8px] text-[#8b949e] select-none">
        <div className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-[1px] bg-[#3FB950]" />
          <span>MITIGATING FEATURE (DECREASES RISK)</span>
        </div>
        <div className="text-center font-bold text-[#e6edf3]">
          DIVERGING ATTRIBUTION (±SHAP)
        </div>
        <div className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-[1px] bg-[#F85149]" />
          <span>SUSPICIOUS DRIVER (INCREASES RISK)</span>
        </div>
      </div>
    </div>
  );
};
