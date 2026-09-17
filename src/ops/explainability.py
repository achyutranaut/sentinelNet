"""Tier 5: SHAP Explainability Engine for Incident Response Triage.

Computes TreeSHAP feature attributions for LightGBM predictions to provide
SOC analysts with immediate, transparent explanations of what dynamic flow traits
triggered an attack classification.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import numpy as np
import shap

from src.models.supervised_classifier import SupervisedFlowClassifier


@dataclass
class FlowFeatureExplanation:
    feature_name: str
    feature_value: float
    shap_value: float
    impact_direction: str  # "INCREASES_ATTACK_RISK" or "REDUCES_ATTACK_RISK"


@dataclass
class IncidentTriageSummary:
    predicted_probability: float
    base_value: float
    top_drivers: List[FlowFeatureExplanation]
    analyst_summary: str


class IncidentExplainabilityEngine:
    """Provides SHAP-based local and global model interpretability for SOC triage."""

    def __init__(self, classifier: SupervisedFlowClassifier):
        self.classifier = classifier
        # LightGBM booster TreeExplainer
        self.explainer = shap.TreeExplainer(classifier.model)
        self.feature_names = classifier.feature_names

    def explain_flow(
        self,
        X_flow: np.ndarray,
        raw_flow_dict: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> IncidentTriageSummary:
        """Generates a detailed triage explanation for a single flow feature vector."""
        if X_flow.ndim == 1:
            X_flow = X_flow.reshape(1, -1)

        shap_values = self.explainer.shap_values(X_flow)
        # For binary classification, shap_values might be a list [class0, class1] or array
        if isinstance(shap_values, list):
            sv = shap_values[1][0]
            base_val = float(self.explainer.expected_value[1])
        else:
            sv = shap_values[0] if shap_values.ndim == 2 else shap_values[0, :, 1]
            base_val = float(self.explainer.expected_value if np.isscalar(self.explainer.expected_value) else self.explainer.expected_value[0])

        prob = float(self.classifier.predict_proba(X_flow)[0])

        # Rank features by absolute SHAP attribution
        ranked_indices = np.argsort(np.abs(sv))[::-1][:top_k]

        drivers: List[FlowFeatureExplanation] = []
        for idx in ranked_indices:
            feat_name = self.feature_names[idx] if idx < len(self.feature_names) else f"feature_{idx}"
            feat_val = float(raw_flow_dict.get(feat_name, X_flow[0, idx])) if raw_flow_dict else float(X_flow[0, idx])
            shap_val = float(sv[idx])
            direction = "INCREASES_ATTACK_RISK" if shap_val > 0 else "REDUCES_ATTACK_RISK"

            drivers.append(FlowFeatureExplanation(
                feature_name=feat_name,
                feature_value=feat_val,
                shap_value=shap_val,
                impact_direction=direction
            ))

        # Construct human-readable SOC narrative
        top_positive = [d for d in drivers if d.shap_value > 0]
        if top_positive:
            reasons = ", ".join([f"'{d.feature_name}' (attribution +{d.shap_value:.3f})" for d in top_positive[:3]])
            summary = f"Alert classified with {prob:.1%} confidence. Primary threat drivers: {reasons}."
        else:
            summary = f"Flow scored low attack probability ({prob:.1%}). Traffic conforms to baseline distributions."

        return IncidentTriageSummary(
            predicted_probability=prob,
            base_value=base_val,
            top_drivers=drivers,
            analyst_summary=summary
        )
