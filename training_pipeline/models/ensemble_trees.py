"""Ensemble tree models: Random Forest, Extra Trees, Gradient Boosting, CatBoost.

Provides sklearn-based ensemble models with standardized interfaces for
the AQI prediction pipeline. Each model includes RobustScaler preprocessing
and feature importance extraction.

Example:
    >>> from training_pipeline.models.ensemble_trees import RandomForestModel
    >>> model = RandomForestModel(n_estimators=500)
    >>> model.fit(X_train, y_train, feature_names=features)
    >>> predictions = model.predict(X_test)
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger(__name__)


class _BaseEnsembleTree:
    """Base class for sklearn ensemble tree models.

    Provides common functionality: RobustScaler pipeline, feature
    importance extraction, save/load, and predict with clipping.
    """

    model_name: str = "base"

    def __init__(self) -> None:
        self.pipeline: Optional[Pipeline] = None
        self.is_fitted = False
        self.feature_names: List[str] = []
        self.feature_importances: Dict[str, float] = {}

    def _build_pipeline(self, regressor) -> Pipeline:
        return Pipeline([
            ("scaler", RobustScaler(quantile_range=(5.0, 95.0))),
            ("regressor", regressor),
        ])

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> "_BaseEnsembleTree":
        self.feature_names = feature_names or [f"f{i}" for i in range(X.shape[1])]

        logger.info(
            "Training %s on %d samples × %d features",
            self.model_name, X.shape[0], X.shape[1],
        )

        self.pipeline.fit(X, y)
        self.is_fitted = True

        # Extract feature importances
        regressor = self.pipeline.named_steps["regressor"]
        if hasattr(regressor, "feature_importances_"):
            importances = regressor.feature_importances_
            self.feature_importances = {
                name: float(imp)
                for name, imp in sorted(
                    zip(self.feature_names, importances),
                    key=lambda x: -x[1],
                )
            }
            logger.info(
                "%s top 5 features: %s",
                self.model_name,
                list(self.feature_importances.keys())[:5],
            )

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError(f"{self.model_name} must be fitted before prediction")
        return np.clip(self.pipeline.predict(X), 0, 500)

    def get_params(self) -> Dict[str, Any]:
        regressor = self.pipeline.named_steps["regressor"]
        params = regressor.get_params()
        params["model_type"] = self.model_name
        return params

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "pipeline": self.pipeline,
                "model_name": self.model_name,
                "feature_names": self.feature_names,
                "feature_importances": self.feature_importances,
                "is_fitted": self.is_fitted,
            }, f)
        logger.info("Saved %s model to %s", self.model_name, path)

    @classmethod
    def load(cls, path: Path) -> "_BaseEnsembleTree":
        with open(path, "rb") as f:
            data = pickle.load(f)
        instance = cls.__new__(cls)
        instance.pipeline = data["pipeline"]
        instance.model_name = data["model_name"]
        instance.feature_names = data["feature_names"]
        instance.feature_importances = data["feature_importances"]
        instance.is_fitted = data["is_fitted"]
        logger.info("Loaded %s model from %s", instance.model_name, path)
        return instance


# ──────────────────────────────────────────────────────────────────────────────
# Random Forest
# ──────────────────────────────────────────────────────────────────────────────


class RandomForestModel(_BaseEnsembleTree):
    """Random Forest Regressor with RobustScaler preprocessing.

    Uses bagging with decorrelated decision trees. Good for capturing
    nonlinear interactions without overfitting to individual features.

    Attributes:
        n_estimators: Number of trees in the forest.
        max_depth: Maximum depth of each tree.
    """

    model_name = "RandomForest"

    def __init__(
        self,
        n_estimators: int = 500,
        max_depth: Optional[int] = None,
        min_samples_leaf: int = 5,
        max_features: str = "sqrt",
        random_state: int = 42,
    ) -> None:
        super().__init__()
        regressor = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            max_features=max_features,
            random_state=random_state,
            n_jobs=-1,
        )
        self.pipeline = self._build_pipeline(regressor)
        logger.info("Initialized RandomForest (n_estimators=%d)", n_estimators)


# ──────────────────────────────────────────────────────────────────────────────
# Extra Trees
# ──────────────────────────────────────────────────────────────────────────────


class ExtraTreesModel(_BaseEnsembleTree):
    """Extremely Randomized Trees Regressor.

    Like Random Forest but with random split thresholds, leading to
    higher variance reduction and faster training.

    Attributes:
        n_estimators: Number of trees.
    """

    model_name = "ExtraTrees"

    def __init__(
        self,
        n_estimators: int = 500,
        max_depth: Optional[int] = None,
        min_samples_leaf: int = 5,
        random_state: int = 42,
    ) -> None:
        super().__init__()
        regressor = ExtraTreesRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
            n_jobs=-1,
        )
        self.pipeline = self._build_pipeline(regressor)
        logger.info("Initialized ExtraTrees (n_estimators=%d)", n_estimators)


# ──────────────────────────────────────────────────────────────────────────────
# Gradient Boosting (sklearn)
# ──────────────────────────────────────────────────────────────────────────────


class GradientBoostingModel(_BaseEnsembleTree):
    """Sklearn Gradient Boosting Regressor with Huber loss.

    Uses Huber loss for robustness against outliers in AQI data.
    Sequential boosting with shrinkage for controlled learning.

    Attributes:
        n_estimators: Number of boosting stages.
        learning_rate: Shrinkage factor per stage.
    """

    model_name = "GradientBoosting"

    def __init__(
        self,
        n_estimators: int = 500,
        learning_rate: float = 0.05,
        max_depth: int = 5,
        subsample: float = 0.8,
        min_samples_leaf: int = 10,
        random_state: int = 42,
    ) -> None:
        super().__init__()
        regressor = GradientBoostingRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            subsample=subsample,
            min_samples_leaf=min_samples_leaf,
            loss="huber",
            random_state=random_state,
        )
        self.pipeline = self._build_pipeline(regressor)
        logger.info(
            "Initialized GradientBoosting (n=%d, lr=%.3f)",
            n_estimators, learning_rate,
        )


# ──────────────────────────────────────────────────────────────────────────────
# SVR (Support Vector Regression)
# ──────────────────────────────────────────────────────────────────────────────


class SVRModel(_BaseEnsembleTree):
    """Support Vector Regression with RBF kernel.

    Effective for smaller datasets with complex nonlinear boundaries.
    Uses RobustScaler for outlier-tolerant preprocessing.

    Attributes:
        kernel: SVM kernel type ('rbf', 'linear', 'poly').
        C: Regularization parameter.
    """

    model_name = "SVR"

    def __init__(
        self,
        kernel: str = "rbf",
        C: float = 10.0,
        epsilon: float = 0.1,
        gamma: str = "scale",
    ) -> None:
        super().__init__()
        from sklearn.svm import SVR
        regressor = SVR(kernel=kernel, C=C, epsilon=epsilon, gamma=gamma)
        self.pipeline = self._build_pipeline(regressor)
        logger.info("Initialized SVR (kernel=%s, C=%.1f)", kernel, C)
