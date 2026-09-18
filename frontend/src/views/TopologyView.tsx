import React, { useState } from 'react';
import { Network, RefreshCw, Eye, X } from 'lucide-react';
import type { AlertStreamItem, GraphNode, GraphStateResponse } from '@/lib/types';
import { NetworkTopologyCanvas } from '@/components/graph/NetworkTopologyCanvas';
import { TreeShapInspector } from '@/components/explainability/TreeShapInspector';

interface TopologyViewProps {
  graphState: GraphStateResponse | null;
  onRefreshGraph: () => void;
  isLoading: boolean;
  error: string | null;
  selectedNodeId: string | null;
  selectedAlert: AlertStreamItem | null;
  onSelectNode: (node: GraphNode) => void;
}

export const TopologyView: React.FC<TopologyViewProps> = ({
  graphState,
  onRefreshGraph,
  isLoading,
  error,
  selectedNodeId,
  selectedAlert,
  onSelectNode,
}) => {
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);

  const nodes = graphState?.nodes || [];
  const edges = graphState?.edges || [];
  const pivots = graphState?.flagged_pivots || [];

  const pivotCount = pivots.length || nodes.filter((n) => n.is_pivot).length;
  const internalCount = nodes.filter((n) => n.role === 'INTERNAL_SERVER' || n.id.includes('10.0.1')).length;
  const dmzCount = nodes.filter((n) => n.role === 'DMZ_SERVER' || n.id.includes('192.168.1')).length;
  const endpointCount = nodes.length - pivotCount - internalCount - dmzCount;

  return (
    <div className="space-y-4">
      {/* Page Header & Summary Strip */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-[#0d1117] border border-[#1f2937] p-3.5 rounded-lg shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2 font-heading">
            <Network className="w-5 h-5 text-purple-400" />
            <span>Temporal Host Interaction & Lateral Pivot Topology</span>
          </h1>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Tier 3 Graph Neural Network & Degree Z-Score novelty analysis tracking chronological infection paths
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs flex-wrap">
          <div className="bg-slate-900 border border-slate-800 px-2.5 py-1 rounded">
            <span className="text-slate-400">Nodes:</span>{' '}
            <strong className="text-slate-100">{nodes.length}</strong>
          </div>
          <div className="bg-slate-900 border border-slate-800 px-2.5 py-1 rounded">
            <span className="text-slate-400">Edges:</span>{' '}
            <strong className="text-slate-100">{edges.length}</strong>
          </div>
          <div className="bg-purple-950/50 border border-purple-800/40 px-2.5 py-1 rounded">
            <span className="text-purple-300">Pivots:</span>{' '}
            <strong className="text-purple-200">{pivotCount}</strong>
          </div>

          <button
            type="button"
            onClick={() => setIsInspectorOpen(!isInspectorOpen)}
            className={`flex items-center gap-1.5 px-3 py-1 rounded font-sans text-xs cursor-pointer transition-colors border ${
              isInspectorOpen
                ? 'bg-sky-500/20 text-sky-400 border-sky-500/60 shadow-xs'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-600'
            }`}
          >
            <Eye className="w-3.5 h-3.5 text-sky-400" />
            <span>{isInspectorOpen ? 'Hide Attribution' : 'Attribution Dock'}</span>
            {selectedNodeId && (
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse ml-0.5" />
            )}
          </button>

          <button
            type="button"
            onClick={onRefreshGraph}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 font-sans text-xs cursor-pointer transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh State</span>
          </button>
        </div>
      </div>

      {/* Main Canvas + Responsive Contextual Inspector Layout */}
      <div className="relative flex flex-1 min-h-0 gap-4">
        {/* Primary Stage: Full-Width Topology Graph Canvas & Classification Legend */}
        <div className="flex-1 min-w-0 flex flex-col gap-4">
          <NetworkTopologyCanvas
            graphState={graphState}
            onRefresh={onRefreshGraph}
            isLoading={isLoading}
            error={error}
            height={620}
            selectedNodeId={selectedNodeId}
            onSelectNode={(node) => {
              setIsInspectorOpen(true);
              onSelectNode(node);
            }}
          />

          {/* Proper Legend Panel */}
          <div className="bg-[#0d1117] border border-[#1f2937] rounded-lg p-4 shadow-sm">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 font-heading">
              Network Topology Node Classification & Legend
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3.5">
              {/* Pivot Host */}
              <div className="p-3.5 rounded-lg bg-red-950/30 border border-red-900/50 flex flex-col justify-between shadow-xs">
                <div className="flex items-center justify-between pb-2 border-b border-red-900/30">
                  <span className="flex items-center gap-2 text-xs font-bold text-red-400 font-heading tracking-wide">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#f85149] shadow-[0_0_8px_#f85149]" />
                    <span>Compromised Pivot</span>
                  </span>
                  <span className="text-xs font-mono font-bold text-red-300 bg-red-900/60 px-2 py-0.5 rounded-md border border-red-800/60 tabular-nums">
                    {pivotCount}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-2.5 leading-relaxed font-sans">
                  Degree Z-score &gt; +2.5σ or high Jaccard novelty. Infection vector spreading internally.
                </p>
              </div>

              {/* Internal Server */}
              <div className="p-3.5 rounded-lg bg-sky-950/30 border border-sky-900/50 flex flex-col justify-between shadow-xs">
                <div className="flex items-center justify-between pb-2 border-b border-sky-900/30">
                  <span className="flex items-center gap-2 text-xs font-bold text-sky-400 font-heading tracking-wide">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#38bdf8] shadow-[0_0_8px_#38bdf8]" />
                    <span>Internal Server</span>
                  </span>
                  <span className="text-xs font-mono font-bold text-sky-300 bg-sky-900/60 px-2 py-0.5 rounded-md border border-sky-800/60 tabular-nums">
                    {internalCount}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-2.5 leading-relaxed font-sans">
                  Enterprise subnet assets (<code className="text-sky-200 bg-sky-950/60 px-1 py-0.5 rounded text-xs">10.0.1.x</code>). Core infrastructure targets.
                </p>
              </div>

              {/* DMZ Gateway */}
              <div className="p-3.5 rounded-lg bg-purple-950/30 border border-purple-900/50 flex flex-col justify-between shadow-xs">
                <div className="flex items-center justify-between pb-2 border-b border-purple-900/30">
                  <span className="flex items-center gap-2 text-xs font-bold text-purple-400 font-heading tracking-wide">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#bc8cff] shadow-[0_0_8px_#bc8cff]" />
                    <span>DMZ Gateway</span>
                  </span>
                  <span className="text-xs font-mono font-bold text-purple-300 bg-purple-900/60 px-2 py-0.5 rounded-md border border-purple-800/60 tabular-nums">
                    {dmzCount}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-2.5 leading-relaxed font-sans">
                  Perimeter bastion hosts (<code className="text-purple-200 bg-purple-950/60 px-1 py-0.5 rounded text-xs">192.168.1.x</code>) facing incoming connections.
                </p>
              </div>

              {/* Endpoint */}
              <div className="p-3.5 rounded-lg bg-emerald-950/30 border border-emerald-900/50 flex flex-col justify-between shadow-xs">
                <div className="flex items-center justify-between pb-2 border-b border-emerald-900/30">
                  <span className="flex items-center gap-2 text-xs font-bold text-emerald-400 font-heading tracking-wide">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#3fb950] shadow-[0_0_8px_#3fb950]" />
                    <span>Workstation</span>
                  </span>
                  <span className="text-xs font-mono font-bold text-emerald-300 bg-emerald-900/60 px-2 py-0.5 rounded-md border border-emerald-800/60 tabular-nums">
                    {endpointCount}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-2.5 leading-relaxed font-sans">
                  Standard endpoints (<code className="text-emerald-200 bg-emerald-950/60 px-1 py-0.5 rounded text-xs">172.16.0.x</code>) displaying nominal traffic patterns.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Responsive Contextual Dock (>=1440px / 2xl) and Slide-Over Drawer (<1440px) */}
        {isInspectorOpen && (
          <>
            {/* Backdrop Blur on screens < 1440px */}
            <div
              className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 2xl:hidden"
              onClick={() => setIsInspectorOpen(false)}
            />

            {/* Slide-over / Dock Container */}
            <div className="fixed top-0 right-0 h-full w-[420px] max-w-[90vw] z-50 bg-[#0d1117]/95 backdrop-blur-md border-l border-[#1f2937] p-4 flex flex-col shadow-2xl overflow-y-auto 2xl:relative 2xl:top-auto 2xl:right-auto 2xl:h-auto 2xl:w-[400px] 2xl:max-w-none 2xl:z-auto 2xl:bg-[#0d1117] 2xl:border 2xl:border-[#1f2937] 2xl:rounded-lg 2xl:shadow-sm 2xl:backdrop-blur-none shrink-0">
              <div className="flex items-center justify-between pb-2.5 border-b border-slate-800 mb-3">
                <div className="flex items-center gap-2">
                  <Eye className="w-4 h-4 text-sky-400" />
                  <span className="text-sm font-bold text-slate-200 font-heading">
                    Host Incident Attribution
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setIsInspectorOpen(false)}
                  title="Close Inspector"
                  className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-[#161b22] cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <p className="text-xs text-slate-400 font-sans mb-3">
                {selectedNodeId
                  ? `Inspecting node telemetry & TreeSHAP drivers for ${selectedNodeId}`
                  : 'Click any graph node to inspect why it was flagged or view baseline telemetry.'}
              </p>
              <TreeShapInspector
                explanation={selectedAlert?.explanation ?? null}
                alertId={selectedAlert?.alert_id}
                targetEntity={
                  selectedAlert
                    ? `${selectedAlert.src_ip} (${selectedAlert.attack_type || 'FLOW'})`
                    : selectedNodeId
                    ? selectedNodeId
                    : undefined
                }
                height={580}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
};
