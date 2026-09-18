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
      className="bg-[#0d1117] border border-[#21262d] rounded-[2px] flex flex-col overflow-hidden"
      style={{ height: `${height}px` }}
    >
      {/* Header Bar */}
      <div className="bg-[#161b22] border-b border-[#21262d] px-2.5 py-1.5 flex justify-between items-center font-heading text-[10px] font-bold tracking-wider uppercase text-[#8b949e] select-none">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-[1px] bg-[#3FB950] inline-block" />
          <span className="text-[#e6edf3]">COMPONENT 01 //</span>
          <span>LIVE FLOW INGESTION & MULTI-TIER SCORING STREAM</span>
        </div>

        <div className="flex items-center gap-3 font-mono text-[9.5px]">
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className="flex items-center gap-1 px-1.5 py-0.5 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] rounded-[2px] transition-colors border border-[#30363d] cursor-pointer"
            title={autoScroll ? 'Freeze auto-scroll' : 'Resume auto-scroll'}
          >
            {autoScroll ? (
              <>
                <Pause className="w-3 h-3 text-[#D29922]" />
                <span>FREEZE</span>
              </>
            ) : (
              <>
                <Play className="w-3 h-3 text-[#3FB950]" />
                <span>LIVE</span>
              </>
            )}
          </button>
          <span className="text-[#8b949e]">
            {searchTerm || severityFilter !== 'ALL' ? (
              <>
                MATCHES: <strong className="text-[#58a6ff]">{filteredAlerts.length}</strong> / {alerts.length}
              </>
            ) : (
              <>
                SYNCED: <strong className="text-[#e6edf3]">{alerts.length}</strong> FLOWS
              </>
            )}
          </span>
        </div>
      </div>

      {/* CyberWatch-style Search and Filter Bar */}
      <div className="bg-[#090b0e] border-b border-[#21262d] px-2.5 py-1.5 flex flex-wrap items-center justify-between gap-2 font-mono text-[10px]">
        {/* Search Input Box */}
        <div className="relative flex-1 min-w-[200px] max-w-md flex items-center">
          <Search className="w-3.5 h-3.5 absolute left-2 text-[#527194] pointer-events-none" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search flow IP, attack profile, tier, or port..."
            className="w-full bg-[#161b22] border border-[#21262d] focus:border-[#58a6ff] text-[#e6edf3] placeholder-[#527194] text-[10px] pl-7 pr-6 py-1 rounded-[2px] outline-none transition-colors"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-2 text-[#8b949e] hover:text-[#e6edf3] cursor-pointer"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Severity Filter Chips */}
        <div className="flex items-center gap-1">
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
                className={`px-2 py-0.5 text-[9px] font-mono rounded-[2px] border cursor-pointer transition-all ${
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
        <table className="w-full border-collapse text-left font-mono text-[10.5px]">
          <thead className="sticky top-0 bg-[#161b22] text-[#8b949e] font-medium text-[9px] uppercase tracking-wider z-10 border-b border-[#21262d]">
            <tr>
              <th className="py-1 px-2.5">TIMESTAMP</th>
              <th className="py-1 px-2.5">SRC ADDR</th>
              <th className="py-1 px-2.5">DST ADDR:PORT</th>
              <th className="py-1 px-2.5">ATTACK PROFILE</th>
              <th className="py-1 px-2.5">SIG PROB</th>
              <th className="py-1 px-2.5">AE LOSS</th>
              <th className="py-1 px-2.5">DETECTION TIER</th>
              <th className="py-1 px-2.5">SEVERITY</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#161b22]">
            {filteredAlerts.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-[#8b949e]">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <ShieldAlert className="w-6 h-6 text-[#8b949e] stroke-1" />
                    <span>
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
                        className="text-[10px] text-[#58a6ff] hover:underline cursor-pointer mt-1"
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
                    ? 'text-[#F85149] font-semibold'
                    : alert.supervised_probability >= 0.15
                    ? 'text-[#D29922] font-semibold'
                    : 'text-[#8b949e]';

                const lossClass =
                  alert.reconstruction_loss >= 0.8 ? 'text-[#D29922] font-semibold' : 'text-[#8b949e]';

                return (
                  <tr
                    key={`${alert.alert_id}-${idx}`}
                    onClick={() => onSelectAlert(alert)}
                    className={`alert-row-animate cursor-pointer transition-colors whitespace-nowrap ${
                      isSelected
                        ? 'bg-[#21262d] border-l-2 border-[#58a6ff]'
                        : 'hover:bg-[#161b22]'
                    }`}
                  >
                    <td className="py-1 px-2.5 text-[#8b949e]">
                      {alert.timestamp.toFixed(2)}
                    </td>
                    <td className="py-1 px-2.5 text-[#e6edf3]">
                      {alert.src_ip}
                    </td>
                    <td className="py-1 px-2.5 text-[#e6edf3]">
                      {alert.dst_ip}:<span className="text-[#8b949e]">{alert.dst_port}</span>
                    </td>
                    <td className="py-1 px-2.5 font-semibold text-[#e6edf3]">
                      {alert.attack_type || 'BENIGN'}
                    </td>
                    <td className={`py-1 px-2.5 ${probClass}`}>
                      {alert.supervised_probability.toFixed(3)}
                    </td>
                    <td className={`py-1 px-2.5 ${lossClass}`}>
                      {alert.reconstruction_loss.toFixed(4)}
                    </td>
                    <td className="py-1 px-2.5">
                      {isCrit ? (
                        <span className="text-[#F85149] font-bold">{alert.detection_tier}</span>
                      ) : isWarn ? (
                        <span className="text-[#D29922] font-semibold">{alert.detection_tier}</span>
                      ) : (
                        <span className="text-[#8b949e]">NONE</span>
                      )}
                    </td>
                    <td className="py-1 px-2.5">
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
