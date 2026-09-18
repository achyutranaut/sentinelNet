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
      className="bg-[#0d1117] border border-[#21262d] rounded-[2px] flex flex-col relative overflow-hidden select-none"
      style={{ height: `${height}px` }}
    >
      {/* Panel Header */}
      <div className="bg-[#161b22] border-b border-[#21262d] px-2.5 py-1.5 flex justify-between items-center font-heading text-[10px] font-bold tracking-wider uppercase text-[#8b949e] select-none z-10">
        <div className="flex items-center gap-2">
          <span className="text-[#e6edf3]">COMPONENT 02 //</span>
          <span>TEMPORAL HOST INTERACTION TOPOLOGY & LATERAL PIVOT CANVAS</span>
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
              <span className="w-1.5 h-1.5 rounded-[1px] bg-[#58a6ff]" />
              <span>INTERNAL</span>
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

      {/* SVG Canvas Area with Pan & Zoom */}
      <div className="flex-1 relative bg-[#090b0e] overflow-hidden select-none">
        {/* Floating CyberWatch-style Zoom Controls */}
        <div className="absolute top-3 right-3 flex flex-col gap-1 z-20 font-mono">
          <button
            onClick={() => zoomBy(1.25)}
            className="w-7 h-7 flex items-center justify-center bg-[#161b22]/90 hover:bg-[#21262d] border border-[#30363d] text-[#e6edf3] hover:text-[#58a6ff] hover:border-[#58a6ff]/50 rounded-[2px] cursor-pointer transition-colors text-xs"
            title="Zoom In (+)"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => zoomBy(0.8)}
            className="w-7 h-7 flex items-center justify-center bg-[#161b22]/90 hover:bg-[#21262d] border border-[#30363d] text-[#e6edf3] hover:text-[#58a6ff] hover:border-[#58a6ff]/50 rounded-[2px] cursor-pointer transition-colors text-xs"
            title="Zoom Out (−)"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={zoomReset}
            className="w-7 h-7 flex items-center justify-center bg-[#161b22]/90 hover:bg-[#21262d] border border-[#30363d] text-[#e6edf3] hover:text-[#58a6ff] hover:border-[#58a6ff]/50 rounded-[2px] cursor-pointer transition-colors text-xs"
            title="Reset View (⟲)"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Bottom Interactive Hint Strip */}
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 font-mono text-[8px] text-[#527194] tracking-[0.16em] uppercase pointer-events-none whitespace-nowrap bg-[#060c14]/90 px-2.5 py-1 rounded-[2px] border border-[#162b47] z-10">
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
                          y={node.y - baseRadius - 4}
                          textAnchor="middle"
                          onClick={(e) => handleNodeClick(node, e)}
                          style={{ pointerEvents: 'all' }}
                          className={`font-mono text-[8.5px] select-none cursor-pointer ${
                            isPivot ? 'fill-[#F85149] font-bold' : isSelected ? 'fill-[#58a6ff] font-bold' : 'fill-[#8b949e]'
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
          <div className="absolute bottom-10 right-3 bg-[#161b22] border border-[#21262d] rounded-[2px] p-2.5 max-w-[260px] font-mono text-[10px] z-20 shadow-lg">
            <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-[#21262d]">
              <span
                className={`font-heading font-bold text-[10px] uppercase ${
                  activeNode.is_pivot ? 'text-[#F85149]' : 'text-[#3FB950]'
                }`}
              >
                {activeNode.is_pivot ? 'ALERT: LATERAL PIVOT HOST' : `HOST: ${activeNode.role}`}
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
                <span className="text-[#8b949e]">IP:</span> <strong className="text-[#e6edf3]">{activeNode.id}</strong>
              </div>
              <div>
                <span className="text-[#8b949e]">Out-Degree:</span> {activeNode.out_degree} (In: {activeNode.in_degree})
              </div>
              <div>
                <span className="text-[#8b949e]">Degree Z-Score:</span>{' '}
                <span className={activeNode.degree_zscore > 2.0 ? 'text-[#F85149] font-bold' : 'text-[#e6edf3]'}>
                  +{activeNode.degree_zscore.toFixed(2)}σ
                </span>
              </div>
              <div>
                <span className="text-[#8b949e]">Jaccard Novelty:</span>{' '}
                <span className={activeNode.jaccard_novelty > 0.4 ? 'text-[#F85149] font-bold' : 'text-[#e6edf3]'}>
                  {(activeNode.jaccard_novelty * 100).toFixed(0)}%
                </span>
              </div>
              <div>
                <span className="text-[#8b949e]">PageRank Shift:</span>{' '}
                <span className="text-[#3b82f6]">+{activeNode.pagerank_delta.toFixed(4)}</span>
              </div>

              {activeNode.reasons && activeNode.reasons.length > 0 && (
                <div className="pt-1 border-t border-[#21262d] mt-1 text-[9px] text-[#F85149]">
                  <strong>PIVOT FLAGS:</strong>
                  <ul className="list-disc list-inside mt-0.5">
                    {activeNode.reasons.map((r: string, i: number) => (
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
