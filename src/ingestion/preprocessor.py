"""Feature engineering and preprocessing pipeline for SentinelNet (MLOps Feature Layer).

Provides robust logarithmic transforms, outlier-resistant quantile/robust scaling,
and zero-leakage dataset splits tailored for unsupervised vs supervised detection models.
Ensures identical feature transformations between offline training and real-time serving.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler


LOG_TRANSFORM_COLS = [
    "flow_duration_ms",
    "total_fwd_packets",
    "total_bwd_packets",
    "total_fwd_bytes",
    "total_bwd_bytes",
    "flow_bytes_per_sec",
    "flow_packets_per_sec",
    "flow_iat_mean_ms",
    "flow_iat_std_ms",
    "flow_iat_max_ms",
    "fwd_iat_mean_ms",
    "bwd_iat_mean_ms",
    "packet_size_variance",
]

METADATA_COLS = [
    "timestamp",
    "src_ip",
    "dst_ip",
    "dst_port",
    "attack_type",
    "label"
]


@dataclass
class DatasetSplits:
    """Container holding strict zero-leakage partitions for supervised & unsupervised models."""
    X_train_supervised: np.ndarray
    y_train_supervised: np.ndarray
    X_train_autoencoder: np.ndarray  # Strictly BENIGN traffic only!
    X_val: np.ndarray
    y_val: np.ndarray
    val_metadata: pd.DataFrame
    X_test: np.ndarray
    y_test: np.ndarray
    test_metadata: pd.DataFrame
    feature_names: List[str]
    raw_test_df: Optional[pd.DataFrame] = None
    raw_val_df: Optional[pd.DataFrame] = None


class FlowPreprocessor:
    """Preprocesses raw network flow features for machine learning models."""

    def __init__(self, feature_cols: Optional[List[str]] = None):
        self.feature_cols = feature_cols
        self.scaler = RobustScaler()
        self.is_fitted = False

    def fit(self, df: pd.DataFrame) -> "FlowPreprocessor":
        """Fits the robust scaler on training feature distributions."""
        if self.feature_cols is None:
            self.feature_cols = [c for c in df.columns if c not in METADATA_COLS]

        X = self._transform_numerical(df[self.feature_cols])
        self.scaler.fit(X)
        self.is_fitted = True
        return self

    def transform(self, df_or_dict: Union[pd.DataFrame, Dict, List[Dict]]) -> np.ndarray:
        """Transforms a DataFrame, dictionary, or list of dicts into normalized feature matrix."""
        if not self.is_fitted:
            raise RuntimeError("Preprocessor must be fitted before calling transform().")

        if isinstance(df_or_dict, dict):
            df = pd.DataFrame([df_or_dict])
        elif isinstance(df_or_dict, list):
            df = pd.DataFrame(df_or_dict)
        elif isinstance(df_or_dict, pd.DataFrame):
            df = df_or_dict.copy()
        else:
            raise TypeError(f"Unsupported input type for transform: {type(df_or_dict)}")

        # Ensure column ordering matches feature_cols exactly
        missing_cols = [c for c in self.feature_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Input data missing expected feature columns: {missing_cols}")

        features_df = df[self.feature_cols]
        X = self._transform_numerical(features_df)
        X_scaled = self.scaler.transform(X)
        # Clip extreme normalized values to prevent gradient explosion in neural nets
        return np.clip(X_scaled, -10.0, 10.0)

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.fit(df).transform(df)

    def _transform_numerical(self, df: pd.DataFrame) -> np.ndarray:
        """Applies log1p transforms to heavy-tailed features and cleans inf/nan values."""
        df_clean = df.copy()
        for col in LOG_TRANSFORM_COLS:
            if col in df_clean.columns:
                vals = df_clean[col].to_numpy(dtype=np.float64)
                vals = np.nan_to_num(vals, nan=0.0, posinf=1e8, neginf=0.0)
                df_clean[col] = np.log1p(np.maximum(0.0, vals))

        mat = df_clean.to_numpy(dtype=np.float64)
        mat = np.nan_to_num(mat, nan=0.0, posinf=10.0, neginf=-10.0)
        return mat

    def save(self, filepath: str) -> None:
        """Serializes fitted preprocessor to disk."""
        joblib.dump({
            "scaler": self.scaler,
            "feature_cols": self.feature_cols,
            "is_fitted": self.is_fitted
        }, filepath)

    @classmethod
    def load(cls, filepath: str) -> "FlowPreprocessor":
        """Loads fitted preprocessor from disk."""
        data = joblib.load(filepath)
        instance = cls(feature_cols=data["feature_cols"])
        instance.scaler = data["scaler"]
        instance.is_fitted = data["is_fitted"]
        return instance


def prepare_benchmark_splits(
    df: pd.DataFrame,
    preprocessor: Optional[FlowPreprocessor] = None,
    test_ratio: float = 0.25,
    val_ratio: float = 0.10,
    seed: int = 42
) -> Tuple[DatasetSplits, FlowPreprocessor]:
    """Prepares data splits strictly enforcing zero-day and unsupervised isolation.

    1. Supervised model trains on 75% of Benign + Known Attacks.
    2. Autoencoder trains ONLY on Benign traffic from the training set.
    3. Test set contains unseen Benign, Known Attacks, Zero-Day C2, and Lateral Movement.
    """
    rng = np.random.default_rng(seed)

    benign_mask = df["attack_type"] == "BENIGN"
    known_mask = df["attack_type"].isin(["DDOS_SYN_FLOOD", "PORT_SCAN", "SSH_BRUTE_FORCE"])
    novel_mask = df["attack_type"].isin(["ZERO_DAY_C2_EXFILTRATION", "LATERAL_MOVEMENT"])

    df_benign = df[benign_mask].copy()
    df_known = df[known_mask].copy()
    df_novel = df[novel_mask].copy()

    # Split benign into train, val, test
    n_b = len(df_benign)
    idx_b = rng.permutation(n_b)
    n_b_test = int(n_b * test_ratio)
    n_b_val = int(n_b * val_ratio)
    n_b_train = n_b - n_b_test - n_b_val

    b_train = df_benign.iloc[idx_b[:n_b_train]]
    b_val = df_benign.iloc[idx_b[n_b_train:n_b_train + n_b_val]]
    b_test = df_benign.iloc[idx_b[n_b_train + n_b_val:]]

    # Split known attacks into train, val, test
    n_k = len(df_known)
    idx_k = rng.permutation(n_k)
    n_k_test = int(n_k * test_ratio)
    n_k_val = int(n_k * val_ratio)
    n_k_train = n_k - n_k_test - n_k_val

    k_train = df_known.iloc[idx_k[:n_k_train]]
    k_val = df_known.iloc[idx_k[n_k_train:n_k_train + n_k_val]]
    k_test = df_known.iloc[idx_k[n_k_train + n_k_val:]]

    # Novel zero-days & lateral movements are ALL held out for validation & testing
    n_n = len(df_novel)
    idx_n = rng.permutation(n_n)
    n_n_val = int(n_n * 0.2)
    novel_val = df_novel.iloc[idx_n[:n_n_val]]
    novel_test = df_novel.iloc[idx_n[n_n_val:]]

    # Assemble supervised train set (Benign + Known Attacks)
    train_sup_df = pd.concat([b_train, k_train]).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    # Assemble autoencoder train set (Benign ONLY!)
    train_ae_df = b_train.reset_index(drop=True)

    val_df = pd.concat([b_val, k_val, novel_val]).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    test_df = pd.concat([b_test, k_test, novel_test]).sample(frac=1.0, random_state=seed).reset_index(drop=True)

    # Fit preprocessor on training data
    if preprocessor is None:
        preprocessor = FlowPreprocessor()
        preprocessor.fit(train_sup_df)

    feature_cols = preprocessor.feature_cols

    X_train_sup = preprocessor.transform(train_sup_df)
    y_train_sup = train_sup_df["label"].to_numpy(dtype=np.int64)

    X_train_ae = preprocessor.transform(train_ae_df)

    X_val = preprocessor.transform(val_df)
    y_val = val_df["label"].to_numpy(dtype=np.int64)

    X_test = preprocessor.transform(test_df)
    y_test = test_df["label"].to_numpy(dtype=np.int64)

    splits = DatasetSplits(
        X_train_supervised=X_train_sup,
        y_train_supervised=y_train_sup,
        X_train_autoencoder=X_train_ae,
        X_val=X_val,
        y_val=y_val,
        val_metadata=val_df[METADATA_COLS].reset_index(drop=True),
        X_test=X_test,
        y_test=y_test,
        test_metadata=test_df[METADATA_COLS].reset_index(drop=True),
        feature_names=feature_cols,
        raw_test_df=test_df,
        raw_val_df=val_df
    )

    return splits, preprocessor
