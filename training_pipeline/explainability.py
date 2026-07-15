"""SHAP-based model interpretability for AQI prediction models.

Integrates SHAP (SHapley Additive exPlanations) for both tree-based
(TreeExplainer) and deep learning (GradientExplainer) models. Provides
feature contribution analysis for real-time prediction explanations.

Example:
    >>> from training_pipeline.explainability import SHAPExplainer
    >>> explainer = SHAPExplainer.for_lightgbm(model, X_background)
    >>> contributions = explainer.explain(X_input)
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from config.schemas import SHAPExplanation

logger = logging.getLogger(__name__)


class SHAPExplainer:
    """Unified SHAP explainer for tree and deep learning models.

    Wraps SHAP's TreeExplainer and GradientExplainer into a consistent
    interface for computing and visualizing feature contributions.

    Attributes:
        explainer: SHAP explainer instance (TreeExplainer or GradientExplainer).
        feature_names: List of feature names.
        explainer_type: Type of SHAP explainer used.
        base_value: Expected base prediction value.
    """

    def __init__(
        self,
        explainer: Any,
        feature_names: List[str],
        explainer_type: str = "tree",
        base_value: float = 0.0,
    ) -> None:
        self.explainer = explainer
        self.feature_names = feature_names
        self.explainer_type = explainer_type
        self.base_value = base_value

    @classmethod
    def for_lightgbm(
        cls,
        model: Any,
        background_data: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> "SHAPExplainer":
        """Create a TreeExplainer for a LightGBM model.

        Args:
            model: Trained LightGBM model (or sklearn-compatible).
            background_data: Background dataset for SHAP calculations.
            feature_names: Feature name list.

        Returns:
            SHAPExplainer: Configured explainer for tree models.
        """
        import shap

        # Handle wrapped models (sklearn pipeline, LightGBMOptimized, etc.)
        raw_model = model
        if hasattr(model, "model"):
            raw_model = model.model
        if hasattr(raw_model, "named_steps"):
            raw_model = raw_model.named_steps.get("regressor", raw_model)

        explainer = shap.TreeExplainer(raw_model, background_data)

        names = feature_names or [f"feature_{i}" for i in range(background_data.shape[1])]
        base_val = float(explainer.expected_value) if np.isscalar(explainer.expected_value) else float(explainer.expected_value[0])

        logger.info(
            "Created TreeExplainer with %d background samples, base_value=%.4f",
            len(background_data), base_val,
        )

        return cls(
            explainer=explainer,
            feature_names=names,
            explainer_type="tree",
            base_value=base_val,
        )

    @classmethod
    def for_pytorch(
        cls,
        model: Any,
        background_data: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> "SHAPExplainer":
        """Create a GradientExplainer for a PyTorch model.

        Args:
            model: Trained PyTorch model.
            background_data: Background dataset (numpy array).
            feature_names: Feature name list.

        Returns:
            SHAPExplainer: Configured explainer for deep learning models.
        """
        import shap
        import torch

        # Get the neural network
        network = model
        if hasattr(model, "model"):
            network = model.model

        network.eval()

        # Convert background to tensor
        bg_tensor = torch.FloatTensor(background_data)
        if hasattr(model, "device"):
            bg_tensor = bg_tensor.to(model.device)

        explainer = shap.GradientExplainer(network, bg_tensor)
        names = feature_names or [f"feature_{i}" for i in range(background_data.shape[-1])]

        logger.info(
            "Created GradientExplainer with %d background samples",
            len(background_data),
        )

        return cls(
            explainer=explainer,
            feature_names=names,
            explainer_type="gradient",
            base_value=float(np.mean(background_data)),
        )

    def explain(
        self,
        X: np.ndarray,
        top_k: int = 15,
    ) -> List[List[SHAPExplanation]]:
        """Compute SHAP explanations for input data.

        Args:
            X: Input feature matrix (n_samples, n_features) or sequences.
            top_k: Number of top features to include per sample.

        Returns:
            List of SHAPExplanation lists, one per input sample.
        """
        import shap

        try:
            if self.explainer_type == "gradient":
                import torch
                if not isinstance(X, torch.Tensor):
                    X_input = torch.FloatTensor(X)
                else:
                    X_input = X
                shap_values = self.explainer.shap_values(X_input)
            else:
                shap_values = self.explainer.shap_values(X)
        except Exception as e:
            logger.error("SHAP computation failed: %s", e)
            return []

        # Handle different SHAP value shapes
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        if isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            # Sequence data: average over time dimension
            shap_values = np.mean(shap_values, axis=1)

        all_explanations: List[List[SHAPExplanation]] = []

        for i in range(len(X)):
            sample_shap = shap_values[i] if i < len(shap_values) else np.zeros(len(self.feature_names))

            # Get feature values
            if X.ndim == 3:
                sample_features = X[i, -1, :]  # Last time step
            else:
                sample_features = X[i]

            # Sort by absolute SHAP value
            abs_shap = np.abs(sample_shap)
            top_indices = np.argsort(abs_shap)[-top_k:][::-1]

            explanations = []
            for idx in top_indices:
                if idx >= len(self.feature_names):
                    continue

                sv = float(sample_shap[idx])
                fv = float(sample_features[idx]) if idx < len(sample_features) else 0.0

                direction = "increase" if sv > 0.01 else ("decrease" if sv < -0.01 else "neutral")

                explanations.append(
                    SHAPExplanation(
                        feature_name=self.feature_names[idx],
                        shap_value=round(sv, 4),
                        feature_value=round(fv, 4),
                        direction=direction,
                    )
                )

            all_explanations.append(explanations)

        logger.info("Computed SHAP explanations for %d samples", len(all_explanations))
        return all_explanations

    def get_global_importance(
        self,
        X: np.ndarray,
        top_k: int = 20,
    ) -> Dict[str, float]:
        """Compute global feature importance via mean absolute SHAP values.

        Args:
            X: Feature matrix for computing global importance.
            top_k: Number of top features to return.

        Returns:
            Dict mapping feature names to mean |SHAP| values.
        """
        try:
            shap_values = self.explainer.shap_values(X)
        except Exception as e:
            logger.error("Global importance computation failed: %s", e)
            return {}

        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        if shap_values.ndim == 3:
            shap_values = np.mean(shap_values, axis=1)

        mean_abs = np.mean(np.abs(shap_values), axis=0)

        importance = {}
        for idx in np.argsort(mean_abs)[-top_k:][::-1]:
            if idx < len(self.feature_names):
                importance[self.feature_names[idx]] = round(float(mean_abs[idx]), 4)

        logger.info("Global SHAP importance computed for %d features", len(importance))
        return importance

    def save(self, path: Path) -> None:
        """Serialize the explainer to disk.

        Args:
            path: File path for saving (.pkl).
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "explainer": self.explainer,
                "feature_names": self.feature_names,
                "explainer_type": self.explainer_type,
                "base_value": self.base_value,
            }, f)
        logger.info("Saved SHAP explainer to %s", path)

    @classmethod
    def load(cls, path: Path) -> "SHAPExplainer":
        """Load a serialized explainer from disk.

        Args:
            path: Path to saved explainer file.

        Returns:
            SHAPExplainer: Loaded explainer instance.
        """
        with open(path, "rb") as f:
            data = pickle.load(f)

        instance = cls(
            explainer=data["explainer"],
            feature_names=data["feature_names"],
            explainer_type=data["explainer_type"],
            base_value=data["base_value"],
        )
        logger.info("Loaded SHAP explainer from %s", path)
        return instance
