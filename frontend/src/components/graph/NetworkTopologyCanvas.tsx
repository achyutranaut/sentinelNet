import React, { useEffect, useRef, useState } from 'react';
import anime from 'animejs';
import type { GraphEdge, GraphNode, GraphStateResponse } from '@/lib/types';
import { Network, RefreshCw, X } from 'lucide-react';

interface NetworkTopologyCanvasProps {
  graphState: GraphStateResponse | null;
  onRefresh?: () => void;
  isLoading?: boolean;
  height?: number;
}

export const NetworkTopologyCanvas: React.FC<NetworkTopologyCanvasProps> = ({
  graphState,
  onRefresh,
  isLoading = false,
  height = 430,
}) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const prevNodesHash = useRef<string>('');

  const nodes: GraphNode[] = graphState?.nodes || [];
  const edges: GraphEdge[] = graphState?.edges || [];
  const flaggedPivots = graphState?.flagged_pivots || [];

  // Reusable Anime.js topology shift animation tied strictly to real state changes
  useEffect(() => {
    if (!graphState || nodes.length === 0) return;

    const currentHash = `${nodes.length}-${edges.length}-${flaggedPivots.join(',')}`;
    if (currentHash !== prevNodesHash.current) {
      prevNodesHash.current = currentHash;

      // 1. Animate threat edges with stagger indicating chronological infection path
      anime({
        targets: '.svg-edge-threat',
        strokeDashoffset: [400, 0],
        duration: 350,
        delay: anime.stagger(45),
        easing: 'easeOutQuad',
      });

      // 2. Pulse pivot nodes
      anime({
        targets: '.svg-node-pivot',
        r: [6, 11, 8],
        duration: 300,
        easing: 'easeOutQuad',
      });
    }
  }, [graphState, nodes.length, edges.length, flaggedPivots]);

  return (
    <div
      className="bg-[#0d1117] border border-[#21262d] rounded-[2px] flex flex-col relative overflow-hidden"
      style={{ height: `${height}px` }}
    >
      {/* Panel Header */}
      <div className="bg-[#161b22] border-b border-[#21262d] px-2.5 py-1.5 flex justify-between items-center font-heading text-[10px] font-bold tracking-wider uppercase text-[#8b949e] select-none">
        <div className="flex items-center gap-2">
          <span className="text-[#e6edf3]">COMPONENT 02 //</span>
          <span>TEMPORAL HOST INTERACTION TOPOLOGY &amp; LATERAL PIVOT CANVAS</span>
          <span className="text-[#30363d]">|</span>
          <span className="text-[#8b949e]">TIER 3 (GRAPH TOPOLOGY)</span>
        </div>

        <div className="flex items-center gap-3">
          {/* Legend */}
          <div className="flex items-center gap-3 font-mono text-[9px]">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-[1px] bg-[#F85149]" />
              <span>PIVOT HOST</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-[1px] bg-[#3b82f6]" />
              <span>INTERNAL SRV</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-[1px] bg-[#8b5cf6]" />
              <span>DMZ</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-[1px] bg-[#3FB950]" />
              <span>ENDPOINT</span>
            </div>
          </div>

          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="p-1 text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#21262d] rounded-[2px] border border-[#30363d] cursor-pointer disabled:opacity-50"
              title="Refresh topology state"
            >
              <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          )}
        </div>
      </div>

      {/* Hand-written SVG Canvas */}
      <div className="flex-1 relative bg-[#090b0e] overflow-hidden select-none">
        {nodes.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-[#8b949e] gap-2 font-mono text-xs">
            <Network className="w-8 h-8 stroke-1 text-[#8b949e]" />
            <span>Loading network communication graph from /graph/state...</span>
          </div>
        ) : (
          <svg
            ref={svgRef}
            viewBox="0 0 800 600"
            className="w-full h-full"
            preserveAspectRatio="xMidYMid meet"
          >
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="16"
                refY="5"
                markerWidth="5"
                markerHeight="5"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#30363d" />
              </marker>
              <marker
                id="arrow-threat"
                viewBox="0 0 10 10"
                refX="18"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#F85149" />
              </marker>
            </defs>

            {/* Background Grid Accent */}
            <pattern id="dotGrid" width="24" height="24" patternUnits="userSpaceOnUse">
              <circle cx="2" cy="2" r="0.8" fill="#161b22" />
            </pattern>
            <rect width="800" height="600" fill="url(#dotGrid)" />

            {/* Edges */}
            <g id="svg-edges">
              {edges.map((edge, idx) => {
                const isThreat =
                  flaggedPivots.includes(edge.source) ||
                  flaggedPivots.includes(edge.target) ||
                  edge.color === '#ef4444' ||
                  edge.color === '#F85149';

                return (
                  <line
                    key={`edge-${edge.source}-${edge.target}-${idx}`}
                    x1={edge.source_x}
                    y1={edge.source_y}
                    x2={edge.target_x}
                    y2={edge.target_y}
                    stroke={isThreat ? '#F85149' : '#30363d'}
                    strokeWidth={isThreat ? 1.8 : 1}
                    strokeDasharray={isThreat ? '400' : 'none'}
                    className={isThreat ? 'svg-edge-threat opacity-95' : 'opacity-50'}
                    markerEnd={isThreat ? 'url(#arrow-threat)' : 'url(#arrow)'}
                  />
                );
              })}
            </g>

            {/* Nodes */}
            <g id="svg-nodes">
              {nodes.map((node) => {
                const isPivot = node.is_pivot || flaggedPivots.includes(node.id);
                const isSelected = selectedNode?.id === node.id;

                let nodeColor = '#3FB950'; // endpoint default
                let baseRadius = 6.0;

                if (isPivot) {
                  nodeColor = '#F85149';
                  baseRadius = 8.5;
                } else if (node.role === 'INTERNAL_SERVER' || node.id.includes('10.0.1')) {
                  nodeColor = '#3b82f6';
                  baseRadius = 7.0;
                } else if (node.role === 'DMZ_SERVER' || node.id.includes('192.168.1')) {
                  nodeColor = '#8b5cf6';
                  baseRadius = 6.5;
                }

                return (
                  <g
                    key={`node-${node.id}`}
                    onClick={() => setSelectedNode(node)}
                    className="cursor-pointer"
                  >
                    {/* Active highlight ring */}
                    {isSelected && (
                      <circle
                        cx={node.x}
                        cy={node.y}
                        r={baseRadius + 4}
                        fill="none"
                        stroke="#e6edf3"
                        strokeWidth="1.5"
                      />
                    )}

                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={baseRadius}
                      fill={nodeColor}
                      className={isPivot ? 'svg-node-pivot' : ''}
                    />

                    {/* Show label for pivots and critical servers */}
                    {(isPivot || node.role === 'INTERNAL_SERVER' || isSelected) && (
                      <text
                        x={node.x}
                        y={node.y - baseRadius - 4}
                        textAnchor="middle"
                        className={`font-mono text-[8.5px] select-none ${
                          isPivot ? 'fill-[#F85149] font-bold' : 'fill-[#8b949e]'
                        }`}
                      >
                        {isPivot ? `[PIVOT] ${node.id}` : node.id}
                      </text>
                    )}
                  </g>
                );
              })}
            </g>
          </svg>
        )}

        {/* Telemetry Overlay Popover for selected host */}
        {selectedNode && (
          <div className="absolute bottom-2 right-2 bg-[#161b22] border border-[#21262d] rounded-[2px] p-2.5 max-w-[260px] font-mono text-[10px] z-20 shadow-none">
            <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-[#21262d]">
              <span
                className={`font-heading font-bold text-[10px] uppercase ${
                  selectedNode.is_pivot ? 'text-[#F85149]' : 'text-[#3FB950]'
                }`}
              >
                {selectedNode.is_pivot ? 'ALERT: LATERAL PIVOT HOST' : `HOST: ${selectedNode.role}`}
              </span>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-[#8b949e] hover:text-[#e6edf3] p-0.5 cursor-pointer"
              >
                <X className="w-3 h-3" />
              </button>
            </div>

            <div className="space-y-1 text-[#e6edf3]">
              <div>
                <span className="text-[#8b949e]">IP:</span> <strong className="text-[#e6edf3]">{selectedNode.id}</strong>
              </div>
              <div>
                <span className="text-[#8b949e]">Out-Degree:</span> {selectedNode.out_degree} (In: {selectedNode.in_degree})
              </div>
              <div>
                <span className="text-[#8b949e]">Degree Z-Score:</span>{' '}
                <span className={selectedNode.degree_zscore > 2.0 ? 'text-[#F85149] font-bold' : 'text-[#e6edf3]'}>
                  +{selectedNode.degree_zscore.toFixed(2)}σ
                </span>
              </div>
              <div>
                <span className="text-[#8b949e]">Jaccard Novelty:</span>{' '}
                <span className={selectedNode.jaccard_novelty > 0.4 ? 'text-[#F85149] font-bold' : 'text-[#e6edf3]'}>
                  {(selectedNode.jaccard_novelty * 100).toFixed(0)}%
                </span>
              </div>
              <div>
                <span className="text-[#8b949e]">PageRank Shift:</span>{' '}
                <span className="text-[#3b82f6]">+{selectedNode.pagerank_delta.toFixed(4)}</span>
              </div>

              {selectedNode.reasons && selectedNode.reasons.length > 0 && (
                <div className="pt-1 border-t border-[#21262d] mt-1 text-[9px] text-[#F85149]">
                  <strong>PIVOT FLAGS:</strong>
                  <ul className="list-disc list-inside mt-0.5">
                    {selectedNode.reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
