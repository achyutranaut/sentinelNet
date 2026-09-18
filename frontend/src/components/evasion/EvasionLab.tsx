import React, { useEffect, useRef, useState } from 'react';
import anime from 'animejs';
import { testEvasion } from '@/lib/api';
import type { EvasionTestResponse } from '@/lib/types';
import { Sliders } from 'lucide-react';

interface EvasionLabProps {
  currentEpsilon: number;
  onEpsilonChange: (eps: number) => void;
  height?: number;
}

interface CurvePoint {
  eps: number;
  sup: number;
  ae: number;
  comb: number;
}

export const EvasionLab: React.FC<EvasionLabProps> = ({
  currentEpsilon,
  onEpsilonChange,
  height = 430,
}) => {
  const [activeTest, setActiveTest] = useState<EvasionTestResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [curvePoints, setCurvePoints] = useState<CurvePoint[]>([
    { eps: 0.0, sup: 0.99, ae: 0.88, comb: 0.99 },
    { eps: 0.05, sup: 0.94, ae: 0.86, comb: 0.98 },
    { eps: 0.1, sup: 0.82, ae: 0.84, comb: 0.96 },
    { eps: 0.15, sup: 0.61, ae: 0.82, comb: 0.93 },
    { eps: 0.2, sup: 0.35, ae: 0.79, comb: 0.89 },
    { eps: 0.3, sup: 0.12, ae: 0.75, comb: 0.82 },
    { eps: 0.4, sup: 0.04, ae: 0.71, comb: 0.78 },
  ]);

  const prevEps = useRef(currentEpsilon);

  // Run backend POST /evasion/test when epsilon changes
  useEffect(() => {
    let isCurrent = true;
    async function evaluate() {
      try {
        setIsLoading(true);
        const res = await testEvasion(currentEpsilon, 40);
        if (isCurrent) {
          setActiveTest(res);
          // Update curve point with real response
          setCurvePoints((prev) =>
            prev.map((pt) =>
              Math.abs(pt.eps - currentEpsilon) < 0.02
                ? {
                    eps: currentEpsilon,
                    sup: res.supervised_recall,
                    ae: res.autoencoder_recall,
                    comb: res.combined_recall,
                  }
                : pt
            )
          );
        }
      } catch (err) {
        console.warn('Evasion test error:', err);
      } finally {
        if (isCurrent) setIsLoading(false);
      }
    }

    evaluate();
    return () => {
      isCurrent = false;
    };
  }, [currentEpsilon]);

  // Coordinate mapping for SVG viewBox 0 0 380 230
  // x: 0.0 -> 40, 0.4 -> 360 (scale = 320 / 0.4 = 800)
  // y: 1.0 -> 20, 0.0 -> 190 (scale = 170)
  const mapX = (eps: number) => 40 + (eps / 0.4) * 320;
  const mapY = (val: number) => 190 - val * 170;

  const targetCursorX = mapX(currentEpsilon);
  const activeSup = activeTest ? activeTest.supervised_recall : 0.61;
  const activeAe = activeTest ? activeTest.autoencoder_recall : 0.82;
  const activeComb = activeTest ? activeTest.combined_recall : 0.93;

  const targetSupY = mapY(activeSup);
  const targetCombY = mapY(activeComb);

  // Anime.js timeline cursor & indicator synchronization
  useEffect(() => {
    if (Math.abs(prevEps.current - currentEpsilon) > 0.001) {
      prevEps.current = currentEpsilon;

      const tl = anime.timeline({
        duration: 160,
        easing: 'easeOutQuad',
      });

      tl.add({
        targets: '#budget-cursor-line',
        x1: targetCursorX,
        x2: targetCursorX,
      })
        .add(
          {
            targets: '#dot-combined',
            cx: targetCursorX,
            cy: targetCombY,
          },
          0
        )
        .add(
          {
            targets: '#dot-supervised',
            cx: targetCursorX,
            cy: targetSupY,
          },
          0
        );
    }
  }, [currentEpsilon, targetCursorX, targetCombY, targetSupY]);

  // Build SVG paths for the 3 curves
  const dSup = curvePoints
    .map((pt, i) => `${i === 0 ? 'M' : 'L'} ${mapX(pt.eps)} ${mapY(pt.sup)}`)
    .join(' ');
  const dAe = curvePoints
    .map((pt, i) => `${i === 0 ? 'M' : 'L'} ${mapX(pt.eps)} ${mapY(pt.ae)}`)
    .join(' ');
  const dComb = curvePoints
    .map((pt, i) => `${i === 0 ? 'M' : 'L'} ${mapX(pt.eps)} ${mapY(pt.comb)}`)
    .join(' ');

  return (
    <div
      className="bg-[#0d1117] border border-[#21262d] rounded flex flex-col overflow-hidden flex-1"
      style={{ minHeight: height }}
    >
      {/* Panel Header */}
      <div className="bg-[#161b22] border-b border-[#21262d] px-3 py-2 flex justify-between items-center font-heading text-xs font-bold tracking-wider uppercase text-[#8b949e] select-none">
        <div className="flex items-center gap-2">
          <span className="text-[#e6edf3]">COMPONENT 04 //</span>
          <span>ADVERSARIAL EVASION & STRESS-TEST LAB</span>
          <span className="text-[#30363d]">|</span>
          <span className="text-[#8b949e]">TIER 4 (RESILIENCE)</span>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs tabular-nums">
          <span className="text-[#8b949e]">ACTIVE ε:</span>
          <span className="text-[#D29922] font-semibold">{currentEpsilon.toFixed(2)}</span>
          {isLoading && <span className="w-2 h-2 bg-[#D29922] rounded-full animate-ping" />}
        </div>
      </div>

      {/* Lab Content */}
      <div className="flex-1 p-3 flex flex-col gap-3">
        {/* Interactive Slider Control */}
        <div className="bg-[#161b22] border border-[#21262d] rounded p-2.5 flex items-center gap-3">
          <div className="flex items-center gap-2 font-heading text-xs font-bold text-[#8b949e] uppercase whitespace-nowrap">
            <Sliders className="w-4 h-4 text-[#e6edf3]" />
            <span>PERTURBATION BUDGET (ε):</span>
          </div>

          <input
            type="range"
            min="0.0"
            max="0.40"
            step="0.05"
            value={currentEpsilon}
            onChange={(e) => onEpsilonChange(parseFloat(e.target.value))}
            className="flex-1 accent-[#D29922] cursor-pointer"
          />

          <span className="font-mono text-xs font-semibold text-[#e6edf3] w-12 text-right tabular-nums">
            {currentEpsilon.toFixed(2)}
          </span>
        </div>

        {/* Chart & Telemetry Row */}
        <div className="flex-1 flex gap-3 min-h-[340px]">
          {/* SVG Chart Area */}
          <div className="flex-[2] bg-[#090b0e] border border-[#21262d] rounded p-2 relative flex items-center justify-center">
            <svg viewBox="0 0 380 230" className="w-full h-full select-none" preserveAspectRatio="xMidYMid meet">
              {/* Grid & Axes */}
              <line x1="40" y1="20" x2="40" y2="190" stroke="#21262d" strokeWidth="1" />
              <line x1="40" y1="190" x2="360" y2="190" stroke="#21262d" strokeWidth="1" />

              {/* Y Axis Ticks */}
              <text x="32" y="24" className="fill-[#8b949e] font-mono text-xs tabular-nums" textAnchor="end">1.0</text>
              <text x="32" y="105" className="fill-[#8b949e] font-mono text-xs tabular-nums" textAnchor="end">0.5</text>
              <text x="32" y="193" className="fill-[#8b949e] font-mono text-xs tabular-nums" textAnchor="end">0.0</text>

              {/* X Axis Ticks */}
              <text x="40" y="204" className="fill-[#8b949e] font-mono text-xs tabular-nums" textAnchor="middle">0.0</text>
              <text x="120" y="204" className="fill-[#8b949e] font-mono text-xs tabular-nums" textAnchor="middle">0.1</text>
              <text x="200" y="204" className="fill-[#8b949e] font-mono text-xs tabular-nums" textAnchor="middle">0.2</text>
              <text x="280" y="204" className="fill-[#8b949e] font-mono text-xs tabular-nums" textAnchor="middle">0.3</text>
              <text x="360" y="204" className="fill-[#8b949e] font-mono text-xs tabular-nums" textAnchor="middle">0.4</text>
              <text x="200" y="222" className="fill-[#8b949e] font-mono text-xs uppercase" textAnchor="middle">
                Perturbation Budget (ε)
              </text>

              {/* Curves */}
              <path d={dSup} fill="none" stroke="#F85149" strokeWidth="1.8" strokeDasharray="4 3" />
              <path d={dAe} fill="none" stroke="#3b82f6" strokeWidth="1.8" strokeDasharray="2 2" />
              <path d={dComb} fill="none" stroke="#3FB950" strokeWidth="2.2" />

              {/* Synchronized Timeline Cursor & Indicator Dots */}
              <line
                id="budget-cursor-line"
                x1={targetCursorX}
                y1="20"
                x2={targetCursorX}
                y2="190"
                stroke="#D29922"
                strokeWidth="1.5"
                strokeDasharray="3 3"
              />
              <circle id="dot-combined" r="4.5" fill="#3FB950" cx={targetCursorX} cy={targetCombY} />
              <circle id="dot-supervised" r="4" fill="#F85149" cx={targetCursorX} cy={targetSupY} />
            </svg>
          </div>

          {/* Telemetry Column */}
          <div className="flex-1 bg-[#161b22] border border-[#21262d] rounded p-3 flex flex-col justify-between font-mono select-none">
            <div className="space-y-3">
              <div>
                <div className="text-xs uppercase text-[#8b949e] font-heading font-semibold">Perturbation Budget</div>
                <div className="text-base font-bold text-[#e6edf3] tabular-nums">{currentEpsilon.toFixed(2)}</div>
              </div>

              <div>
                <div className="text-xs uppercase text-[#8b949e] font-heading font-semibold">Signature Recall (Tier 1)</div>
                <div className="text-base font-bold text-[#F85149] tabular-nums">
                  {(activeSup * 100).toFixed(1)}%
                </div>
              </div>

              <div>
                <div className="text-xs uppercase text-[#8b949e] font-heading font-semibold">Zero-Day Anomaly (Tier 2)</div>
                <div className="text-base font-bold text-[#3b82f6] tabular-nums">
                  {(activeAe * 100).toFixed(1)}%
                </div>
              </div>

              <div>
                <div className="text-xs uppercase text-[#8b949e] font-heading font-semibold">Multi-Tier Defense</div>
                <div className="text-base font-bold text-[#3FB950] tabular-nums">
                  {(activeComb * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Legend */}
            <div className="pt-2 border-t border-[#21262d] space-y-1 text-xs">
              <div className="flex items-center gap-2 text-[#3FB950]">
                <span className="w-3 h-0.5 bg-[#3FB950]" />
                <span className="font-sans font-medium">Multi-Tier Combined</span>
              </div>
              <div className="flex items-center gap-2 text-[#F85149]">
                <span className="w-3 h-0.5 bg-[#F85149] border-b border-dashed" />
                <span className="font-sans font-medium">Tier 1 LightGBM</span>
              </div>
              <div className="flex items-center gap-2 text-[#3b82f6]">
                <span className="w-3 h-0.5 bg-[#3b82f6] border-b border-dotted" />
                <span className="font-sans font-medium">Tier 2 Autoencoder</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
