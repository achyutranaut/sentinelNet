"""Data Validation Contracts and Schema Invariants for SentinelNet (MLOps Data Layer).

Defines Pydantic data contract models and DataFrame invariant validators to ensure
training-serving data consistency and reject malformed/anomalous NetFlow records
before feature transformation.
"""

from ipaddress import IPv4Address, ip_address
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator


class NetFlowRecord(BaseModel):
    """Pydantic schema contract representing a single incoming network flow."""

    timestamp: float = Field(..., description="UNIX epoch timestamp in seconds")
    src_ip: str = Field(..., description="Source IPv4 address")
    dst_ip: str = Field(..., description="Destination IPv4 address")
    dst_port: int = Field(..., ge=1, le=65535, description="Destination TCP/UDP port (1-65535)")
    flow_duration_ms: float = Field(..., ge=0.0, le=86400000.0, description="Flow duration in milliseconds")
    total_fwd_packets: int = Field(..., ge=0, description="Total forward packets")
    total_bwd_packets: int = Field(..., ge=0, description="Total backward packets")
    total_fwd_bytes: float = Field(..., ge=0.0, description="Total bytes sent in forward direction")
    total_bwd_bytes: float = Field(..., ge=0.0, description="Total bytes sent in backward direction")
    fwd_packet_length_mean: float = Field(0.0, ge=0.0)
    fwd_packet_length_std: float = Field(0.0, ge=0.0)
    bwd_packet_length_mean: float = Field(0.0, ge=0.0)
    bwd_packet_length_std: float = Field(0.0, ge=0.0)
    flow_bytes_per_sec: float = Field(0.0, ge=0.0)
    flow_packets_per_sec: float = Field(0.0, ge=0.0)
    flow_iat_mean_ms: float = Field(0.0, ge=0.0)
    flow_iat_std_ms: float = Field(0.0, ge=0.0)
    flow_iat_max_ms: float = Field(0.0, ge=0.0)
    flow_iat_min_ms: float = Field(0.0, ge=0.0)
    fwd_iat_mean_ms: float = Field(0.0, ge=0.0)
    bwd_iat_mean_ms: float = Field(0.0, ge=0.0)
    fwd_syn_flags: int = Field(0, ge=0)
    fwd_rst_flags: int = Field(0, ge=0)
    fwd_psh_flags: int = Field(0, ge=0)
    fwd_ack_flags: int = Field(0, ge=0)
    bwd_syn_flags: int = Field(0, ge=0)
    bwd_rst_flags: int = Field(0, ge=0)
    bwd_psh_flags: int = Field(0, ge=0)
    bwd_ack_flags: int = Field(0, ge=0)
    header_length_ratio: float = Field(0.0, ge=0.0)
    packet_size_variance: float = Field(0.0, ge=0.0)
    down_up_ratio: float = Field(0.0, ge=0.0)
    avg_fwd_segment_size: float = Field(0.0, ge=0.0)
    avg_bwd_segment_size: float = Field(0.0, ge=0.0)
    attack_type: Optional[str] = Field("UNKNOWN", description="Ground truth or predicted attack label")
    label: Optional[int] = Field(0, ge=0, le=1, description="0=Benign, 1=Malicious")

    @field_validator("src_ip", "dst_ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        try:
            ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid IP address format: {v}")

    @model_validator(mode="after")
    def validate_packets_and_bytes(self) -> "NetFlowRecord":
        if self.total_fwd_packets + self.total_bwd_packets < 1:
            raise ValueError("A flow must have at least 1 total packet (forward or backward).")
        return self


class DataValidationReport(BaseModel):
    """Summary report for batch dataset validation."""
    total_records: int
    valid_records: int
    invalid_records: int
    missing_columns: List[str]
    null_counts: Dict[str, int]
    negative_val_violations: Dict[str, int]
    is_valid: bool
    errors: List[str]


class FlowDataValidator:
    """Validates batch DataFrames and streaming records against schema invariants."""

    EXPECTED_FEATURES = [
        "flow_duration_ms", "total_fwd_packets", "total_bwd_packets",
        "total_fwd_bytes", "total_bwd_bytes", "fwd_packet_length_mean",
        "fwd_packet_length_std", "bwd_packet_length_mean", "bwd_packet_length_std",
        "flow_bytes_per_sec", "flow_packets_per_sec", "flow_iat_mean_ms",
        "flow_iat_std_ms", "flow_iat_max_ms", "flow_iat_min_ms",
        "fwd_iat_mean_ms", "bwd_iat_mean_ms", "fwd_syn_flags",
        "fwd_rst_flags", "fwd_psh_flags", "fwd_ack_flags",
        "bwd_syn_flags", "bwd_rst_flags", "bwd_psh_flags",
        "bwd_ack_flags", "header_length_ratio", "packet_size_variance",
        "down_up_ratio", "avg_fwd_segment_size", "avg_bwd_segment_size"
    ]

    NON_NEGATIVE_COLS = EXPECTED_FEATURES

    @classmethod
    def validate_dataframe(cls, df: pd.DataFrame, strict: bool = False) -> Tuple[bool, DataValidationReport]:
        """Runs full suite of data quality checks on a DataFrame."""
        total = len(df)
        missing_cols = [col for col in cls.EXPECTED_FEATURES if col not in df.columns]
        null_counts = df[cls.EXPECTED_FEATURES].isnull().sum().to_dict() if not missing_cols else {}
        
        errors: List[str] = []
        if missing_cols:
            errors.append(f"Missing required features: {missing_cols}")

        negative_counts = {}
        for col in cls.NON_NEGATIVE_COLS:
            if col in df.columns:
                neg_cnt = int((df[col] < 0).sum())
                if neg_cnt > 0:
                    negative_counts[col] = neg_cnt
                    errors.append(f"Column '{col}' has {neg_cnt} negative values.")

        # Check for Infinite values
        inf_cols = {}
        for col in cls.EXPECTED_FEATURES:
            if col in df.columns:
                inf_cnt = int(np.isinf(df[col]).sum())
                if inf_cnt > 0:
                    inf_cols[col] = inf_cnt
                    errors.append(f"Column '{col}' contains {inf_cnt} infinite values.")

        invalid_cnt = sum(negative_counts.values()) + sum(null_counts.values()) + sum(inf_cols.values())
        valid_cnt = max(0, total - invalid_cnt)
        is_valid = len(errors) == 0

        report = DataValidationReport(
            total_records=total,
            valid_records=valid_cnt,
            invalid_records=invalid_cnt,
            missing_columns=missing_cols,
            null_counts={k: int(v) for k, v in null_counts.items() if v > 0},
            negative_val_violations=negative_counts,
            is_valid=is_valid,
            errors=errors
        )

        if strict and not is_valid:
            raise ValueError(f"Data validation failed: {errors}")

        return is_valid, report

    @classmethod
    def validate_record(cls, record_dict: Dict[str, Any]) -> NetFlowRecord:
        """Validates a single flow dictionary using Pydantic."""
        return NetFlowRecord(**record_dict)
