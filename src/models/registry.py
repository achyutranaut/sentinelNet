"""Model Registry & Artifact Lineage Store for SentinelNet (MLOps Model Layer).

Provides versioning, artifact bundling (preprocessor + models), dataset hash lineage,
and lifecycle stage transitions (staging -> production -> archived) aligned with ml-ops.org principles.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import joblib
import numpy as np
import pandas as pd

from src.ingestion.preprocessor import FlowPreprocessor
from src.models.anomaly_autoencoder import AnomalyAutoencoder
from src.models.supervised_classifier import SupervisedFlowClassifier


@dataclass
class ModelMetadata:
    """Metadata manifest tracking model lineage, data fingerprint, and validation metrics."""
    model_id: str
    version: str
    created_at: str
    dataset_hash: str
    status: str  # "staging", "production", "archived"
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, Any]
    feature_names: List[str]
    description: str


class InferenceBundle:
    """Hermetic inference bundle encapsulating preprocessor and models to eliminate training-serving skew."""

    def __init__(
        self,
        preprocessor: FlowPreprocessor,
        supervised_model: SupervisedFlowClassifier,
        autoencoder_model: AnomalyAutoencoder,
        metadata: ModelMetadata
    ):
        self.preprocessor = preprocessor
        self.supervised_model = supervised_model
        self.autoencoder_model = autoencoder_model
        self.metadata = metadata

    def score_single_flow(self, flow_record: Dict[str, Any], supervised_threshold: float = 0.5) -> Dict[str, Any]:
        """Runs unified multi-tier scoring on a single raw flow dictionary."""
        # 1. Preprocess with identical robust scaling & log transforms
        X = self.preprocessor.transform(flow_record)

        # 2. Tier 1: LightGBM Supervised Scoring
        supervised_prob = float(self.supervised_model.predict_proba(X)[0])
        supervised_pred = int(supervised_prob >= supervised_threshold)

        # 3. Tier 2: Autoencoder Zero-Day Reconstruction Scoring
        recon_loss = float(self.autoencoder_model.compute_reconstruction_error(X)[0])
        ae_threshold = float(self.autoencoder_model.threshold if self.autoencoder_model.threshold else 1.0)
        autoencoder_pred = int(recon_loss >= ae_threshold)

        # 4. Multi-tier ensemble decision
        is_attack = bool(supervised_pred or autoencoder_pred)
        detection_tier = "NONE"
        if supervised_pred and autoencoder_pred:
            detection_tier = "TIER_1_AND_TIER_2"
        elif supervised_pred:
            detection_tier = "TIER_1_SUPERVISED"
        elif autoencoder_pred:
            detection_tier = "TIER_2_ZERO_DAY_ANOMALY"

        return {
            "is_attack": is_attack,
            "detection_tier": detection_tier,
            "supervised_probability": supervised_prob,
            "supervised_prediction": supervised_pred,
            "reconstruction_loss": recon_loss,
            "reconstruction_threshold": ae_threshold,
            "autoencoder_prediction": autoencoder_pred,
            "model_version": self.metadata.version
        }

    def score_batch(self, df: pd.DataFrame, supervised_threshold: float = 0.5) -> pd.DataFrame:
        """Scores a batch of flows and returns enriched DataFrame."""
        X = self.preprocessor.transform(df)
        sup_probs = self.supervised_model.predict_proba(X)
        sup_preds = (sup_probs >= supervised_threshold).astype(int)

        recon_losses = self.autoencoder_model.compute_reconstruction_error(X)
        ae_thresh = float(self.autoencoder_model.threshold if self.autoencoder_model.threshold else 1.0)
        ae_preds = (recon_losses >= ae_thresh).astype(int)

        df_out = df.copy()
        df_out["supervised_prob"] = sup_probs
        df_out["supervised_pred"] = sup_preds
        df_out["reconstruction_loss"] = recon_losses
        df_out["reconstruction_threshold"] = ae_thresh
        df_out["autoencoder_pred"] = ae_preds
        df_out["is_attack"] = (sup_preds | ae_preds).astype(int)
        return df_out


class ModelRegistry:
    """Local file-backed Model Registry managing model lifecycle and versioning."""

    def __init__(self, registry_dir: str = "artifacts/registry", models_dir: str = "artifacts/models"):
        self.registry_dir = Path(registry_dir)
        self.models_dir = Path(models_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.registry_dir / "registry_manifest.json"
        self._init_manifest()

    def _init_manifest(self) -> None:
        if not self.manifest_file.exists():
            with open(self.manifest_file, "w") as f:
                json.dump({"models": {}, "active_production_id": None}, f, indent=2)

    def _read_manifest(self) -> Dict[str, Any]:
        with open(self.manifest_file, "r") as f:
            return json.load(f)

    def _write_manifest(self, manifest: Dict[str, Any]) -> None:
        with open(self.manifest_file, "w") as f:
            json.dump(manifest, f, indent=2)

    @staticmethod
    def compute_dataset_hash(data: Union[pd.DataFrame, np.ndarray]) -> str:
        """Computes SHA256 fingerprint of dataset to enforce data-model lineage."""
        if isinstance(data, pd.DataFrame):
            bytes_data = pd.util.hash_pandas_object(data, index=True).values.tobytes()
        else:
            bytes_data = data.tobytes()
        return hashlib.sha256(bytes_data).hexdigest()[:16]

    def register_bundle(
        self,
        bundle: InferenceBundle,
        model_id: Optional[str] = None,
        promote_to_production: bool = False
    ) -> str:
        """Saves bundle to disk and records metadata in registry manifest."""
        if model_id is None:
            ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            model_id = f"sentinelnet_{bundle.metadata.version}_{ts_str}"

        bundle.metadata.model_id = model_id
        bundle_path = self.models_dir / f"{model_id}.bundle"
        joblib.dump(bundle, bundle_path)

        manifest = self._read_manifest()
        manifest["models"][model_id] = asdict(bundle.metadata)
        manifest["models"][model_id]["artifact_path"] = str(bundle_path)

        if promote_to_production:
            # Set previous production to archived
            old_prod = manifest.get("active_production_id")
            if old_prod and old_prod in manifest["models"]:
                manifest["models"][old_prod]["status"] = "archived"
            manifest["models"][model_id]["status"] = "production"
            manifest["active_production_id"] = model_id
        else:
            manifest["models"][model_id]["status"] = "staging"

        self._write_manifest(manifest)
        return model_id

    def load_bundle(self, model_id: str) -> InferenceBundle:
        """Loads a specific versioned inference bundle."""
        manifest = self._read_manifest()
        if model_id not in manifest["models"]:
            raise KeyError(f"Model ID '{model_id}' not found in registry.")

        raw_path = Path(manifest["models"][model_id]["artifact_path"])
        if raw_path.exists():
            artifact_path = raw_path
        elif (self.models_dir / raw_path.name).exists():
            artifact_path = self.models_dir / raw_path.name
        elif (self.registry_dir.parent / raw_path).exists():
            artifact_path = self.registry_dir.parent / raw_path
        else:
            artifact_path = raw_path
        bundle = joblib.load(artifact_path)
        bundle.metadata.status = manifest["models"][model_id]["status"]
        return bundle

    def get_production_bundle(self) -> InferenceBundle:
        """Loads the currently designated production inference bundle."""
        manifest = self._read_manifest()
        prod_id = manifest.get("active_production_id")
        if not prod_id or prod_id not in manifest["models"]:
            raise RuntimeError("No active production model found in registry.")
        return self.load_bundle(prod_id)

    def promote_to_production(self, model_id: str) -> None:
        """Promotes a registered model to active production status."""
        manifest = self._read_manifest()
        if model_id not in manifest["models"]:
            raise KeyError(f"Model ID '{model_id}' does not exist.")
        old_prod = manifest.get("active_production_id")
        if old_prod and old_prod in manifest["models"]:
            manifest["models"][old_prod]["status"] = "archived"
        manifest["models"][model_id]["status"] = "production"
        manifest["active_production_id"] = model_id
        self._write_manifest(manifest)

    def list_models(self) -> List[Dict[str, Any]]:
        """Lists all registered models with their metadata."""
        manifest = self._read_manifest()
        return list(manifest["models"].values())
