"""High-Density Live Alert Stream Component (Anime.js v4 Entrance Transitions).

Provides a dense SOC terminal log view with IBM Plex Mono tabular alignment,
color-coded severity signaling, and sharp, non-bouncy Anime.js v4 entrance animations.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
import streamlit.components.v1 as components


def render_alert_stream(flows: List[Dict[str, Any]], height: int = 340) -> None:
    """Renders high-density live stream table with Anime.js v4 entrance animation."""
    flows_json = json.dumps(flows)
    
    # Read local vendored anime.js v4 if available
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
          line-height: 1.4;
          overflow: hidden;
          padding: 4px;
        }}
        .terminal-panel {{
          background-color: #0d1117;
          border: 1px solid #21262d;
          border-radius: 2px;
          display: flex;
          flex-direction: column;
          height: {height - 8}px;
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
        .panel-header .title-group {{
          display: flex;
          align-items: center;
          gap: 6px;
        }}
        .status-dot {{
          width: 6px;
          height: 6px;
          background-color: #3fb950;
          border-radius: 1px;
        }}
        .stream-table-container {{
          overflow-y: auto;
          flex: 1;
        }}
        table.stream-table {{
          width: 100%;
          border-collapse: collapse;
          text-align: left;
        }}
        table.stream-table th {{
          position: sticky;
          top: 0;
          background-color: #161b22;
          color: #8b949e;
          font-weight: 500;
          font-size: 9.5px;
          letter-spacing: 0.05em;
          padding: 5px 8px;
          border-bottom: 1px solid #21262d;
          text-transform: uppercase;
          z-index: 2;
        }}
        table.stream-table td {{
          padding: 4px 8px;
          border-bottom: 1px solid #161b22;
          white-space: nowrap;
        }}
        tr.flow-row:hover {{
          background-color: #161b22;
        }}
        .badge {{
          display: inline-block;
          padding: 1px 5px;
          font-size: 9px;
          font-weight: 600;
          letter-spacing: 0.04em;
          border-radius: 2px;
          text-align: center;
        }}
        .badge-critical {{
          background-color: #f85149;
          color: #0d1117;
          font-weight: 700;
        }}
        .badge-warning {{
          background-color: #d29922;
          color: #0d1117;
          font-weight: 700;
        }}
        .badge-neutral {{
          background-color: #21262d;
          color: #8b949e;
        }}
        .val-threat {{
          color: #f85149;
          font-weight: 600;
        }}
        .val-warn {{
          color: #d29922;
          font-weight: 600;
        }}
        .val-dim {{
          color: #8b949e;
        }}
        /* Custom thin scrollbar */
        ::-webkit-scrollbar {{
          width: 4px;
          height: 4px;
        }}
        ::-webkit-scrollbar-track {{
          background: #0d1117;
        }}
        ::-webkit-scrollbar-thumb {{
          background: #21262d;
        }}
      </style>
    </head>
    <body>
      <div class="terminal-panel">
        <div class="panel-header">
          <div class="title-group">
            <div class="status-dot"></div>
            <span>LIVE FLOW INGESTION & TIER SCORING STREAM</span>
          </div>
          <span id="flow-count-label">SYNCED: 0 FLOWS</span>
        </div>
        <div class="stream-table-container">
          <table class="stream-table">
            <thead>
              <tr>
                <th>TIMESTAMP</th>
                <th>SRC ADDR</th>
                <th>DST ADDR:PORT</th>
                <th>ATTACK PROFILE</th>
                <th>SIG PROB</th>
                <th>AE LOSS</th>
                <th>DETECTION TIER</th>
                <th>SEVERITY</th>
              </tr>
            </thead>
            <tbody id="stream-tbody">
              <!-- Dynamically populated -->
            </tbody>
          </table>
        </div>
      </div>

      <script>
        const rawFlows = {flows_json};
        const tbody = document.getElementById('stream-tbody');
        const countLabel = document.getElementById('flow-count-label');
        countLabel.textContent = `SYNCED: ${{rawFlows.length}} FLOWS`;

        // Render rows
        rawFlows.forEach((flow, idx) => {{
          const tr = document.createElement('tr');
          tr.className = 'flow-row flow-row-animated';
          tr.id = `flow-row-${{idx}}`;

          const isAttack = flow.is_attack === 1 || flow.is_attack === true;
          const supProb = flow.supervised_prob !== undefined ? flow.supervised_prob : (flow.supervised_probability || 0.0);
          const reconLoss = flow.reconstruction_loss || 0.0;
          const reconThresh = flow.reconstruction_threshold || 0.8;
          const isTier1 = supProb >= 0.15;
          const isTier2 = reconLoss >= reconThresh;

          let severityBadge = '<span class="badge badge-neutral">CLEAN</span>';
          let tierText = '<span class="val-dim">NONE</span>';

          if (isTier1 && isTier2) {{
            severityBadge = '<span class="badge badge-critical">CRITICAL</span>';
            tierText = '<span class="val-threat">TIER 1 + 2</span>';
          }} else if (isTier1) {{
            severityBadge = '<span class="badge badge-critical">CRITICAL</span>';
            tierText = '<span class="val-threat">TIER 1 (SIG)</span>';
          }} else if (isTier2) {{
            severityBadge = '<span class="badge badge-warning">ANOMALY</span>';
            tierText = '<span class="val-warn">TIER 2 (AE)</span>';
          }}

          const probClass = supProb >= 0.5 ? 'val-threat' : (supProb >= 0.15 ? 'val-warn' : 'val-dim');
          const lossClass = reconLoss >= reconThresh ? 'val-warn' : 'val-dim';
          const atkName = flow.attack_type || 'BENIGN';

          tr.innerHTML = `
            <td class="val-dim">${{parseFloat(flow.timestamp || 0).toFixed(2)}}</td>
            <td>${{flow.src_ip || '0.0.0.0'}}</td>
            <td>${{flow.dst_ip || '0.0.0.0'}}:<span class="val-dim">${{flow.dst_port || 80}}</span></td>
            <td>${{atkName}}</td>
            <td class="${{probClass}}">${{parseFloat(supProb).toFixed(3)}}</td>
            <td class="${{lossClass}}">${{parseFloat(reconLoss).toFixed(4)}}</td>
            <td>${{tierText}}</td>
            <td>${{severityBadge}}</td>
          `;
          tbody.appendChild(tr);
        }});

        // Anime.js v4 Exact API Call for Entrance Transition
        if (window.anime && window.anime.animate) {{
          const {{ animate }} = window.anime;
          animate('.flow-row-animated', {{
            opacity: [0, 1],
            translateX: [-8, 0],
            duration: 90,
            ease: 'outQuad',
            delay: (el, i) => i * 15 // Tight micro-stagger for temporal order
          }});
        }}
      </script>
    </body>
    </html>
    """
    components.html(html_content, height=height, scrolling=False)
