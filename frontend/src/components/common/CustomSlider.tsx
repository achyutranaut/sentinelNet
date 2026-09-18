import React, { useState } from 'react';

interface CustomSliderProps {
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (val: number) => void;
  label?: string;
  sublabel?: string;
  unit?: string;
  color?: string; // hex accent color
  formatValue?: (val: number) => string;
}

export const CustomSlider: React.FC<CustomSliderProps> = ({
  value,
  min,
  max,
  step = 0.01,
  onChange,
  label,
  sublabel,
  unit = '',
  color = '#38bdf8',
  formatValue,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const pct = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
  const displayVal = formatValue ? formatValue(value) : `${value.toFixed(2)}${unit}`;

  return (
    <div className="space-y-1.5 w-full">
      {/* Header with Label and Value */}
      {(label || sublabel) && (
        <div className="flex justify-between items-baseline">
          <div>
            {label && (
              <span className="font-sans text-xs font-semibold text-slate-200 tracking-wide uppercase">
                {label}
              </span>
            )}
            {sublabel && (
              <span className="block text-[11px] text-slate-400 font-sans mt-0.5">
                {sublabel}
              </span>
            )}
          </div>
          <span
            className="font-mono text-sm font-bold tracking-tight px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700/60 shadow-sm"
            style={{ color }}
          >
            {displayVal}
          </span>
        </div>
      )}

      {/* Slider Container with Custom Track Fill and Floating Tooltip */}
      <div
        className="relative py-2 flex items-center"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Floating Tooltip during hover or drag */}
        {(isHovered || isDragging) && (
          <div
            className="absolute -top-7 -translate-x-1/2 pointer-events-none z-30 transition-all duration-75 ease-out"
            style={{ left: `${pct}%` }}
          >
            <div
              className="px-2 py-0.5 rounded text-[11px] font-mono font-bold text-slate-950 shadow-lg whitespace-nowrap"
              style={{ backgroundColor: color }}
            >
              {displayVal}
              {/* Arrow */}
              <div
                className="w-1.5 h-1.5 rotate-45 mx-auto -mt-0.5"
                style={{ backgroundColor: color }}
              />
            </div>
          </div>
        )}

        {/* Custom Progress Track Behind Native Slider */}
        <div className="absolute inset-x-0 h-1.5 rounded-full bg-slate-800 overflow-hidden pointer-events-none">
          <div
            className="h-full rounded-full transition-all duration-75 ease-out"
            style={{
              width: `${pct}%`,
              backgroundColor: color,
              boxShadow: `0 0 8px ${color}80`,
            }}
          />
        </div>

        {/* Transparent Native Range Input */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          onMouseDown={() => setIsDragging(true)}
          onMouseUp={() => setIsDragging(false)}
          onTouchStart={() => setIsDragging(true)}
          onTouchEnd={() => setIsDragging(false)}
          className="custom-slider relative z-10 w-full cursor-pointer"
          style={
            {
              '--thumb-color': color,
            } as React.CSSProperties
          }
        />
      </div>
    </div>
  );
};
