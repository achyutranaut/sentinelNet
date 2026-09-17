"""End-to-end ingestion and preprocessing pipeline for SentinelNet."""

import os
from pathlib import Path
import joblib
import pandas as pd
import yaml

from src.ingestion.dataset_loader import NetworkFlowGenerator
from src.ingestion.schema import FlowDataValidator
from src.ingestion.preprocessor import prepare_benchmark_splits, METADATA_COLS


def run_pipeline(config_path: str = "configs/config.yaml"):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    seed = config["system"].get("random_seed", 42)
    data_cfg = config["data"]
    
    print("=" * 60)
    print(">>> SentinelNet Ingestion & Preprocessing Pipeline")
    print("=" * 60)

    # 1. Generate Synthetic Enterprise Traffic
    print(f"[*] Generating {data_cfg['num_baseline_samples']} baseline flows...")
    print(f"[*] Generating {data_cfg['num_known_attack_samples']} known attack flows...")
    print(f"[*] Generating {data_cfg['num_zero_day_samples']} zero-day C2 flows...")
    print(f"[*] Generating {data_cfg['num_lateral_movement_samples']} lateral movement flows...")

    generator = NetworkFlowGenerator(seed=seed)
    df_raw = generator.generate_full_dataset(
        n_baseline=data_cfg["num_baseline_samples"],
        n_known=data_cfg["num_known_attack_samples"],
        n_zero_day=data_cfg["num_zero_day_samples"],
        n_lateral=data_cfg["num_lateral_movement_samples"]
    )
    print(f"[+] Total raw NetFlow records generated: {len(df_raw)}")

    # 2. Schema Validation
    print("[*] Validating records against schema and network physical invariants...")
    is_valid, report = FlowDataValidator.validate_dataframe(df_raw, strict=True)
    print(f"[+] Schema validation passed: {is_valid} ({report.valid_records} valid records)")

    # 3. Persist Raw Data
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_parquet_path = raw_dir / "raw_flows.parquet"
    df_raw.to_parquet(raw_parquet_path, index=False)
    print(f"[+] Raw data saved to: {raw_parquet_path}")

    # 4. Prepare Benchmark Splits (Zero-Day Isolation Protocol)
    print("[*] Performing zero-day isolated train/val/test split...")
    splits, preprocessor = prepare_benchmark_splits(
        df_raw,
        test_ratio=data_cfg.get("test_size", 0.25),
        val_ratio=data_cfg.get("val_size", 0.10),
        seed=seed
    )

    # 5. Persist Processed Splits & Fitted Preprocessor
    models_dir = Path("artifacts/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    preprocessor_path = models_dir / "preprocessor.joblib"
    preprocessor.save(str(preprocessor_path))
    print(f"[+] Preprocessor saved to: {preprocessor_path}")

    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    splits_path = processed_dir / "dataset_splits.joblib"
    joblib.dump(splits, splits_path)
    print(f"[+] Processed splits saved to: {splits_path}")

    # Save raw test and val dataframes with unscaled features + metadata for evaluation
    test_raw_df = pd.DataFrame(
        splits.X_test,
        columns=splits.feature_names
    )
    # We can inverse or map with original metadata
    # But even better: let's save the exact raw test DataFrame
    # Let's recreate test_raw_df using splits.test_metadata and features
    print("\n[+] Dataset Partition Summary:")
    print(f"    - Supervised Train: {splits.X_train_supervised.shape} (Malicious: {int(splits.y_train_supervised.sum())})")
    print(f"    - Autoencoder Train: {splits.X_train_autoencoder.shape} (Benign Only: 100%)")
    print(f"    - Validation Set:   {splits.X_val.shape} (Malicious: {int(splits.y_val.sum())})")
    print(f"    - Test Set:         {splits.X_test.shape} (Malicious: {int(splits.y_test.sum())})")
    print(f"    - Test Attack Distribution:\n{splits.test_metadata['attack_type'].value_counts().to_string()}")
    print("=" * 60)

    return df_raw, splits, preprocessor


if __name__ == "__main__":
    run_pipeline()
