import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import anime from 'animejs';
import type { GraphEdge, GraphNode, GraphStateResponse } from '@/lib/types';
import { AlertTriangle, Network, RefreshCw, X, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface NetworkTopologyCanvasProps {
  graphState: GraphStateResponse | null;
  onRefresh?: () => void;
  isLoading?: boolean;
  error?: string | null;
  height?: number;
  selectedNodeId?: string | null;
  onSelectNode?: (node: GraphNode) => void;
}

export const NetworkTopologyCanvas: React.FC<NetworkTopologyCanvasProps> = ({
  graphState,
  onRefresh,
  isLoading = false,
  error = null,
  height = 430,
  selectedNodeId = null,
  onSelectNode,
}) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const prevNodesHash = useRef<string>('');

  // Zoom and Pan transform state (CyberWatch reference pattern)
  const [transform, setTransform] = useState<{ scale: number; tx: number; ty: number }>({
    scale: 1,
    tx: 0,
    ty: 0,
  });

  const [isDragging, setIsDragging] = useState(false);
  const isDraggingRef = useRef(false);
  const startPosRef = useRef({ x: 0, y: 0 });
  const hasMovedRef = useRef(false);

  const nodes: GraphNode[] = graphState?.nodes || [];
  const edges: GraphEdge[] = graphState?.edges || [];
  const flaggedPivots = graphState?.flagged_pivots || [];
  const flaggedPivotsStr = flaggedPivots.join(',');

  // Derive activeNode from external prop or local selection
  const activeNode = useMemo(() => {
    if (selectedNodeId) {
      return nodes.find((n) => n.id === selectedNodeId) || selectedNode;
    }
    return selectedNode;
  }, [selectedNodeId, nodes, selectedNode]);

  // Zoom manipulation helper
  const zoomBy = useCallback((factor: number, cx?: number, cy?: number) => {
    setTransform((prev) => {
      const svg = svgRef.current;
      const rect = svg ? svg.getBoundingClientRect() : { left: 0, top: 0, width: 800, height: 600 };
      const px = cx !== undefined ? cx - rect.left : rect.width / 2;
      const py = cy !== undefined ? cy - rect.top : rect.height / 2;

      const newScale = Math.max(0.3, Math.min(4.0, prev.scale * factor));
      const k = newScale / prev.scale;
      const newTx = px - (px - prev.tx) * k;
      const newTy = py - (py - prev.ty) * k;

      return { scale: newScale, tx: newTx, ty: newTy };
    });
  }, []);

  const zoomReset = useCallback(() => {
    setTransform({ scale: 1, tx: 0, ty: 0 });
  }, []);

  // Wheel zoom handler
  const handleWheel = useCallback(
    (e: React.WheelEvent<SVGSVGElement>) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.15 : 0.87;
      zoomBy(factor, e.clientX, e.clientY);
    },
    [zoomBy]
  );

  // Drag to pan handlers
  const handleMouseDown = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    // Only drag on left click
    if (e.button !== 0) return;
    isDraggingRef.current = true;
    setIsDragging(true);
    hasMovedRef.current = false;
    startPosRef.current = { x: e.clientX, y: e.clientY };
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - startPosRef.current.x;
    const dy = e.clientY - startPosRef.current.y;

    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
      hasMovedRef.current = true;
    }

    startPosRef.current = { x: e.clientX, y: e.clientY };
    setTransform((prev) => ({
      ...prev,
      tx: prev.tx + dx,
      ty: prev.ty + dy,
    }));
  }, []);

  const handleMouseUp = useCallback(() => {
    isDraggingRef.current = false;
    setIsDragging(false);
  }, []);

  // Node click handler with drag prevention
  const handleNodeClick = useCallback(
    (node: GraphNode, e: React.MouseEvent) => {
      e.stopPropagation();
      // If user was dragging canvas, don't trigger node click
      if (hasMovedRef.current) return;

      setSelectedNode(node);
      onSelectNode?.(node);
    },
    [onSelectNode]
  );

  // Reusable Anime.js topology shift animation tied strictly to real state changes
  useEffect(() => {
    if (!graphState || nodes.length === 0) return;

    const currentHash = `${nodes.length}-${edges.length}-${flaggedPivotsStr}`;
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
  }, [graphState, nodes.length, edges.length, flaggedPivotsStr]);

  return (
    <div
      className="bg-[#0d1117] border border-[#21262d] rounded flex flex-col relative overflow-hidden select-none min-h-[540px] flex-1"
      style={height ? { minHeight: `${height}px` } : undefined}
    >
      {/* Panel Header */}
      <div className="bg-[#161b22] border-b border-[#21262d] px-3 py-2 flex justify-between items-center font-heading text-xs font-bold tracking-wider uppercase text-[#8b949e] select-none z-10">
        <div className="flex items-center gap-2">
          <span className="text-[#e6edf3]">COMPONENT 02 //</span>
          <span>TEMPORAL HOST INTERACTION TOPOLOGY & LATERAL PIVOT CANVAS</span>
          <span className="text-[#30363d]">|</span>
          <span className="text-[#8b949e]">TIER 3 (GRAPH TOPOLOGY)</span>
        </div>

        <div className="flex items-center gap-3">
          {/* Legend */}
          <div className="flex items-center gap-3 font-mono text-xs">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#F85149]" />
              <span className="text-slate-300">PIVOT HOST</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#58a6ff]" />
              <span className="text-slate-300">INTERNAL</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#8b5cf6]" />
              <span className="text-slate-300">DMZ</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#3FB950]" />
              <span className="text-slate-300">ENDPOINT</span>
            </div>
          </div>

          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="p-1 text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#21262d] rounded border border-[#30363d] cursor-pointer disabled:opacity-50"
              title="Refresh topology state"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          )}
        </div>
      </div>

      {/* SVG Canvas Area with Pan & Zoom */}
      <div className="flex-1 relative bg-[#090b0e] overflow-hidden select-none min-h-[460px]">
        {/* Floating CyberWatch-style Zoom Controls */}
        <div className="absolute top-3 right-3 flex flex-col gap-1 z-20 font-mono">
          <button
            onClick={() => zoomBy(1.25)}
            className="w-8 h-8 flex items-center justify-center bg-[#161b22]/90 hover:bg-[#21262d] border border-[#30363d] text-[#e6edf3] hover:text-[#58a6ff] hover:border-[#58a6ff]/50 rounded cursor-pointer transition-colors text-xs"
            title="Zoom In (+)"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => zoomBy(0.8)}
            className="w-8 h-8 flex items-center justify-center bg-[#161b22]/90 hover:bg-[#21262d] border border-[#30363d] text-[#e6edf3] hover:text-[#58a6ff] hover:border-[#58a6ff]/50 rounded cursor-pointer transition-colors text-xs"
            title="Zoom Out (−)"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={zoomReset}
            className="w-8 h-8 flex items-center justify-center bg-[#161b22]/90 hover:bg-[#21262d] border border-[#30363d] text-[#e6edf3] hover:text-[#58a6ff] hover:border-[#58a6ff]/50 rounded cursor-pointer transition-colors text-xs"
            title="Reset View (⟲)"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        {/* Bottom Interactive Hint Strip */}
        <div className="absolute bottom-3 left-1/2 -translate-x-1/2 font-mono text-[11px] text-[#527194] tracking-[0.14em] uppercase pointer-events-none whitespace-nowrap bg-[#060c14]/90 px-3 py-1 rounded border border-[#162b47] z-10 shadow-sm">
          SCROLL TO ZOOM · DRAG TO PAN · CLICK A NODE TO INSPECT WITH TREESHAP
        </div>

        {error ? (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center gap-3 font-mono text-xs">
            <div className="w-10 h-10 rounded-full bg-[#f85149]/10 border border-[#f85149]/30 flex items-center justify-center text-[#f85149]">
              <AlertTriangle className="w-5 h-5 stroke-2" />
            </div>
            <div className="flex flex-col gap-1 max-w-md">
              <span className="text-[#f85149] font-semibold text-sm">Failed to Load Network Topology</span>
              <p className="text-[#8b949e] text-xs leading-relaxed break-words">{error}</p>
            </div>
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isLoading}
                className="mt-2 inline-flex items-center gap-2 px-3 py-1.5 rounded-[2px] bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] border border-[#30363d] cursor-pointer disabled:opacity-50 transition-colors text-xs font-mono"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
                <span>Retry Connection</span>
              </button>
            )}
          </div>
        ) : isLoading ? (
          <div className="h-full flex flex-col items-center justify-center text-[#8b949e] gap-2 font-mono text-xs">
            <RefreshCw className="w-7 h-7 stroke-1 text-[#8b949e] animate-spin" />
            <span>Loading network communication graph from /graph/state...</span>
          </div>
        ) : nodes.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-[#8b949e] gap-2 font-mono text-xs">
            <Network className="w-8 h-8 stroke-1 text-[#8b949e]" />
            <span>No network topology data available.</span>
          </div>
        ) : (
          <svg
            ref={svgRef}
            viewBox="0 0 800 600"
            className="w-full h-full cursor-grab active:cursor-grabbing"
            preserveAspectRatio="xMidYMid meet"
            onWheel={handleWheel}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
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
            <rect width="100%" height="100%" fill="url(#dotGrid)" />

            {/* Viewport <g> receiving transform matrix for pan/zoom */}
            <g
              id="viewport"
              transform={`translate(${transform.tx}, ${transform.ty}) scale(${transform.scale})`}
              style={{ transformOrigin: '0 0', transition: isDragging ? 'none' : 'transform 0.05s ease-out' }}
            >
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
                  const isSelected = activeNode?.id === node.id;

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
                      data-node-id={node.id}
                      onClick={(e) => handleNodeClick(node, e)}
                      className="cursor-pointer group"
                      style={{ pointerEvents: 'all' }}
                    >
                      {/* Active selection pulse ring */}
                      {isSelected && (
                        <circle
                          cx={node.x}
                          cy={node.y}
                          r={baseRadius + 5}
                          fill="none"
                          stroke="#58a6ff"
                          strokeWidth="2"
                          strokeDasharray="3 2"
                          className="animate-spin origin-center"
                          style={{
                            transformOrigin: `${node.x}px ${node.y}px`,
                            pointerEvents: 'none',
                          }}
                        />
                      )}

                      {/* Base Node Circle */}
                      <circle
                        cx={node.x}
                        cy={node.y}
                        r={baseRadius}
                        fill={nodeColor}
                        onClick={(e) => handleNodeClick(node, e)}
                        className={`${isPivot ? 'svg-node-pivot' : ''} transition-transform group-hover:scale-125`}
                        style={{ transformOrigin: `${node.x}px ${node.y}px`, pointerEvents: 'all' }}
                      />

                      {/* Node Label */}
                      {(isPivot || node.role === 'INTERNAL_SERVER' || isSelected) && (
                        <text
                          x={node.x}
                          y={node.y - baseRadius - 5}
                          textAnchor="middle"
                          onClick={(e) => handleNodeClick(node, e)}
                          style={{ pointerEvents: 'all' }}
                          className={`font-mono text-xs select-none cursor-pointer ${
                            isPivot ? 'fill-[#F85149] font-bold' : isSelected ? 'fill-[#58a6ff] font-bold' : 'fill-slate-300'
                          }`}
                        >
                          {isPivot ? `[PIVOT] ${node.id}` : node.id}
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
            </g>
          </svg>
        )}

        {/* Telemetry Overlay Popover for selected host */}
        {activeNode && (
          <div className="absolute bottom-12 right-4 bg-[#0e1623]/95 backdrop-blur-md border border-[#233348] rounded-lg p-4 w-84 font-sans shadow-2xl z-20 select-text">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#233348]">
              <div className="flex items-center gap-2">
                <span
                  className={`w-2.5 h-2.5 rounded-full ${
                    activeNode.is_pivot
                      ? 'bg-[#f85149] shadow-[0_0_10px_#f85149]'
                      : 'bg-[#3fb950] shadow-[0_0_10px_#3fb950]'
                  }`}
                />
                <span
                  className={`font-heading font-extrabold text-xs uppercase tracking-wider ${
                    activeNode.is_pivot ? 'text-[#f85149]' : 'text-[#3fb950]'
                  }`}
                >
                  {activeNode.is_pivot ? 'ALERT: LATERAL PIVOT HOST' : `HOST: ${activeNode.role}`}
                </span>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-slate-400 hover:text-slate-100 p-1 rounded hover:bg-slate-800/60 cursor-pointer transition-colors"
                title="Close overlay"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Key-Value Metrics List with clear vertical rhythm */}
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400 font-semibold uppercase tracking-wider text-xs">
                  IP Address:
                </span>
                <span className="font-mono font-bold text-slate-100 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/60 tabular-nums">
                  {activeNode.id}
                </span>
              </div>

              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400 font-semibold uppercase tracking-wider text-xs">
                  Out-Degree:
                </span>
                <span className="font-mono font-semibold text-slate-200 tabular-nums">
                  {activeNode.out_degree}{' '}
                  <span className="text-slate-400 text-xs font-normal">(In: {activeNode.in_degree})</span>
                </span>
              </div>

              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400 font-semibold uppercase tracking-wider text-xs">
                  Degree Z-Score:
                </span>
                <span
                  className={`font-mono font-bold tabular-nums ${
                    activeNode.degree_zscore > 2.0 ? 'text-[#f85149]' : 'text-slate-200'
                  }`}
                >
                  +{activeNode.degree_zscore.toFixed(2)}σ
                </span>
              </div>

              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400 font-semibold uppercase tracking-wider text-xs">
                  Jaccard Novelty:
                </span>
                <span
                  className={`font-mono font-bold tabular-nums ${
                    activeNode.jaccard_novelty > 0.4 ? 'text-[#f85149]' : 'text-slate-200'
                  }`}
                >
                  {(activeNode.jaccard_novelty * 100).toFixed(1)}%
                </span>
              </div>

              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400 font-semibold uppercase tracking-wider text-xs">
                  PageRank Shift:
                </span>
                <span className="font-mono font-bold text-[#38bdf8] tabular-nums">
                  +{activeNode.pagerank_delta.toFixed(4)}
                </span>
              </div>

              {activeNode.reasons && activeNode.reasons.length > 0 && (
                <div className="mt-3 pt-2.5 border-t border-red-900/40 bg-red-950/25 p-2.5 rounded-md text-xs">
                  <span className="font-bold text-[#f85149] uppercase tracking-wider block mb-1.5 text-xs">
                    PIVOT DETECTION FLAGS:
                  </span>
                  <ul className="space-y-1 text-red-300 font-mono text-xs">
                    {activeNode.reasons.map((r: string, i: number) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-red-500 font-bold">•</span>
                        <span>{r}</span>
                      </li>
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
