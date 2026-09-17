"""Tier 3: Dynamic Network Interaction Graph (Anime.js v4 SVG Topology Morphing).

Renders the temporal host interaction graph with SVG paths.
When stealth lateral movement is detected, Anime.js v4 morphs edge paths
and uses stagger() along the chronological infection path to make internal pivoting legible.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
import networkx as nx
import numpy as np
import pandas as pd
import streamlit.components.v1 as components


def render_network_topology_canvas(
    df_window: pd.DataFrame,
    flagged_pivots: List[Dict[str, Any]],
    height: int = 460
) -> None:
    """Renders interactive SVG Network Graph with Anime.js v4 path morphing and staggered reveals."""
    # Build NetworkX graph from flows
    G = nx.DiGraph()
    for _, row in df_window.iterrows():
        src = str(row["src_ip"])
        dst = str(row["dst_ip"])
        G.add_edge(src, dst)

    # Compute spring layout coordinates
    pos = nx.spring_layout(G, seed=42, k=0.4, iterations=40)
    
    # Normalize positions to canvas width=760, height=380
    w_canvas, h_canvas = 760, 380
    padding = 40
    
    # Normalize flagged_pivots whether dataclasses or dicts
    pivots_list = []
    for p in flagged_pivots:
        if hasattr(p, "host_ip"):
            pivots_list.append({
                "host_ip": str(p.host_ip),
                "out_degree": int(p.out_degree),
                "degree_zscore": float(p.degree_zscore),
                "jaccard_novelty": float(p.jaccard_novelty),
                "pagerank": float(p.pagerank),
                "pagerank_delta": float(p.pagerank_delta),
                "is_suspicious_pivot": bool(p.is_suspicious_pivot),
                "reasons": list(p.reasons) if hasattr(p, "reasons") else []
            })
        elif isinstance(p, dict):
            pivots_list.append(p)
    flagged_pivots = pivots_list

    nodes_data = []
    flagged_ip_set = {p["host_ip"]: p for p in flagged_pivots}

    for node in G.nodes():
        raw_x, raw_y = pos[node]
        cx = int((raw_x + 1.0) / 2.0 * (w_canvas - 2 * padding) + padding)
        cy = int((raw_y + 1.0) / 2.0 * (h_canvas - 2 * padding) + padding)

        is_pivot = node in flagged_ip_set
        node_type = "PIVOT" if is_pivot else ("SERVER" if "10.0.1." in node else ("DMZ" if "192.168.1." in node else "ENDPOINT"))

        nodes_data.append({
            "id": node,
            "cx": cx,
            "cy": cy,
            "type": node_type,
            "is_pivot": is_pivot,
            "pivot_details": flagged_ip_set.get(node, None)
        })

    node_coord_map = {n["id"]: (n["cx"], n["cy"]) for n in nodes_data}
    edges_data = []
    
    for u, v in G.edges():
        if u in node_coord_map and v in node_coord_map:
            x1, y1 = node_coord_map[u]
            x2, y2 = node_coord_map[v]
            is_threat_edge = (u in flagged_ip_set)
            edges_data.append({
                "source": u,
                "target": v,
                "x1": x1, "y1": y1,
                "x2": x2, "y2": y2,
                "is_threat_edge": is_threat_edge
            })

    nodes_json = json.dumps(nodes_data)
    edges_json = json.dumps(edges_data)
    pivots_json = json.dumps(flagged_pivots)

    anime_path = Path(__file__).resolve().parent.parent / "static" / "anime.v4.min.js"
    anime_src = "https://cdn.jsdelivr.net/npm/animejs@4.0.0"
    anime_inline_script = ""
    if anime_path.exists():
        try:
            anime_inline_script = f"<script>{anime_path.read_text()}</script>"
        except Exception:
            anime_inline_script = f'<script src="{anime_src}"></script>'
    else:
        anime_inline_script = f'<script src="{anime_src}"></script>'

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,400;0,500;0,600;1,400&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
      {anime_inline_script}
      <style>
        * {{
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }}
        body {{
          background-color: #090b0e;
          color: #e6edf3;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          overflow: hidden;
          padding: 4px;
        }}
        .graph-panel {{
          background-color: #0d1117;
          border: 1px solid #21262d;
          border-radius: 2px;
          display: flex;
          flex-direction: column;
          height: {height - 8}px;
          position: relative;
        }}
        .panel-header {{
          background-color: #161b22;
          border-bottom: 1px solid #21262d;
          padding: 6px 10px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-family: 'Space Grotesk', sans-serif;
          font-size: 10px;
          font-weight: 600;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: #8b949e;
        }}
        .legend {{
          display: flex;
          gap: 12px;
          font-size: 9.5px;
          font-family: 'IBM Plex Mono', monospace;
        }}
        .legend-item {{
          display: flex;
          align-items: center;
          gap: 4px;
        }}
        .legend-chip {{
          width: 7px;
          height: 7px;
          border-radius: 1px;
        }}
        .chip-pivot {{ background-color: #f85149; }}
        .chip-server {{ background-color: #58a6ff; }}
        .chip-endpoint {{ background-color: #3fb950; }}
        .svg-container {{
          flex: 1;
          position: relative;
          background: radial-gradient(#161b22 1px, transparent 1px);
          background-size: 20px 20px;
        }}
        svg {{
          width: 100%;
          height: 100%;
        }}
        .edge-line {{
          stroke: #30363d;
          stroke-width: 1;
          stroke-dasharray: 400;
          stroke-dashoffset: 0;
          opacity: 0.6;
        }}
        .edge-threat {{
          stroke: #f85149;
          stroke-width: 1.8;
          opacity: 0.95;
          stroke-dasharray: 400;
        }}
        .node-circle {{
          cursor: pointer;
          transition: stroke 0.15s;
        }}
        .node-circle:hover {{
          stroke: #ffffff;
          stroke-width: 2px;
        }}
        .node-label {{
          font-family: 'IBM Plex Mono', monospace;
          font-size: 8px;
          fill: #8b949e;
          pointer-events: none;
        }}
        .label-threat {{
          fill: #f85149;
          font-weight: 600;
          font-size: 9px;
        }}
        #telemetry-overlay {{
          position: absolute;
          bottom: 8px;
          right: 8px;
          background-color: #161b22;
          border: 1px solid #21262d;
          border-radius: 2px;
          padding: 8px 12px;
          font-size: 10px;
          max-width: 280px;
          display: none;
          z-index: 10;
        }}
        .overlay-title {{
          font-family: 'Space Grotesk', sans-serif;
          font-weight: 700;
          color: #f85149;
          margin-bottom: 4px;
        }}
      </style>
    </head>
    <body>
      <div class="graph-panel">
        <div class="panel-header">
          <span>TEMPORAL HOST INTERACTION TOPOLOGY (TIER 3)</span>
          <div class="legend">
            <div class="legend-item"><div class="legend-chip chip-pivot"></div><span>PIVOT HOST</span></div>
            <div class="legend-item"><div class="legend-chip chip-server"></div><span>INTERNAL SRV</span></div>
            <div class="legend-item"><div class="legend-chip chip-endpoint"></div><span>ENDPOINT</span></div>
          </div>
        </div>
        <div class="svg-container">
          <svg id="network-svg" viewBox="0 0 {w_canvas} {h_canvas}">
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="16" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#30363d" />
              </marker>
              <marker id="arrow-threat" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#f85149" />
              </marker>
            </defs>
            <g id="edges-group"></g>
            <g id="nodes-group"></g>
          </svg>
          <div id="telemetry-overlay">
            <div class="overlay-title" id="ov-title">PIVOT DETECTED</div>
            <div id="ov-details"></div>
          </div>
        </div>
      </div>

      <script>
        const nodes = {nodes_json};
        const edges = {edges_json};
        const pivots = {pivots_json};

        const svg = document.getElementById('network-svg');
        const edgesGroup = document.getElementById('edges-group');
        const nodesGroup = document.getElementById('nodes-group');
        const overlay = document.getElementById('telemetry-overlay');
        const ovTitle = document.getElementById('ov-title');
        const ovDetails = document.getElementById('ov-details');

        // Draw Edges
        edges.forEach((e, idx) => {{
          const path = document.createElementNS('http://www.w3.org/2000/svg', 'line');
          path.setAttribute('x1', e.x1);
          path.setAttribute('y1', e.y1);
          path.setAttribute('x2', e.x2);
          path.setAttribute('y2', e.y2);
          path.setAttribute('class', e.is_threat_edge ? 'edge-line edge-threat' : 'edge-line');
          path.setAttribute('marker-end', e.is_threat_edge ? 'url(#arrow-threat)' : 'url(#arrow)');
          path.id = `edge-${{idx}}`;
          edgesGroup.appendChild(path);
        }});

        // Draw Nodes
        nodes.forEach((n) => {{
          const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
          
          const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          circle.setAttribute('cx', n.cx);
          circle.setAttribute('cy', n.cy);
          circle.setAttribute('class', n.is_pivot ? 'node-circle node-pivot' : 'node-circle');
          circle.id = `node-${{n.id.replace(/\\./g, '_')}}`;

          let color = '#3fb950'; // default endpoint
          let radius = 5;
          if (n.is_pivot) {{
            color = '#f85149';
            radius = 8;
          }} else if (n.type === 'SERVER') {{
            color = '#58a6ff';
            radius = 7;
          }} else if (n.type === 'DMZ') {{
            color = '#bc8cff';
            radius = 6;
          }}

          circle.setAttribute('r', radius);
          circle.setAttribute('fill', color);

          // Tooltip click handler
          circle.addEventListener('click', () => {{
            overlay.style.display = 'block';
            if (n.is_pivot && n.pivot_details) {{
              const p = n.pivot_details;
              ovTitle.textContent = `ALERT: COMPROMISED PIVOT HOST`;
              ovTitle.style.color = '#f85149';
              ovDetails.innerHTML = `
                <b>Host:</b> ${{n.id}}<br>
                <b>Out-Degree:</b> ${{p.out_degree}}<br>
                <b>Z-Score:</b> +${{p.degree_zscore.toFixed(2)}}σ<br>
                <b>Jaccard Novelty:</b> ${{(p.jaccard_novelty * 100).toFixed(0)}}%<br>
                <b>PageRank Delta:</b> +${{p.pagerank_delta.toFixed(3)}}
              `;
            }} else {{
              ovTitle.textContent = `HOST TELEMETRY: ${{n.type}}`;
              ovTitle.style.color = color;
              ovDetails.innerHTML = `<b>IP:</b> ${{n.id}}<br><b>Status:</b> Baseline Nominal`;
            }}
          }});

          // Label
          if (n.is_pivot || n.type === 'SERVER') {{
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', n.cx);
            text.setAttribute('y', n.cy - 10);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('class', n.is_pivot ? 'node-label label-threat' : 'node-label');
            text.textContent = n.is_pivot ? `[PIVOT] ${{n.id}}` : n.id;
            g.appendChild(text);
          }}

          g.appendChild(circle);
          nodesGroup.appendChild(g);
        }});

        // Anime.js v4 Exact API Call for Topology Morphing & Staggered Infection
        if (window.anime) {{
          const {{ animate, stagger }} = window.anime;

          // Animate threat edges with stagger indicating chronological pivot order
          animate('.edge-threat', {{
            strokeDashoffset: [400, 0],
            duration: 350,
            delay: stagger(45, {{ from: 'first' }}),
            ease: 'outQuad'
          }});

          // Morph/Pulse pivot nodes
          animate('.node-pivot', {{
            r: [6, 11, 8],
            duration: 300,
            ease: 'outQuad'
          }});
        }}
      </script>
    </body>
    </html>
    """
    components.html(html_content, height=height, scrolling=False)
