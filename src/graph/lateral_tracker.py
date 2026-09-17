"""Tier 3: Temporal Network Interaction Graph for Lateral Movement Detection.

Tracks host-to-host interaction topology over sliding time windows using NetworkX.
Detects stealthy low-and-slow internal pivoting (SMB/SSH/RDP) that evades per-flow classifiers,
using degree bursts (z-score), Jaccard edge novelty, and PageRank delta shifts.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx
import numpy as np
import pandas as pd


@dataclass
class HostThreatScore:
    host_ip: str
    out_degree: int
    degree_zscore: float
    jaccard_novelty: float
    pagerank: float
    pagerank_delta: float
    is_suspicious_pivot: bool
    reasons: List[str]


@dataclass
class GraphAnomalyReport:
    window_start: float
    window_end: float
    num_nodes: int
    num_edges: int
    flagged_pivots: List[HostThreatScore]


class TemporalLateralTracker:
    """Dynamic temporal graph tracker for enterprise host interaction topologies."""

    def __init__(
        self,
        window_size_seconds: float = 300.0,
        degree_zscore_threshold: float = 2.5,
        jaccard_novelty_threshold: float = 0.80,
        pagerank_delta_threshold: float = 0.10,
        baseline_min_history_flows: int = 50
    ):
        self.window_size = window_size_seconds
        self.zscore_thresh = degree_zscore_threshold
        self.novelty_thresh = jaccard_novelty_threshold
        self.pagerank_thresh = pagerank_delta_threshold
        self.min_history = baseline_min_history_flows

        # Historical baseline edge set {(src_ip, dst_ip)}
        self.baseline_edges: Set[Tuple[str, str]] = set()
        self.baseline_degrees: Dict[str, List[int]] = defaultdict(list)
        self.baseline_pagerank: Dict[str, float] = {}
        self.baseline_graph = nx.DiGraph()

    def fit_baseline(self, baseline_df: pd.DataFrame) -> "TemporalLateralTracker":
        """Builds normal interaction topology baseline from historical enterprise flows."""
        self.baseline_edges.clear()
        self.baseline_degrees.clear()
        self.baseline_graph.clear()

        # Build initial baseline graph
        for _, row in baseline_df.iterrows():
            src = str(row["src_ip"])
            dst = str(row["dst_ip"])
            self.baseline_edges.add((src, dst))
            self.baseline_graph.add_edge(src, dst)

        # Baseline out-degrees and PageRank
        for node in self.baseline_graph.nodes():
            self.baseline_degrees[node].append(self.baseline_graph.out_degree(node))

        if len(self.baseline_graph) > 0:
            self.baseline_pagerank = nx.pagerank(self.baseline_graph, alpha=0.85)

        return self

    def analyze_window(self, window_df: pd.DataFrame) -> GraphAnomalyReport:
        """Analyzes a temporal batch of flows and flags lateral movement pivot hosts."""
        g_window = nx.DiGraph()
        ts_min = float(window_df["timestamp"].min()) if not window_df.empty else 0.0
        ts_max = float(window_df["timestamp"].max()) if not window_df.empty else 0.0

        for _, row in window_df.iterrows():
            src = str(row["src_ip"])
            dst = str(row["dst_ip"])
            weight = g_window[src][dst]["weight"] + 1 if g_window.has_edge(src, dst) else 1
            g_window.add_edge(src, dst, weight=weight)

        if len(g_window) == 0:
            return GraphAnomalyReport(ts_min, ts_max, 0, 0, [])

        window_pagerank = nx.pagerank(g_window, alpha=0.85)
        out_degrees = dict(g_window.out_degree())
        deg_values = list(out_degrees.values())
        mean_deg = float(np.mean(deg_values)) if deg_values else 0.0
        std_deg = float(np.std(deg_values)) if deg_values and np.std(deg_values) > 1e-4 else 1.0

        flagged: List[HostThreatScore] = []

        for host in g_window.nodes():
            out_deg = out_degrees[host]
            zscore = (out_deg - mean_deg) / std_deg

            # Edge novelty (Jaccard dissimilarity to known baseline)
            current_neighbors = set(g_window.successors(host))
            if not current_neighbors:
                continue

            # Calculate how many of current destination hosts are completely novel
            novel_neighbors = 0
            for dst in current_neighbors:
                if (host, dst) not in self.baseline_edges:
                    novel_neighbors += 1

            jaccard_novelty = novel_neighbors / max(1, len(current_neighbors))

            # PageRank shift
            base_pr = self.baseline_pagerank.get(host, 0.0)
            curr_pr = window_pagerank.get(host, 0.0)
            pr_delta = curr_pr - base_pr

            # Anomaly criteria
            is_suspicious = False
            reasons = []

            # 1. Degree burst: connecting to unusual number of distinct endpoints
            if zscore >= self.zscore_thresh and out_deg >= 4:
                is_suspicious = True
                reasons.append(f"High Out-Degree Z-Score ({zscore:.2f} >= {self.zscore_thresh})")

            # 2. Edge novelty: sudden contacts to unvisited internal endpoints
            if jaccard_novelty >= self.novelty_thresh and out_deg >= 3:
                is_suspicious = True
                reasons.append(f"High Edge Novelty ({jaccard_novelty:.1%} unseen target hosts)")

            # 3. Structural centrality shift
            if pr_delta >= self.pagerank_thresh and out_deg >= 4:
                is_suspicious = True
                reasons.append(f"PageRank Delta Spike (+{pr_delta:.3f})")

            if is_suspicious:
                flagged.append(HostThreatScore(
                    host_ip=host,
                    out_degree=out_deg,
                    degree_zscore=float(zscore),
                    jaccard_novelty=float(jaccard_novelty),
                    pagerank=float(curr_pr),
                    pagerank_delta=float(pr_delta),
                    is_suspicious_pivot=True,
                    reasons=reasons
                ))

        return GraphAnomalyReport(
            window_start=ts_min,
            window_end=ts_max,
            num_nodes=g_window.number_of_nodes(),
            num_edges=g_window.number_of_edges(),
            flagged_pivots=flagged
        )
