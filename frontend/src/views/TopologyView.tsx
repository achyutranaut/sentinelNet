import React from 'react';
import { Network, RefreshCw, Eye } from 'lucide-react';
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
  const nodes = graphState?.nodes || [];
  const edges = graphState?.edges || [];
  const pivots = graphState?.flagged_pivots || [];

  const pivotCount = pivots.length || nodes.filter((n) => n.is_pivot).length;
  const internalCount = nodes.filter((n) => n.role === 'INTERNAL_SERVER' || n.id.includes('10.0.1')).length;
  const dmzCount = nodes.filter((n) => n.role === 'DMZ_SERVER' || n.id.includes('192.168.1')).length;
  const endpointCount = nodes.length - pivotCount - internalCount - dmzCount;

  return (
    <div className="space-y-6">
      {/* Page Header & Summary Strip */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-[#0d1117] border border-[#1f2937] p-4 rounded-lg shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2 font-heading">
            <Network className="w-5 h-5 text-purple-400" />
            <span>Temporal Host Interaction & Lateral Pivot Topology</span>
          </h1>
          <p className="text-xs text-slate-400 font-sans mt-1">
            Tier 3 Graph Neural Network & Degree Z-Score novelty analysis tracking chronological infection paths
          </p>
        </div>

        <div className="flex items-center gap-4 font-mono text-xs">
          <div className="bg-slate-900 border border-slate-800 px-3 py-1.5 rounded">
            <span className="text-slate-400">Nodes:</span>{' '}
            <strong className="text-slate-100">{nodes.length}</strong>
          </div>
          <div className="bg-slate-900 border border-slate-800 px-3 py-1.5 rounded">
            <span className="text-slate-400">Edges:</span>{' '}
            <strong className="text-slate-100">{edges.length}</strong>
          </div>
          <div className="bg-purple-950/50 border border-purple-800/40 px-3 py-1.5 rounded">
            <span className="text-purple-300">Pivots:</span>{' '}
            <strong className="text-purple-200">{pivotCount}</strong>
          </div>
          <button
            type="button"
            onClick={onRefreshGraph}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 font-sans text-xs cursor-pointer transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh State</span>
          </button>
        </div>
      </div>

      {/* Main Canvas + Side Inspection Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Full-Width Topology Graph Canvas (8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          <NetworkTopologyCanvas
            graphState={graphState}
            onRefresh={onRefreshGraph}
            isLoading={isLoading}
            error={error}
            height={680}
            selectedNodeId={selectedNodeId}
            onSelectNode={onSelectNode}
          />

          {/* Proper Legend Panel (Fixing Problem #1 and #6) */}
          <div className="bg-[#0d1117] border border-[#1f2937] rounded-lg p-4 shadow-sm">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 font-heading">
              Network Topology Node Classification & Legend
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              {/* Pivot Host */}
              <div className="p-3 rounded bg-red-950/30 border border-red-900/40 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-xs font-bold text-red-400">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#f85149] shadow-[0_0_8px_#f85149]" />
                    <span>Compromised Pivot</span>
                  </span>
                  <span className="text-xs font-mono font-bold text-red-300 bg-red-900/60 px-1.5 py-0.5 rounded">
                    {pivotCount}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed font-sans">
                  Degree Z-score &gt; +2.5σ or high Jaccard novelty. Infection vector spreading internally.
                </p>
              </div>

              {/* Internal Server */}
              <div className="p-3 rounded bg-sky-950/30 border border-sky-900/40 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-xs font-bold text-sky-400">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#38bdf8] shadow-[0_0_8px_#38bdf8]" />
                    <span>Internal Server</span>
                  </span>
                  <span className="text-xs font-mono font-bold text-sky-300 bg-sky-900/60 px-1.5 py-0.5 rounded">
                    {internalCount}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed font-sans">
                  Enterprise subnet assets (<code className="text-slate-300">10.0.1.x</code>). Core infrastructure targets.
                </p>
              </div>

              {/* DMZ Gateway */}
              <div className="p-3 rounded bg-purple-950/30 border border-purple-900/40 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-xs font-bold text-purple-400">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#bc8cff] shadow-[0_0_8px_#bc8cff]" />
                    <span>DMZ Gateway</span>
                  </span>
                  <span className="text-xs font-mono font-bold text-purple-300 bg-purple-900/60 px-1.5 py-0.5 rounded">
                    {dmzCount}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed font-sans">
                  Perimeter bastion hosts (<code className="text-slate-300">192.168.1.x</code>) facing incoming connections.
                </p>
              </div>

              {/* Endpoint */}
              <div className="p-3 rounded bg-emerald-950/30 border border-emerald-900/40 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-xs font-bold text-emerald-400">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#3fb950] shadow-[0_0_8px_#3fb950]" />
                    <span>Workstation</span>
                  </span>
                  <span className="text-xs font-mono font-bold text-emerald-300 bg-emerald-900/60 px-1.5 py-0.5 rounded">
                    {endpointCount}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed font-sans">
                  Standard endpoints (<code className="text-slate-300">172.16.0.x</code>) displaying nominal traffic patterns.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Side Triage Panel: TreeSHAP Inspector + Host Attribution (4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <div className="bg-[#0d1117] border border-[#1f2937] rounded-lg p-4 shadow-sm">
            <h2 className="text-sm font-bold text-slate-200 font-heading mb-1 flex items-center gap-2">
              <Eye className="w-4 h-4 text-sky-400" />
              <span>Host Incident Attribution</span>
            </h2>
            <p className="text-xs text-slate-400 font-sans mb-3">
              Click any graph node to inspect why it was flagged or view baseline telemetry.
            </p>
            <TreeShapInspector
              explanation={selectedAlert?.explanation ?? null}
              alertId={selectedAlert?.alert_id}
              targetEntity={selectedAlert ? `${selectedAlert.src_ip} (${selectedAlert.attack_type || 'FLOW'})` : undefined}
              height={580}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
