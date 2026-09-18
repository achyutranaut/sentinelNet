import React, { useEffect, useMemo, useRef, useState } from 'react';
import anime from 'animejs';
import type { AlertStreamItem } from '@/lib/types';
import { Pause, Play, ShieldAlert, Search, X } from 'lucide-react';

interface LiveAlertStreamProps {
  alerts: AlertStreamItem[];
  selectedAlertId: string | null;
  onSelectAlert: (alert: AlertStreamItem) => void;
  height?: number;
}

export const LiveAlertStream: React.FC<LiveAlertStreamProps> = ({
  alerts,
  selectedAlertId,
  onSelectAlert,
  height = 360,
}) => {
  const [autoScroll, setAutoScroll] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<'ALL' | 'CRITICAL' | 'ANOMALY' | 'CLEAN'>('ALL');

  const containerRef = useRef<HTMLDivElement>(null);
  const prevAlertCount = useRef(alerts.length);

  // Filtered alerts based on search and severity
  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      const isCrit = alert.is_attack || alert.supervised_probability >= 0.5;
      const isWarn = !isCrit && (alert.reconstruction_loss >= 0.8 || alert.supervised_probability >= 0.15);
      const isClean = !isCrit && !isWarn;

      // Severity check
      if (severityFilter === 'CRITICAL' && !isCrit) return false;
      if (severityFilter === 'ANOMALY' && !isWarn) return false;
      if (severityFilter === 'CLEAN' && !isClean) return false;

      // Search term check
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase().trim();
        const srcMatch = alert.src_ip.toLowerCase().includes(query);
        const dstMatch = alert.dst_ip.toLowerCase().includes(query);
        const portMatch = alert.dst_port.toString().includes(query);
        const attackMatch = (alert.attack_type || 'BENIGN').toLowerCase().includes(query);
        const tierMatch = (alert.detection_tier || '').toLowerCase().includes(query);
        const idMatch = alert.alert_id.toLowerCase().includes(query);
        const severityStr = isCrit ? 'critical' : isWarn ? 'anomaly elevated warn' : 'clean nominal benign';
        const severityMatch = severityStr.includes(query);

        if (!srcMatch && !dstMatch && !portMatch && !attackMatch && !tierMatch && !idMatch && !severityMatch) {
          return false;
        }
      }

      return true;
    });
  }, [alerts, searchTerm, severityFilter]);

  // Trigger Anime.js entrance transition only when new alerts arrive
  useEffect(() => {
    if (alerts.length > prevAlertCount.current) {
      anime({
        targets: '.alert-row-animate',
        opacity: [0, 1],
        translateX: [-8, 0],
        duration: 90,
        easing: 'easeOutQuad',
        delay: anime.stagger(15),
      });

      if (autoScroll && containerRef.current && !searchTerm) {
        containerRef.current.scrollTop = containerRef.current.scrollHeight;
      }
    }
    prevAlertCount.current = alerts.length;
  }, [alerts, autoScroll, searchTerm]);

  return (
    <div
      className="bg-[#0d1117] border border-[#21262d] rounded flex flex-col overflow-hidden flex-1"
      style={height ? { minHeight: `${height}px` } : undefined}
    >
      {/* Header Bar */}
      <div className="bg-[#161b22] border-b border-[#21262d] px-3 py-2 flex justify-between items-center font-heading text-xs font-bold tracking-wider uppercase text-[#8b949e] select-none">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#3FB950] inline-block animate-pulse" />
          <span className="text-[#e6edf3]">COMPONENT 01 //</span>
          <span>LIVE FLOW INGESTION & MULTI-TIER SCORING STREAM</span>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className="flex items-center gap-1.5 px-2 py-1 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] rounded transition-colors border border-[#30363d] cursor-pointer"
            title={autoScroll ? 'Freeze auto-scroll' : 'Resume auto-scroll'}
          >
            {autoScroll ? (
              <>
                <Pause className="w-3.5 h-3.5 text-[#D29922]" />
                <span className="text-xs font-semibold">FREEZE</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 text-[#3FB950]" />
                <span className="text-xs font-semibold">LIVE</span>
              </>
            )}
          </button>
          <span className="text-[#8b949e]">
            {searchTerm || severityFilter !== 'ALL' ? (
              <>
                MATCHES: <strong className="text-[#58a6ff] tabular-nums">{filteredAlerts.length}</strong> / {alerts.length}
              </>
            ) : (
              <>
                SYNCED: <strong className="text-[#e6edf3] tabular-nums">{alerts.length}</strong> FLOWS
              </>
            )}
          </span>
        </div>
      </div>

      {/* Search and Filter Bar */}
      <div className="bg-[#090b0e] border-b border-[#21262d] px-3 py-2 flex flex-wrap items-center justify-between gap-2.5 font-mono text-xs">
        {/* Search Input Box */}
        <div className="relative flex-1 min-w-[220px] max-w-md flex items-center">
          <Search className="w-4 h-4 absolute left-2.5 text-[#527194] pointer-events-none" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search flow IP, attack profile, tier, or port..."
            className="w-full bg-[#161b22] border border-[#21262d] focus:border-[#58a6ff] text-[#e6edf3] placeholder-[#527194] text-xs pl-8 pr-7 py-1.5 rounded outline-none transition-colors"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-2.5 text-[#8b949e] hover:text-[#e6edf3] cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Severity Filter Chips */}
        <div className="flex items-center gap-1.5">
          {(['ALL', 'CRITICAL', 'ANOMALY', 'CLEAN'] as const).map((sev) => {
            const isActive = severityFilter === sev;
            const activeColors = {
              ALL: 'bg-[#58a6ff]/20 text-[#58a6ff] border-[#58a6ff]/60',
              CRITICAL: 'bg-[#f85149]/20 text-[#f85149] border-[#f85149]/60',
              ANOMALY: 'bg-[#d29922]/20 text-[#d29922] border-[#d29922]/60',
              CLEAN: 'bg-[#3fb950]/20 text-[#3fb950] border-[#3fb950]/60',
            };

            return (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-2.5 py-1 text-xs font-mono font-semibold rounded border cursor-pointer transition-all ${
                  isActive
                    ? activeColors[sev]
                    : 'bg-[#161b22] text-[#8b949e] border-[#21262d] hover:border-[#30363d] hover:text-[#e6edf3]'
                }`}
              >
                {sev}
              </button>
            );
          })}
        </div>
      </div>

      {/* Monospace Stream Table */}
      <div ref={containerRef} className="flex-1 overflow-y-auto overflow-x-auto select-text">
        <table className="w-full border-collapse text-left font-mono text-xs tabular-nums">
          <thead className="sticky top-0 bg-[#161b22] text-slate-400 font-semibold text-[11px] uppercase tracking-wider z-10 border-b border-white/10">
            <tr>
              <th className="py-2 px-3">TIMESTAMP</th>
              <th className="py-2 px-3">SRC ADDR</th>
              <th className="py-2 px-3">DST ADDR:PORT</th>
              <th className="py-2 px-3">ATTACK PROFILE</th>
              <th className="py-2 px-3">SIG PROB</th>
              <th className="py-2 px-3">AE LOSS</th>
              <th className="py-2 px-3">DETECTION TIER</th>
              <th className="py-2 px-3">SEVERITY</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filteredAlerts.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-14 text-center text-slate-500">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <ShieldAlert className="w-7 h-7 text-slate-500 stroke-1" />
                    <span className="text-xs">
                      {alerts.length === 0
                        ? 'Awaiting streaming network flows. Ingest a flow batch from operational controls.'
                        : `No flows match current filter criteria ("${searchTerm || severityFilter}").`}
                    </span>
                    {(searchTerm || severityFilter !== 'ALL') && (
                      <button
                        onClick={() => {
                          setSearchTerm('');
                          setSeverityFilter('ALL');
                        }}
                        className="text-xs text-[#38bdf8] hover:underline cursor-pointer mt-1 font-semibold"
                      >
                        Reset filters
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ) : (
              filteredAlerts.map((alert, idx) => {
                const isSelected = alert.alert_id === selectedAlertId;
                const isCrit = alert.is_attack || alert.supervised_probability >= 0.5;
                const isWarn = !isCrit && (alert.reconstruction_loss >= 0.8 || alert.supervised_probability >= 0.15);

                const probClass =
                  alert.supervised_probability >= 0.5
                    ? 'text-[#F85149] font-bold'
                    : alert.supervised_probability >= 0.15
                    ? 'text-[#D29922] font-semibold'
                    : 'text-slate-400';

                const lossClass =
                  alert.reconstruction_loss >= 0.8 ? 'text-[#D29922] font-semibold' : 'text-slate-400';

                return (
                  <tr
                    key={`${alert.alert_id}-${idx}`}
                    onClick={() => onSelectAlert(alert)}
                    className={`alert-row-animate cursor-pointer transition-colors whitespace-nowrap even:bg-white/[0.015] border-b border-white/5 ${
                      isSelected
                        ? 'bg-sky-500/10 border-l-2 border-[#38bdf8]'
                        : 'hover:bg-white/[0.04]'
                    }`}
                  >
                    <td className="py-2 px-3 text-slate-400 font-mono text-xs tabular-nums">
                      {alert.timestamp.toFixed(2)}
                    </td>
                    <td className="py-2 px-3 text-slate-200 font-medium font-mono text-xs tabular-nums">
                      {alert.src_ip}
                    </td>
                    <td className="py-2 px-3 text-slate-200 font-mono text-xs tabular-nums">
                      {alert.dst_ip}:<span className="text-slate-400">{alert.dst_port}</span>
                    </td>
                    <td className="py-2 px-3 font-semibold text-slate-100 font-sans text-xs">
                      {alert.attack_type || 'BENIGN'}
                    </td>
                    <td className={`py-2 px-3 font-mono text-xs tabular-nums ${probClass}`}>
                      {alert.supervised_probability.toFixed(3)}
                    </td>
                    <td className={`py-2 px-3 font-mono text-xs tabular-nums ${lossClass}`}>
                      {alert.reconstruction_loss.toFixed(4)}
                    </td>
                    <td className="py-2 px-3 font-mono text-xs">
                      {isCrit ? (
                        <span className="text-[#F85149] font-bold">{alert.detection_tier}</span>
                      ) : isWarn ? (
                        <span className="text-[#D29922] font-semibold">{alert.detection_tier}</span>
                      ) : (
                        <span className="text-slate-400">NONE</span>
                      )}
                    </td>
                    <td className="py-2 px-3">
                      {isCrit ? (
                        <span className="badge-critical">CRITICAL</span>
                      ) : isWarn ? (
                        <span className="badge-warning">ANOMALY</span>
                      ) : (
                        <span className="badge-neutral">CLEAN</span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
