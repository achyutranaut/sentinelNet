"""Dataset generator and loader for SentinelNet (MLOps Ingestion Layer).

Generates high-fidelity network flow traces mimicking enterprise enterprise environments,
including baseline enterprise traffic, volumetric DDoS attacks, brute-force attempts,
novel zero-day C2 exfiltration, and stealth lateral movement.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class NetworkSubnet:
    dmz_servers: List[str]
    internal_workstations: List[str]
    internal_servers: List[str]
    external_ips: List[str]


def create_enterprise_network_topology() -> NetworkSubnet:
    """Creates realistic IP addresses representing enterprise network segments."""
    dmz = [f"192.168.1.{i}" for i in range(10, 15)]  # Web, Mail, DNS, VPN
    workstations = [f"192.168.10.{i}" for i in range(100, 140)]  # User endpoints
    servers = [f"10.0.1.{i}" for i in range(20, 28)]  # DB, AD Domain Controller, File share
    externals = [f"198.51.100.{i}" for i in range(1, 60)]  # External internet clients/adversaries
    return NetworkSubnet(
        dmz_servers=dmz,
        internal_workstations=workstations,
        internal_servers=servers,
        external_ips=externals
    )


class NetworkFlowGenerator:
    """Generates synthetic high-fidelity NetFlow records following empirical distributions."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.topology = create_enterprise_network_topology()

    def generate_baseline_flows(self, n_samples: int) -> pd.DataFrame:
        """Generates benign enterprise traffic (web browsing, DNS lookups, internal file access)."""
        flows = []
        base_time = 1715000000.0

        for i in range(n_samples):
            traffic_type = self.rng.choice(["web", "dns", "internal_rpc", "cloud_sync"], p=[0.55, 0.20, 0.15, 0.10])
            ts = base_time + float(i * 0.4 + self.rng.uniform(0.01, 0.2))

            if traffic_type == "web":
                src_ip = self.rng.choice(self.topology.internal_workstations)
                dst_ip = self.rng.choice(self.topology.external_ips)
                dst_port = int(self.rng.choice([80, 443]))
                duration = float(np.clip(self.rng.exponential(250.0), 10.0, 5000.0))
                fwd_pkts = int(self.rng.integers(5, 45))
                bwd_pkts = int(self.rng.integers(8, 70))
                fwd_bytes = fwd_pkts * float(self.rng.normal(320, 60))
                bwd_bytes = bwd_pkts * float(self.rng.normal(850, 200))
                fwd_syn = 1
                fwd_ack = fwd_pkts - 1
                bwd_syn = 1
                bwd_ack = bwd_pkts
                fwd_psh = int(self.rng.integers(1, 4))
                bwd_psh = int(self.rng.integers(2, 8))
                fwd_rst = 0
                bwd_rst = 0
            elif traffic_type == "dns":
                src_ip = self.rng.choice(self.topology.internal_workstations)
                dst_ip = self.topology.dmz_servers[2]  # Internal DNS resolver
                dst_port = 53
                duration = float(np.clip(self.rng.normal(15.0, 5.0), 2.0, 40.0))
                fwd_pkts = 1
                bwd_pkts = 1
                fwd_bytes = float(self.rng.uniform(45.0, 95.0))
                bwd_bytes = float(self.rng.uniform(110.0, 350.0))
                fwd_syn = 0
                fwd_ack = 0
                bwd_syn = 0
                bwd_ack = 0
                fwd_psh = 0
                bwd_psh = 0
                fwd_rst = 0
                bwd_rst = 0
            elif traffic_type == "internal_rpc":
                src_ip = self.rng.choice(self.topology.internal_workstations)
                dst_ip = self.rng.choice(self.topology.internal_servers)
                dst_port = int(self.rng.choice([445, 139, 389]))
                duration = float(np.clip(self.rng.exponential(120.0), 5.0, 1500.0))
                fwd_pkts = int(self.rng.integers(4, 25))
                bwd_pkts = int(self.rng.integers(4, 25))
                fwd_bytes = fwd_pkts * float(self.rng.normal(210, 40))
                bwd_bytes = bwd_pkts * float(self.rng.normal(310, 70))
                fwd_syn = 1
                fwd_ack = fwd_pkts
                bwd_syn = 1
                bwd_ack = bwd_pkts
                fwd_psh = int(self.rng.integers(1, 3))
                bwd_psh = int(self.rng.integers(1, 3))
                fwd_rst = 0
                bwd_rst = 0
            else:  # cloud_sync
                src_ip = self.rng.choice(self.topology.internal_workstations)
                dst_ip = self.rng.choice(self.topology.external_ips)
                dst_port = 443
                duration = float(np.clip(self.rng.exponential(1500.0), 200.0, 12000.0))
                fwd_pkts = int(self.rng.integers(20, 150))
                bwd_pkts = int(self.rng.integers(30, 200))
                fwd_bytes = fwd_pkts * float(self.rng.normal(650, 150))
                bwd_bytes = bwd_pkts * float(self.rng.normal(1200, 250))
                fwd_syn = 1
                fwd_ack = fwd_pkts
                bwd_syn = 1
                bwd_ack = bwd_pkts
                fwd_psh = int(self.rng.integers(5, 20))
                bwd_psh = int(self.rng.integers(8, 30))
                fwd_rst = 0
                bwd_rst = 0

            flow = self._assemble_flow(
                src_ip=src_ip,
                dst_ip=dst_ip,
                dst_port=dst_port,
                timestamp=ts,
                duration=duration,
                fwd_pkts=fwd_pkts,
                bwd_pkts=bwd_pkts,
                fwd_bytes=fwd_bytes,
                bwd_bytes=bwd_bytes,
                fwd_syn=fwd_syn,
                fwd_ack=fwd_ack,
                bwd_syn=bwd_syn,
                bwd_ack=bwd_ack,
                fwd_psh=fwd_psh,
                bwd_psh=bwd_psh,
                fwd_rst=fwd_rst,
                bwd_rst=bwd_rst,
                attack_type="BENIGN",
                label=0
            )
            flows.append(flow)

        return pd.DataFrame(flows)

    def generate_known_attacks(self, n_samples: int) -> pd.DataFrame:
        """Generates signature attacks: DDoS SYN Flood, Port Scans, and Brute Force SSH/FTP."""
        flows = []
        base_time = 1715004000.0
        n_ddos = int(n_samples * 0.45)
        n_scan = int(n_samples * 0.35)
        n_brute = n_samples - n_ddos - n_scan

        # 1. DDoS SYN Flood
        attacker_pool = self.rng.choice(self.topology.external_ips, size=8, replace=False)
        target_server = self.topology.dmz_servers[0]
        for i in range(n_ddos):
            ts = base_time + float(i * 0.005)
            src_ip = self.rng.choice(attacker_pool)
            duration = float(self.rng.uniform(1.0, 25.0))
            fwd_pkts = int(self.rng.integers(60, 300))
            bwd_pkts = int(self.rng.integers(0, 3))
            fwd_bytes = fwd_pkts * float(self.rng.uniform(54.0, 72.0))
            bwd_bytes = bwd_pkts * float(self.rng.uniform(54.0, 72.0))

            flows.append(self._assemble_flow(
                src_ip=src_ip, dst_ip=target_server, dst_port=80, timestamp=ts,
                duration=duration, fwd_pkts=fwd_pkts, bwd_pkts=bwd_pkts,
                fwd_bytes=fwd_bytes, bwd_bytes=bwd_bytes,
                fwd_syn=fwd_pkts, fwd_ack=0, bwd_syn=0, bwd_ack=bwd_pkts,
                fwd_psh=0, bwd_psh=0, fwd_rst=0, bwd_rst=bwd_pkts,
                attack_type="DDOS_SYN_FLOOD", label=1
            ))

        # 2. Port Scan
        scan_attacker = self.rng.choice(self.topology.external_ips)
        for i in range(n_scan):
            ts = base_time + 500.0 + float(i * 0.04)
            scanned_port = int(self.rng.integers(20, 1024))
            scanned_dst = self.rng.choice(self.topology.dmz_servers)
            duration = float(self.rng.uniform(2.0, 15.0))
            fwd_pkts = int(self.rng.integers(1, 3))
            bwd_pkts = int(self.rng.choice([0, 1], p=[0.75, 0.25]))
            fwd_bytes = fwd_pkts * 60.0
            bwd_bytes = bwd_pkts * 54.0

            flows.append(self._assemble_flow(
                src_ip=scan_attacker, dst_ip=scanned_dst, dst_port=scanned_port, timestamp=ts,
                duration=duration, fwd_pkts=fwd_pkts, bwd_pkts=bwd_pkts,
                fwd_bytes=fwd_bytes, bwd_bytes=bwd_bytes,
                fwd_syn=1, fwd_ack=0, bwd_syn=0, bwd_ack=0,
                fwd_psh=0, bwd_psh=0, fwd_rst=0, bwd_rst=bwd_pkts,
                attack_type="PORT_SCAN", label=1
            ))

        # 3. SSH/FTP Brute Force
        brute_attacker = self.rng.choice(self.topology.external_ips)
        brute_target = self.topology.dmz_servers[3]
        for i in range(n_brute):
            ts = base_time + 1000.0 + float(i * 0.3)
            duration = float(self.rng.uniform(80.0, 320.0))
            fwd_pkts = int(self.rng.integers(12, 28))
            bwd_pkts = int(self.rng.integers(10, 24))
            fwd_bytes = fwd_pkts * float(self.rng.normal(180, 20))
            bwd_bytes = bwd_pkts * float(self.rng.normal(190, 25))

            flows.append(self._assemble_flow(
                src_ip=brute_attacker, dst_ip=brute_target, dst_port=22, timestamp=ts,
                duration=duration, fwd_pkts=fwd_pkts, bwd_pkts=bwd_pkts,
                fwd_bytes=fwd_bytes, bwd_bytes=bwd_bytes,
                fwd_syn=1, fwd_ack=fwd_pkts - 1, bwd_syn=1, bwd_ack=bwd_pkts,
                fwd_psh=int(self.rng.integers(3, 7)), bwd_psh=int(self.rng.integers(3, 7)),
                fwd_rst=1, bwd_rst=0,
                attack_type="SSH_BRUTE_FORCE", label=1
            ))

        return pd.DataFrame(flows)

    def generate_zero_day_attacks(self, n_samples: int) -> pd.DataFrame:
        """Generates novel zero-day attacks: C2 periodic beaconing & stealth exfiltration."""
        flows = []
        base_time = 1715010000.0
        compromised_host = self.topology.internal_workstations[5]
        c2_server = "198.51.100.99"

        for i in range(n_samples):
            ts = base_time + float(i * 45.0 + self.rng.normal(0.0, 0.3))
            duration = float(self.rng.uniform(120.0, 300.0))
            fwd_pkts = int(self.rng.integers(15, 60))
            bwd_pkts = int(self.rng.integers(2, 6))
            fwd_bytes = fwd_pkts * float(self.rng.normal(1380, 40))
            bwd_bytes = bwd_pkts * float(self.rng.normal(64, 5))

            flows.append(self._assemble_flow(
                src_ip=compromised_host, dst_ip=c2_server, dst_port=8443, timestamp=ts,
                duration=duration, fwd_pkts=fwd_pkts, bwd_pkts=bwd_pkts,
                fwd_bytes=fwd_bytes, bwd_bytes=bwd_bytes,
                fwd_syn=1, fwd_ack=fwd_pkts, bwd_syn=1, bwd_ack=bwd_pkts,
                fwd_psh=int(self.rng.integers(4, 12)), bwd_psh=1,
                fwd_rst=0, bwd_rst=0,
                attack_type="ZERO_DAY_C2_EXFILTRATION", label=1
            ))

        return pd.DataFrame(flows)

    def generate_lateral_movement(self, n_samples: int) -> pd.DataFrame:
        """Generates stealthy lateral movement.

        Individual connections mimic normal internal SMB/SSH administrative traffic,
        making per-flow classifiers blind. Only graph topology reveals the anomaly.
        """
        flows = []
        base_time = 1715015000.0
        pivot_host = self.topology.internal_workstations[14]
        target_machines = self.topology.internal_workstations[:12] + [self.topology.internal_servers[0]]

        for i in range(n_samples):
            ts = base_time + float(i * 85.0 + self.rng.uniform(5.0, 20.0))
            dst_ip = target_machines[i % len(target_machines)]
            dst_port = int(self.rng.choice([445, 22, 3389]))
            duration = float(np.clip(self.rng.normal(90.0, 20.0), 30.0, 300.0))

            fwd_pkts = int(self.rng.integers(8, 20))
            bwd_pkts = int(self.rng.integers(8, 20))
            fwd_bytes = fwd_pkts * float(self.rng.normal(240, 30))
            bwd_bytes = bwd_pkts * float(self.rng.normal(320, 40))

            flows.append(self._assemble_flow(
                src_ip=pivot_host, dst_ip=dst_ip, dst_port=dst_port, timestamp=ts,
                duration=duration, fwd_pkts=fwd_pkts, bwd_pkts=bwd_pkts,
                fwd_bytes=fwd_bytes, bwd_bytes=bwd_bytes,
                fwd_syn=1, fwd_ack=fwd_pkts, bwd_syn=1, bwd_ack=bwd_pkts,
                fwd_psh=2, bwd_psh=2, fwd_rst=0, bwd_rst=0,
                attack_type="LATERAL_MOVEMENT", label=1
            ))

        return pd.DataFrame(flows)

    def _assemble_flow(
        self, src_ip: str, dst_ip: str, dst_port: int, timestamp: float,
        duration: float, fwd_pkts: int, bwd_pkts: int, fwd_bytes: float, bwd_bytes: float,
        fwd_syn: int, fwd_ack: int, bwd_syn: int, bwd_ack: int,
        fwd_psh: int, bwd_psh: int, fwd_rst: int, bwd_rst: int,
        attack_type: str, label: int
    ) -> Dict:
        """Computes 30 standard NetFlow statistical features from raw flow dynamics."""
        total_pkts = max(1, fwd_pkts + bwd_pkts)
        total_bytes = max(1.0, fwd_bytes + bwd_bytes)
        safe_duration_sec = max(0.001, duration / 1000.0)

        fwd_len_mean = fwd_bytes / max(1, fwd_pkts)
        bwd_len_mean = bwd_bytes / max(1, bwd_pkts)
        fwd_len_std = float(fwd_len_mean * self.rng.uniform(0.1, 0.4))
        bwd_len_std = float(bwd_len_mean * self.rng.uniform(0.1, 0.4))

        bytes_per_sec = total_bytes / safe_duration_sec
        pkts_per_sec = total_pkts / safe_duration_sec

        flow_iat_mean = duration / max(1, total_pkts - 1)
        flow_iat_std = flow_iat_mean * float(self.rng.uniform(0.2, 0.8))
        flow_iat_max = flow_iat_mean * float(self.rng.uniform(1.5, 3.5))
        flow_iat_min = max(0.01, flow_iat_mean * float(self.rng.uniform(0.1, 0.4)))

        fwd_iat_mean = duration / max(1, fwd_pkts)
        bwd_iat_mean = duration / max(1, bwd_pkts)

        header_len_ratio = (fwd_pkts * 20.0) / max(1.0, fwd_bytes)
        packet_size_variance = ((fwd_len_std ** 2) + (bwd_len_std ** 2)) / 2.0
        down_up_ratio = bwd_bytes / max(1.0, fwd_bytes)
        avg_fwd_segment = fwd_len_mean
        avg_bwd_segment = bwd_len_mean

        return {
            "timestamp": timestamp,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "dst_port": dst_port,
            "flow_duration_ms": duration,
            "total_fwd_packets": fwd_pkts,
            "total_bwd_packets": bwd_pkts,
            "total_fwd_bytes": fwd_bytes,
            "total_bwd_bytes": bwd_bytes,
            "fwd_packet_length_mean": fwd_len_mean,
            "fwd_packet_length_std": fwd_len_std,
            "bwd_packet_length_mean": bwd_len_mean,
            "bwd_packet_length_std": bwd_len_std,
            "flow_bytes_per_sec": bytes_per_sec,
            "flow_packets_per_sec": pkts_per_sec,
            "flow_iat_mean_ms": flow_iat_mean,
            "flow_iat_std_ms": flow_iat_std,
            "flow_iat_max_ms": flow_iat_max,
            "flow_iat_min_ms": flow_iat_min,
            "fwd_iat_mean_ms": fwd_iat_mean,
            "bwd_iat_mean_ms": bwd_iat_mean,
            "fwd_syn_flags": fwd_syn,
            "fwd_rst_flags": fwd_rst,
            "fwd_psh_flags": fwd_psh,
            "fwd_ack_flags": fwd_ack,
            "bwd_syn_flags": bwd_syn,
            "bwd_rst_flags": bwd_rst,
            "bwd_psh_flags": bwd_psh,
            "bwd_ack_flags": bwd_ack,
            "header_length_ratio": header_len_ratio,
            "packet_size_variance": packet_size_variance,
            "down_up_ratio": down_up_ratio,
            "avg_fwd_segment_size": avg_fwd_segment,
            "avg_bwd_segment_size": avg_bwd_segment,
            "attack_type": attack_type,
            "label": label
        }

    def generate_full_dataset(
        self,
        n_baseline: int = 12000,
        n_known: int = 5000,
        n_zero_day: int = 1500,
        n_lateral: int = 1200
    ) -> pd.DataFrame:
        """Generates the combined full dataset with all traffic profiles."""
        df_base = self.generate_baseline_flows(n_baseline)
        df_known = self.generate_known_attacks(n_known)
        df_zero = self.generate_zero_day_attacks(n_zero_day)
        df_lat = self.generate_lateral_movement(n_lateral)

        df_all = pd.concat([df_base, df_known, df_zero, df_lat], ignore_index=True)
        # Sort chronologically to simulate streaming ingestion
        df_all = df_all.sort_values("timestamp").reset_index(drop=True)
        return df_all
