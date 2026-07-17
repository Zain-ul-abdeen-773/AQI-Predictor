"""SHAP and LIME model interpretability for AQI prediction models.

Integrates SHAP (SHapley Additive exPlanations) for both tree-based
(TreeExplainer) and deep learning (GradientExplainer) models, and LIME
(Local Interpretable Model-agnostic Explanations) for any black-box model.
Provides feature contribution analysis for real-time prediction explanations.

Example:
    >>> from training_pipeline.explainability import SHAPExplainer, LIMEExplainer
    >>> shap_exp = SHAPExplainer.for_lightgbm(model, X_background)
    >>> contributions = shap_exp.explain(X_input)
    >>>
    >>> lime_exp = LIMEExplainer(model, X_train, feature_names)
    >>> explanation = lime_exp.explain_instance(X_input[0])
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


# ──────────────────────────────────────────────────────────────────────────────
# LIME Explainer
# ──────────────────────────────────────────────────────────────────────────────


class LIMEExplainer:
    """LIME (Local Interpretable Model-agnostic Explanations) for AQI models.

    Generates local surrogate explanations by perturbing input features and
    fitting an interpretable linear model in the neighborhood of each prediction.
    Works with any model that has a `predict()` method.

    Attributes:
        model: Any trained model with a predict method.
        explainer: LIME TabularExplainer instance.
        feature_names: List of feature names.
        mode: Explanation mode ('regression' for AQI prediction).
    """

    def __init__(
        self,
        model: Any,
        training_data: np.ndarray,
        feature_names: Optional[List[str]] = None,
        mode: str = "regression",
        kernel_width: float = 0.75,
        num_features: int = 15,
    ) -> None:
        """Initialize LIME explainer with training data statistics.

        Args:
            model: Trained model with predict() method.
            training_data: Training dataset for computing statistics
                (mean, std, quartiles) used during perturbation.
            feature_names: List of feature names.
            mode: 'regression' for continuous AQI prediction.
            kernel_width: Width of the exponential kernel for weighting
                perturbed samples (smaller = more local).
            num_features: Default number of top features in explanations.
        """
        import lime.lime_tabular

        self.model = model
        self.feature_names = feature_names or [
            f"feature_{i}" for i in range(training_data.shape[1])
        ]
        self.mode = mode
        self.num_features = num_features

        # Extract raw predict function
        self._predict_fn = self._get_predict_fn(model)

        # Create LIME TabularExplainer
        self.explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data=training_data,
            feature_names=self.feature_names,
            mode=mode,
            kernel_width=kernel_width,
            verbose=False,
            discretize_continuous=True,
        )

        logger.info(
            "Created LIME TabularExplainer (%s mode) with %d training samples, "
            "%d features, kernel_width=%.2f",
            mode, len(training_data), len(self.feature_names), kernel_width,
        )

    @staticmethod
    def _get_predict_fn(model: Any):
        """Extract a callable predict function from various model wrappers.

        Handles sklearn pipelines, custom model classes, and raw models.

        Args:
            model: Any model object.

        Returns:
            Callable that takes numpy array and returns predictions.
        """
        if hasattr(model, "predict"):
            return model.predict
        elif hasattr(model, "model") and hasattr(model.model, "predict"):
            return model.model.predict
        else:
            raise ValueError(
                f"Model of type {type(model).__name__} does not have a predict() method"
            )

    def explain_instance(
        self,
        instance: np.ndarray,
        num_features: Optional[int] = None,
        num_samples: int = 5000,
    ) -> Dict[str, Any]:
        """Generate LIME explanation for a single prediction.

        Args:
            instance: Single feature vector (1D array of shape [n_features]).
            num_features: Number of top features to include. Defaults to
                self.num_features.
            num_samples: Number of perturbations to generate for the
                local surrogate model.

        Returns:
            Dict containing:
                - predicted_value: The model's prediction for this instance.
                - intercept: Intercept of the local linear model.
                - local_r2: R-squared of the local surrogate fit.
                - contributions: List of dicts with feature_name, weight,
                  feature_value, and direction.
        """
        n_features = num_features or self.num_features

        try:
            explanation = self.explainer.explain_instance(
                data_row=instance,
                predict_fn=self._predict_fn,
                num_features=n_features,
                num_samples=num_samples,
            )
        except Exception as e:
            logger.error("LIME explanation failed: %s", e)
            return {
                "predicted_value": float(self._predict_fn(instance.reshape(1, -1))[0]),
                "intercept": 0.0,
                "local_r2": 0.0,
                "contributions": [],
                "error": str(e),
            }

        # Extract results
        predicted_value = float(self._predict_fn(instance.reshape(1, -1))[0])
        feature_contributions = explanation.as_list()
        local_r2 = explanation.score

        contributions = []
        for feature_desc, weight in feature_contributions:
            # Parse feature name from LIME's description (e.g., "temperature_c > 25.0")
            feat_name = feature_desc.split(" ")[0] if " " in feature_desc else feature_desc

            # Get the index and actual value
            feat_idx = None
            for i, name in enumerate(self.feature_names):
                if name in feature_desc:
                    feat_idx = i
                    feat_name = name
                    break

            feat_value = float(instance[feat_idx]) if feat_idx is not None else 0.0
            direction = "increase" if weight > 0.01 else ("decrease" if weight < -0.01 else "neutral")

            contributions.append({
                "feature_name": feat_name,
                "feature_description": feature_desc,
                "weight": round(float(weight), 4),
                "feature_value": round(feat_value, 4),
                "direction": direction,
            })

        result = {
            "predicted_value": round(predicted_value, 2),
            "intercept": round(float(explanation.intercept[0]) if hasattr(explanation.intercept, '__len__') else float(explanation.intercept), 4),
            "local_r2": round(float(local_r2), 4),
            "contributions": contributions,
        }

        logger.info(
            "LIME explanation: predicted=%.1f, R2=%.3f, top_feature=%s (%.4f)",
            predicted_value, local_r2,
            contributions[0]["feature_name"] if contributions else "N/A",
            contributions[0]["weight"] if contributions else 0.0,
        )
        return result

    def explain_batch(
        self,
        X: np.ndarray,
        num_features: Optional[int] = None,
        num_samples: int = 3000,
    ) -> List[Dict[str, Any]]:
        """Generate LIME explanations for multiple instances.

        Args:
            X: Feature matrix (n_samples, n_features).
            num_features: Number of top features per explanation.
            num_samples: Perturbation samples per instance.

        Returns:
            List of explanation dicts, one per input sample.
        """
        explanations = []
        for i in range(len(X)):
            exp = self.explain_instance(
                instance=X[i],
                num_features=num_features,
                num_samples=num_samples,
            )
            explanations.append(exp)

        logger.info("Generated LIME explanations for %d instances", len(explanations))
        return explanations

    def get_global_importance(
        self,
        X: np.ndarray,
        num_samples_per_instance: int = 2000,
        max_instances: int = 100,
    ) -> Dict[str, float]:
        """Approximate global feature importance by averaging LIME weights.

        Computes local explanations for a sample of instances and averages
        the absolute feature weights to produce global importance scores.

        Args:
            X: Feature matrix to sample from.
            num_samples_per_instance: Perturbations per LIME explanation.
            max_instances: Maximum number of instances to explain.

        Returns:
            Dict mapping feature names to mean absolute LIME weights.
        """
        # Sample instances if dataset is large
        n = min(max_instances, len(X))
        indices = np.random.choice(len(X), size=n, replace=False)
        X_sample = X[indices]

        # Accumulate weights
        weight_accumulator: Dict[str, List[float]] = {
            name: [] for name in self.feature_names
        }

        for i in range(n):
            exp = self.explain_instance(
                instance=X_sample[i],
                num_samples=num_samples_per_instance,
            )
            for contrib in exp.get("contributions", []):
                feat_name = contrib["feature_name"]
                if feat_name in weight_accumulator:
                    weight_accumulator[feat_name].append(abs(contrib["weight"]))

        # Compute mean absolute weight
        importance = {}
        for name, weights in weight_accumulator.items():
            if weights:
                importance[name] = round(float(np.mean(weights)), 4)

        # Sort by importance
        importance = dict(
            sorted(importance.items(), key=lambda x: x[1], reverse=True)
        )

        logger.info(
            "LIME global importance computed from %d instances. Top: %s",
            n, list(importance.keys())[:5],
        )
        return importance

    def save(self, path: Path) -> None:
        """Serialize LIME explainer metadata to disk.

        Note: The LIME explainer itself is lightweight (stores training stats),
        but the model reference is NOT serialized. Reload the model separately.

        Args:
            path: File path for saving (.pkl).
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "feature_names": self.feature_names,
                "mode": self.mode,
                "num_features": self.num_features,
                "explainer": self.explainer,
            }, f)
        logger.info("Saved LIME explainer to %s", path)

    @classmethod
    def load(
        cls,
        path: Path,
        model: Any,
    ) -> "LIMEExplainer":
        """Load a serialized LIME explainer from disk.

        Args:
            path: Path to saved explainer file.
            model: The trained model to attach (must have predict()).

        Returns:
            LIMEExplainer: Loaded explainer instance.
        """
        with open(path, "rb") as f:
            data = pickle.load(f)

        instance = cls.__new__(cls)
        instance.model = model
        instance.feature_names = data["feature_names"]
        instance.mode = data["mode"]
        instance.num_features = data["num_features"]
        instance.explainer = data["explainer"]
        instance._predict_fn = cls._get_predict_fn(model)

        logger.info("Loaded LIME explainer from %s", path)
        return instance
