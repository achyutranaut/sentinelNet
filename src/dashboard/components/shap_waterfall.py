"""Tier 5: TreeSHAP Feature Attribution Waterfall Inspector (Anime.js v4 Staggered Reveal).

Provides SOC Tier 1 analysts with transparent flow-level explainability:
- Horizontal diverging attribution bars for threat drivers vs mitigators
- Plain-English analyst narrative brief
- Strict SOC terminal aesthetic in IBM Plex Mono and Space Grotesk
- Sharp, non-bouncy Anime.js v4 animations on alert selection
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import streamlit.components.v1 as components


def render_shap_waterfall(
    summary: Any,
    height: int = 340
) -> None:
    """Renders high-density TreeSHAP attribution inspector with Anime.js v4 reveals."""
    # Handle dataclass or dict
    if hasattr(summary, "predicted_probability"):
        pred_prob = float(summary.predicted_probability)
        base_val = float(summary.base_value)
        analyst_text = str(summary.analyst_summary)
        raw_drivers = summary.top_drivers
    elif isinstance(summary, dict):
        pred_prob = float(summary.get("predicted_probability", 0.0))
        base_val = float(summary.get("base_value", 0.0))
        analyst_text = str(summary.get("analyst_summary", "No analyst brief available."))
        raw_drivers = summary.get("top_drivers", [])
    else:
        pred_prob = 0.0
        base_val = 0.0
        analyst_text = "No flow selected for triage."
        raw_drivers = []

    drivers_data: List[Dict[str, Any]] = []
    for d in raw_drivers:
        if hasattr(d, "feature_name"):
            drivers_data.append({
                "name": str(d.feature_name),
                "val": float(d.feature_value),
                "shap": float(d.shap_value),
                "direction": str(d.impact_direction)
            })
        elif isinstance(d, dict):
            drivers_data.append({
                "name": str(d.get("feature_name", "unknown")),
                "val": float(d.get("feature_value", 0.0)),
                "shap": float(d.get("shap_value", 0.0)),
                "direction": str(d.get("impact_direction", "UNKNOWN"))
            })

    drivers_json = json.dumps(drivers_data)

    # Read vendored anime.js v4
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

    prob_pct = f"{pred_prob * 100:.1f}%"
    severity_class = "badge-crit" if pred_prob >= 0.5 else ("badge-warn" if pred_prob >= 0.15 else "badge-nominal")
    severity_label = "CRITICAL RISK" if pred_prob >= 0.5 else ("ELEVATED" if pred_prob >= 0.15 else "BENIGN")

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
        .shap-panel {{
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
        .header-left {{
          display: flex;
          align-items: center;
          gap: 6px;
        }}
        .dot-indicator {{
          width: 6px;
          height: 6px;
          background-color: #58a6ff;
          border-radius: 1px;
        }}
        .badge {{
          display: inline-block;
          padding: 1px 6px;
          font-size: 9px;
          font-weight: 700;
          letter-spacing: 0.05em;
          border-radius: 2px;
        }}
        .badge-crit {{ background-color: #f85149; color: #0d1117; }}
        .badge-warn {{ background-color: #d29922; color: #0d1117; }}
        .badge-nominal {{ background-color: #238636; color: #ffffff; }}

        .narrative-banner {{
          background-color: #161b22;
          border-bottom: 1px solid #21262d;
          border-left: 3px solid #58a6ff;
          padding: 6px 10px;
          font-size: 9.5px;
          color: #c9d1d9;
          line-height: 1.4;
        }}
        .narrative-banner b {{
          color: #58a6ff;
          font-family: 'Space Grotesk', sans-serif;
          letter-spacing: 0.05em;
        }}

        .waterfall-content {{
          flex: 1;
          overflow-y: auto;
          padding: 6px 8px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }}
        .waterfall-content::-webkit-scrollbar {{
          width: 4px;
        }}
        .waterfall-content::-webkit-scrollbar-track {{ background: #0d1117; }}
        .waterfall-content::-webkit-scrollbar-thumb {{ background: #21262d; }}

        .shap-row {{
          display: grid;
          grid-template-columns: 130px 65px 1fr 60px;
          align-items: center;
          gap: 8px;
          padding: 3px 4px;
          background-color: #161b22;
          border: 1px solid #21262d;
          border-radius: 2px;
          font-size: 9.5px;
        }}
        .feat-name {{
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          color: #e6edf3;
          font-weight: 500;
        }}
        .feat-val {{
          color: #8b949e;
          text-align: right;
          font-size: 9px;
        }}
        .bar-container {{
          position: relative;
          height: 14px;
          background-color: #090b0e;
          border-radius: 1px;
          display: flex;
          align-items: center;
          overflow: hidden;
        }}
        .center-line {{
          position: absolute;
          left: 50%;
          top: 0;
          bottom: 0;
          width: 1px;
          background-color: #30363d;
          z-index: 2;
        }}
        .shap-bar-fill {{
          height: 100%;
          position: absolute;
          transition: width 0.05s ease;
        }}
        .bar-driver {{
          left: 50%;
          background-color: #f85149;
        }}
        .bar-mitigator {{
          right: 50%;
          background-color: #3fb950;
        }}
        .shap-delta {{
          text-align: right;
          font-weight: 600;
          font-size: 9.5px;
        }}
        .delta-driver {{ color: #f85149; }}
        .delta-mitigator {{ color: #3fb950; }}

        .footer-metrics {{
          background-color: #161b22;
          border-top: 1px solid #21262d;
          padding: 4px 10px;
          display: flex;
          justify-content: space-between;
          font-size: 9px;
          color: #8b949e;
        }}
        .footer-metrics span b {{
          color: #e6edf3;
        }}
      </style>
    </head>
    <body>
      <div class="shap-panel">
        <div class="panel-header">
          <div class="header-left">
            <div class="dot-indicator"></div>
            <span>TREESHAP INCIDENT ATTRIBUTION INSPECTOR (TIER 5)</span>
          </div>
          <div>
            <span class="badge {severity_class}">{severity_label}: {prob_pct}</span>
          </div>
        </div>

        <div class="narrative-banner">
          <b>SOC ANALYST BRIEF:</b> {analyst_text}
        </div>

        <div class="waterfall-content" id="waterfall-list">
          <!-- Dynamically populated rows -->
        </div>

        <div class="footer-metrics">
          <span>BASE RATE (LOG-ODDS): <b>{base_val:.3f}</b></span>
          <span>CALIBRATED PROB: <b>{prob_pct}</b></span>
          <span>ATTRIBUTIONS: <b>TREESHAP FAST</b></span>
        </div>
      </div>

      <script>
        const drivers = {drivers_json};
        const container = document.getElementById('waterfall-list');

        if (drivers.length === 0) {{
          container.innerHTML = '<div style="color: #8b949e; padding: 12px; text-align: center;">No active flow selected. Inject or click an incident to inspect feature attributions.</div>';
        }} else {{
          // Determine maximum absolute SHAP value for proportional bar scaling
          let maxAbs = 0.001;
          drivers.forEach(d => {{
            const a = Math.abs(d.shap);
            if (a > maxAbs) maxAbs = a;
          }});

          drivers.forEach((d, idx) => {{
            const row = document.createElement('div');
            row.className = 'shap-row';
            row.id = `shap-row-${{idx}}`;

            const isThreat = d.shap >= 0;
            const pctWidth = Math.min((Math.abs(d.shap) / maxAbs) * 50.0, 50.0);
            const deltaSign = isThreat ? `+${{d.shap.toFixed(3)}}` : `${{d.shap.toFixed(3)}}`;
            const deltaClass = isThreat ? 'delta-driver' : 'delta-mitigator';
            const barClass = isThreat ? 'shap-bar-fill bar-driver' : 'shap-bar-fill bar-mitigator';

            row.innerHTML = `
              <div class="feat-name" title="${{d.name}}">${{d.name}}</div>
              <div class="feat-val">${{d.val.toFixed(2)}}</div>
              <div class="bar-container">
                <div class="center-line"></div>
                <div class="${{barClass}}" data-width="${{pctWidth}}" style="width: ${{pctWidth}}%;"></div>
              </div>
              <div class="shap-delta ${{deltaClass}}">${{deltaSign}}</div>
            `;
            container.appendChild(row);
          }});

          // Anime.js v4 Exact API Integration
          if (window.anime) {{
            const {{ animate, stagger }} = window.anime;

            // Micro-stagger entrance for rows
            animate('.shap-row', {{
              opacity: [0, 1],
              translateX: [-8, 0],
              duration: 120,
              delay: stagger(20),
              ease: 'outQuad'
            }});

            // Expand horizontal attribution bars
            document.querySelectorAll('.shap-bar-fill').forEach((bar) => {{
              const targetW = parseFloat(bar.getAttribute('data-width') || '0');
              animate(bar, {{
                width: ['0%', `${{targetW}}%`],
                duration: 250,
                delay: stagger(25),
                ease: 'outQuad'
              }});
            }});
          }}
        }}
      </script>
    </body>
    </html>
    """
    components.html(html_content, height=height, scrolling=False)
