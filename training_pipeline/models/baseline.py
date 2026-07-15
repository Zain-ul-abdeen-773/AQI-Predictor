"""Baseline regression models for AQI prediction.

Implements Ridge and ElasticNet regressors with RobustScaler preprocessing
pipeline to handle skewed pollutant distributions. Serves as the statistical
baseline for comparison against tree ensembles and deep learning models.

Example:
    >>> from training_pipeline.models.baseline import BaselineRegressor
    >>> model = BaselineRegressor(model_type="ridge")
    >>> model.fit(X_train, y_train)
    >>> predictions = model.predict(X_test)
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import numpy as np
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from config.settings import get_settings

logger = logging.getLogger(__name__)


class BaselineRegressor:
    """Scikit-learn baseline regression model with robust preprocessing.

    Uses RobustScaler to handle outliers and skewed distributions common
    in pollutant concentration data. Supports both Ridge and ElasticNet
    regression with configurable hyperparameters.

    Attributes:
        model_type: Type of regression ('ridge' or 'elasticnet').
        pipeline: Scikit-learn Pipeline (scaler + regressor).
        is_fitted: Whether the model has been trained.
        feature_names: List of feature names used during training.
    """

    def __init__(
        self,
        model_type: Literal["ridge", "elasticnet"] = "ridge",
        alpha: float = 1.0,
        l1_ratio: float = 0.5,
        max_iter: int = 10_000,
    ) -> None:
        """Initialize the baseline regressor.

        Args:
            model_type: Type of regression model.
            alpha: Regularization strength (higher = stronger).
            l1_ratio: ElasticNet L1 ratio (0=Ridge, 1=Lasso).
            max_iter: Maximum solver iterations.
        """
        self.model_type = model_type
        self.is_fitted = False
        self.feature_names: list[str] = []

        # Build preprocessing + regression pipeline
        if model_type == "elasticnet":
            regressor = ElasticNet(
                alpha=alpha,
                l1_ratio=l1_ratio,
                max_iter=max_iter,
                random_state=42,
            )
        else:
            regressor = Ridge(
                alpha=alpha,
                max_iter=max_iter,
                solver="auto",
            )

        self.pipeline = Pipeline([
            ("scaler", RobustScaler(quantile_range=(5.0, 95.0))),
            ("regressor", regressor),
        ])

        logger.info(
            "Initialized %s regressor (alpha=%.4f)",
            model_type, alpha,
        )

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[list[str]] = None,
    ) -> "BaselineRegressor":
        """Train the baseline model.

        Args:
            X: Training feature matrix (n_samples, n_features).
            y: Target AQI values (n_samples,).
            feature_names: Optional list of feature names.

        Returns:
            Self for method chaining.
        """
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]

        logger.info(
            "Training %s on %d samples × %d features",
            self.model_type, X.shape[0], X.shape[1],
        )

        self.pipeline.fit(X, y)
        self.is_fitted = True

        # Log coefficient summary
        regressor = self.pipeline.named_steps["regressor"]
        coefs = regressor.coef_
        top_k = min(10, len(coefs))
        top_indices = np.argsort(np.abs(coefs))[-top_k:][::-1]

        logger.info("Top %d features by absolute coefficient:", top_k)
        for idx in top_indices:
            name = self.feature_names[idx] if idx < len(self.feature_names) else f"f{idx}"
            logger.info("  %s: %.6f", name, coefs[idx])

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate AQI predictions.

        Args:
            X: Feature matrix (n_samples, n_features).

        Returns:
            np.ndarray: Predicted AQI values (n_samples,).

        Raises:
            RuntimeError: If model hasn't been fitted.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        predictions = self.pipeline.predict(X)
        # Clip to valid AQI range
        predictions = np.clip(predictions, 0, 500)
        return predictions

    def get_coefficients(self) -> Dict[str, float]:
        """Get feature coefficients from the fitted model.

        Returns:
            Dict mapping feature names to coefficient values.
        """
        if not self.is_fitted:
            return {}

        regressor = self.pipeline.named_steps["regressor"]
        coefs = regressor.coef_

        return {
            name: float(coef)
            for name, coef in zip(self.feature_names, coefs)
        }

    def get_params(self) -> Dict[str, Any]:
        """Get model hyperparameters.

        Returns:
            Dict of model parameters.
        """
        regressor = self.pipeline.named_steps["regressor"]
        params = regressor.get_params()
        params["model_type"] = self.model_type
        return params

    def save(self, path: Path) -> None:
        """Save the trained model to disk.

        Args:
            path: File path to save the model (.pkl).
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "pipeline": self.pipeline,
                "model_type": self.model_type,
                "feature_names": self.feature_names,
                "is_fitted": self.is_fitted,
            }, f)
        logger.info("Saved %s model to %s", self.model_type, path)

    @classmethod
    def load(cls, path: Path) -> "BaselineRegressor":
        """Load a trained model from disk.

        Args:
            path: Path to the saved model file.

        Returns:
            BaselineRegressor: Loaded model instance.
        """
        with open(path, "rb") as f:
            data = pickle.load(f)

        model = cls(model_type=data["model_type"])
        model.pipeline = data["pipeline"]
        model.feature_names = data["feature_names"]
        model.is_fitted = data["is_fitted"]
        logger.info("Loaded %s model from %s", model.model_type, path)
        return model
