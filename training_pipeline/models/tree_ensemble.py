"""LightGBM tree ensemble with Bayesian hyperparameter optimization.

Implements a LightGBM Regressor with Optuna-based Bayesian optimization
for finding optimal hyperparameters. Designed for tabular AQI prediction
with strong handling of feature interactions and nonlinear relationships.

Example:
    >>> from training_pipeline.models.tree_ensemble import LightGBMOptimized
    >>> model = LightGBMOptimized()
    >>> model.fit(X_train, y_train, X_val, y_val)
    >>> predictions = model.predict(X_test)
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from config.settings import get_settings

logger = logging.getLogger(__name__)


class LightGBMOptimized:
    """LightGBM Regressor with Optuna Bayesian hyperparameter tuning.

    Performs automated hyperparameter search over key LightGBM parameters
    including learning rate, max depth, number of leaves, and regularization
    terms. Uses early stopping to prevent overfitting.

    Attributes:
        n_trials: Number of Optuna optimization trials.
        best_params: Best hyperparameters found during optimization.
        model: Trained LightGBM model.
        is_fitted: Whether the model has been trained.
        feature_names: Feature names used during training.
        feature_importances: Feature importance scores.
    """

    def __init__(
        self,
        n_trials: Optional[int] = None,
        random_state: int = 42,
    ) -> None:
        """Initialize the LightGBM model with Optuna optimization.

        Args:
            n_trials: Number of Bayesian optimization trials.
            random_state: Random seed for reproducibility.
        """
        settings = get_settings()
        self.n_trials = n_trials or settings.optuna_n_trials
        self.random_state = random_state
        self.best_params: Dict[str, Any] = {}
        self.model = None
        self.is_fitted = False
        self.feature_names: List[str] = []
        self.feature_importances: Dict[str, float] = {}

        logger.info("Initialized LightGBM with %d Optuna trials", self.n_trials)

    def _create_objective(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
    ):
        """Create an Optuna objective function for hyperparameter search.

        Args:
            X_train: Training features.
            y_train: Training targets.
            X_val: Validation features.
            y_val: Validation targets.

        Returns:
            Callable: Optuna objective function.
        """
        import lightgbm as lgb

        def objective(trial) -> float:
            params = {
                "objective": "regression",
                "metric": "rmse",
                "boosting_type": "gbdt",
                "verbosity": -1,
                "random_state": self.random_state,
                "n_jobs": -1,

                # Tunable hyperparameters (Anti-Overfitting Regularization Bounds Enforced)
                "learning_rate": trial.suggest_float("learning_rate", 0.008, 0.15, log=True),
                "n_estimators": trial.suggest_int("n_estimators", 150, 1200),
                "max_depth": trial.suggest_int("max_depth", 3, 9),
                "num_leaves": trial.suggest_int("num_leaves", 16, 128),
                "min_child_samples": trial.suggest_int("min_child_samples", 20, 120),
                "subsample": trial.suggest_float("subsample", 0.6, 0.9),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 0.85),
                "reg_alpha": trial.suggest_float("reg_alpha", 0.05, 15.0, log=True),
                "reg_lambda": trial.suggest_float("reg_lambda", 0.05, 15.0, log=True),
                "min_split_gain": trial.suggest_float("min_split_gain", 0.01, 1.5),
            }

            model = lgb.LGBMRegressor(**params)

            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                callbacks=[
                    lgb.early_stopping(stopping_rounds=50, verbose=False),
                    lgb.log_evaluation(period=0),
                ],
            )

            y_pred = model.predict(X_val)
            rmse = np.sqrt(np.mean((y_val - y_pred) ** 2))
            return rmse

        return objective

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None,
    ) -> "LightGBMOptimized":
        """Train with Bayesian hyperparameter optimization.

        If validation data is not provided, uses a 80/20 split from
        the training data.

        Args:
            X_train: Training feature matrix.
            y_train: Training target values.
            X_val: Validation features (optional).
            y_val: Validation targets (optional).
            feature_names: Feature name list (optional).

        Returns:
            Self for method chaining.
        """
        import lightgbm as lgb
        import optuna

        # Suppress Optuna logs during trials
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        self.feature_names = feature_names or [f"f{i}" for i in range(X_train.shape[1])]

        # Create validation split if not provided
        if X_val is None or y_val is None:
            split_idx = int(0.8 * len(X_train))
            X_val = X_train[split_idx:]
            y_val = y_train[split_idx:]
            X_train = X_train[:split_idx]
            y_train = y_train[:split_idx]

        logger.info(
            "Starting Optuna optimization: %d trials, train=%d, val=%d",
            self.n_trials, len(X_train), len(X_val),
        )

        # ── Bayesian Optimization ──
        study = optuna.create_study(
            direction="minimize",
            study_name="lightgbm_aqi",
            sampler=optuna.samplers.TPESampler(seed=self.random_state),
        )

        objective = self._create_objective(X_train, y_train, X_val, y_val)
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=True)

        self.best_params = study.best_params
        logger.info(
            "Optuna optimization complete. Best RMSE: %.4f",
            study.best_value,
        )
        logger.info("Best parameters: %s", json.dumps(self.best_params, indent=2))

        # ── Train final model with best params ──
        final_params = {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "verbosity": -1,
            "random_state": self.random_state,
            "n_jobs": -1,
            **self.best_params,
        }

        self.model = lgb.LGBMRegressor(**final_params)
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[
                lgb.early_stopping(stopping_rounds=50, verbose=False),
                lgb.log_evaluation(period=100),
            ],
        )

        # ── Extract feature importances ──
        importances = self.model.feature_importances_
        self.feature_importances = {
            name: float(imp)
            for name, imp in sorted(
                zip(self.feature_names, importances),
                key=lambda x: -x[1],
            )
        }

        self.is_fitted = True
        logger.info(
            "LightGBM trained. Top 5 features: %s",
            list(self.feature_importances.keys())[:5],
        )
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate AQI predictions.

        Args:
            X: Feature matrix (n_samples, n_features).

        Returns:
            np.ndarray: Predicted AQI values clipped to [0, 500].

        Raises:
            RuntimeError: If model is not fitted.
        """
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Model must be fitted before prediction")

        predictions = self.model.predict(X)
        return np.clip(predictions, 0, 500)

    def get_params(self) -> Dict[str, Any]:
        """Get the best hyperparameters found during optimization.

        Returns:
            Dict of optimized hyperparameters.
        """
        return {
            "model_type": "lightgbm",
            "n_trials": self.n_trials,
            "best_params": self.best_params,
        }

    def get_feature_importance(self, top_k: int = 20) -> Dict[str, float]:
        """Get top-K feature importance scores.

        Args:
            top_k: Number of top features to return.

        Returns:
            Dict mapping feature names to importance scores.
        """
        items = list(self.feature_importances.items())[:top_k]
        return dict(items)

    def save(self, path: Path) -> None:
        """Save trained model and metadata to disk.

        Args:
            path: File path to save the model (.pkl).
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "model": self.model,
                "best_params": self.best_params,
                "feature_names": self.feature_names,
                "feature_importances": self.feature_importances,
                "is_fitted": self.is_fitted,
            }, f)
        logger.info("Saved LightGBM model to %s", path)

    @classmethod
    def load(cls, path: Path) -> "LightGBMOptimized":
        """Load a trained model from disk.

        Args:
            path: Path to the saved model file.

        Returns:
            LightGBMOptimized: Loaded model instance.
        """
        with open(path, "rb") as f:
            data = pickle.load(f)

        instance = cls()
        instance.model = data["model"]
        instance.best_params = data["best_params"]
        instance.feature_names = data["feature_names"]
        instance.feature_importances = data["feature_importances"]
        instance.is_fitted = data["is_fitted"]
        logger.info("Loaded LightGBM model from %s", path)
        return instance
