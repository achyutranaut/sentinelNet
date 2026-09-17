"""Tier 4: Adversarial Evasion Lab Component (Anime.js v4 createTimeline Sync).

Renders the evasion resilience curve and links perturbation budget controls
using Anime.js v4 createTimeline() to keep recall drop indicators, budget cursor,
and defense metrics strictly synchronized without bouncing or decorative delays.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
import streamlit.components.v1 as components


def render_evasion_lab(
    curve_points: List[Dict[str, float]],
    current_epsilon: float = 0.15,
    height: int = 340
) -> None:
    # Normalize curve_points whether dataclasses or dicts
    clean_points = []
    for p in curve_points:
        if hasattr(p, "epsilon"):
            clean_points.append({
                "epsilon": float(p.epsilon),
                "supervised_recall": float(p.supervised_recall),
                "autoencoder_recall": float(p.autoencoder_recall),
                "combined_recall": float(p.combined_recall)
            })
        elif isinstance(p, dict):
            clean_points.append({
                "epsilon": float(p.get("epsilon", p.get("Epsilon", 0.0))),
                "supervised_recall": float(p.get("supervised_recall", p.get("LightGBM Signature Recall", 0.0))),
                "autoencoder_recall": float(p.get("autoencoder_recall", p.get("Autoencoder Anomaly Recall", 0.0))),
                "combined_recall": float(p.get("combined_recall", p.get("Multi-Tier Combined Recall", 0.0)))
            })
    points_json = json.dumps(clean_points)

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
        .lab-panel {{
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
        .lab-content {{
          display: flex;
          flex: 1;
          padding: 8px;
          gap: 12px;
        }}
        .chart-area {{
          flex: 2;
          position: relative;
        }}
        svg.chart-svg {{
          width: 100%;
          height: 100%;
        }}
        .telemetry-col {{
          flex: 1;
          background-color: #161b22;
          border: 1px solid #21262d;
          border-radius: 2px;
          padding: 10px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
        }}
        .telemetry-row {{
          margin-bottom: 6px;
        }}
        .t-label {{
          font-size: 9px;
          color: #8b949e;
          text-transform: uppercase;
        }}
        .t-val {{
          font-size: 13px;
          font-weight: 600;
          color: #e6edf3;
        }}
        .t-val-crit {{
          color: #f85149;
        }}
        .t-val-secure {{
          color: #3fb950;
        }}
        .curve-line {{
          fill: none;
          stroke-width: 1.5;
        }}
        .line-combined {{ stroke: #3fb950; }}
        .line-supervised {{ stroke: #f85149; stroke-dasharray: 4; }}
        .line-autoencoder {{ stroke: #58a6ff; stroke-dasharray: 2; }}
        .grid-line {{
          stroke: #21262d;
          stroke-width: 1;
        }}
        .axis-label {{
          font-size: 8.5px;
          fill: #8b949e;
          font-family: 'IBM Plex Mono', monospace;
        }}
        #budget-cursor-line {{
          stroke: #d29922;
          stroke-width: 1.5;
          stroke-dasharray: 3 3;
        }}
      </style>
    </head>
    <body>
      <div class="lab-panel">
        <div class="panel-header">
          <span>ADVERSARIAL EVASION & STRESS-TEST LAB (TIER 4)</span>
          <span id="active-eps-badge">ACTIVE ε: {current_epsilon:.2f}</span>
        </div>
        <div class="lab-content">
          <div class="chart-area">
            <svg class="chart-svg" id="evasion-svg" viewBox="0 0 380 230">
              <!-- Grid & Axes -->
              <line x1="40" y1="20" x2="40" y2="190" class="grid-line" />
              <line x1="40" y1="190" x2="360" y2="190" class="grid-line" />
              
              <!-- Y Axis Ticks -->
              <text x="32" y="24" class="axis-label" text-anchor="end">1.0</text>
              <text x="32" y="105" class="axis-label" text-anchor="end">0.5</text>
              <text x="32" y="193" class="axis-label" text-anchor="end">0.0</text>

              <!-- X Axis Ticks -->
              <text x="40" y="206" class="axis-label" text-anchor="middle">0.0</text>
              <text x="120" y="206" class="axis-label" text-anchor="middle">0.1</text>
              <text x="200" y="206" class="axis-label" text-anchor="middle">0.2</text>
              <text x="280" y="206" class="axis-label" text-anchor="middle">0.3</text>
              <text x="360" y="206" class="axis-label" text-anchor="middle">0.4</text>
              <text x="200" y="222" class="axis-label" text-anchor="middle">PERTURBATION BUDGET (ε)</text>

              <!-- Curves -->
              <path id="path-supervised" class="curve-line line-supervised" />
              <path id="path-autoencoder" class="curve-line line-autoencoder" />
              <path id="path-combined" class="curve-line line-combined" />

              <!-- Synchronized Timeline Cursor & Indicator Dots -->
              <line id="budget-cursor-line" x1="40" y1="20" x2="40" y2="190" />
              <circle id="dot-combined" r="4" fill="#3fb950" cx="40" cy="190" />
              <circle id="dot-supervised" r="3.5" fill="#f85149" cx="40" cy="190" />
            </svg>
          </div>
          <div class="telemetry-col">
            <div class="telemetry-row">
              <div class="t-label">Perturbation Budget</div>
              <div class="t-val" id="disp-eps">{current_epsilon:.2f}</div>
            </div>
            <div class="telemetry-row">
              <div class="t-label">Signature Recall (Tier 1)</div>
              <div class="t-val t-val-crit" id="disp-rec-t1">--%</div>
            </div>
            <div class="telemetry-row">
              <div class="t-label">Zero-Day Anomaly (Tier 2)</div>
              <div class="t-val" id="disp-rec-t2" style="color: #58a6ff;">--%</div>
            </div>
            <div class="telemetry-row">
              <div class="t-label">Multi-Tier Defense</div>
              <div class="t-val t-val-secure" id="disp-rec-comb">--%</div>
            </div>
          </div>
        </div>
      </div>

      <script>
        const pts = {points_json};
        const currentEps = {current_epsilon};

        // Coordinates mapping
        // x: 0.0 -> 40, 0.4 -> 360  (scale = 320 / 0.4 = 800)
        // y: 1.0 -> 20, 0.0 -> 190  (scale = 170)
        function mapX(eps) {{ return 40 + (eps / 0.4) * 320; }}
        function mapY(val) {{ return 190 - (val * 170); }}

        let dSup = "";
        let dAe = "";
        let dComb = "";

        pts.forEach((pt, i) => {{
          const px = mapX(pt.epsilon);
          const pySup = mapY(pt.supervised_recall);
          const pyAe = mapY(pt.autoencoder_recall);
          const pyComb = mapY(pt.combined_recall);

          dSup += (i === 0 ? `M ${{px}} ${{pySup}}` : ` L ${{px}} ${{pySup}}`);
          dAe += (i === 0 ? `M ${{px}} ${{pyAe}}` : ` L ${{px}} ${{pyAe}}`);
          dComb += (i === 0 ? `M ${{px}} ${{pyComb}}` : ` L ${{px}} ${{pyComb}}`);
        }});

        document.getElementById('path-supervised').setAttribute('d', dSup);
        document.getElementById('path-autoencoder').setAttribute('d', dAe);
        document.getElementById('path-combined').setAttribute('d', dComb);

        // Find closest point to currentEps
        let activePt = pts[0];
        let minDiff = 999;
        pts.forEach(p => {{
          const diff = Math.abs(p.epsilon - currentEps);
          if (diff < minDiff) {{
            minDiff = diff;
            activePt = p;
          }}
        }});

        const targetCursorX = mapX(activePt.epsilon);
        const targetCombY = mapY(activePt.combined_recall);
        const targetSupY = mapY(activePt.supervised_recall);

        // Update telemetry numbers
        document.getElementById('disp-eps').textContent = activePt.epsilon.toFixed(2);
        document.getElementById('disp-rec-t1').textContent = `${{(activePt.supervised_recall * 100).toFixed(1)}}%`;
        document.getElementById('disp-rec-t2').textContent = `${{(activePt.autoencoder_recall * 100).toFixed(1)}}%`;
        document.getElementById('disp-rec-comb').textContent = `${{(activePt.combined_recall * 100).toFixed(1)}}%`;

        // Anime.js v4 Exact API Call using createTimeline()
        if (window.anime && window.anime.createTimeline) {{
          const {{ createTimeline }} = window.anime;
          const tl = createTimeline({{
            defaults: {{
              duration: 180,
              ease: 'outQuad'
            }}
          }});

          tl.add('#budget-cursor-line', {{
            x1: targetCursorX,
            x2: targetCursorX
          }})
          .add('#dot-combined', {{
            cx: targetCursorX,
            cy: targetCombY
          }}, 0)
          .add('#dot-supervised', {{
            cx: targetCursorX,
            cy: targetSupY
          }}, 0);
        }} else {{
          // Immediate fallback if script loads synchronously
          const cLine = document.getElementById('budget-cursor-line');
          cLine.setAttribute('x1', targetCursorX);
          cLine.setAttribute('x2', targetCursorX);
          const dComb = document.getElementById('dot-combined');
          dComb.setAttribute('cx', targetCursorX);
          dComb.setAttribute('cy', targetCombY);
        }}
      </script>
    </body>
    </html>
    """
    components.html(html_content, height=height, scrolling=False)
