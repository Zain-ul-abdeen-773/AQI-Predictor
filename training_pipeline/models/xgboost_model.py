"""XGBoost regression model with Optuna hyperparameter optimization.

Provides an XGBoost regressor with Bayesian hyperparameter tuning
using Optuna, TimeSeriesSplit cross-validation, and early stopping.

Example:
    >>> from training_pipeline.models.xgboost_model import XGBoostOptimized
    >>> model = XGBoostOptimized(n_trials=50)
    >>> model.fit(X_train, y_train, feature_names=feature_names)
    >>> predictions = model.predict(X_test)
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.model_selection import TimeSeriesSplit

logger = logging.getLogger(__name__)


class XGBoostOptimized:
    """XGBoost Regressor with Optuna Bayesian hyperparameter tuning.

    Uses TimeSeriesSplit cross-validation within the Optuna objective
    for more robust hyperparameter selection on temporal data.

    Attributes:
        n_trials: Number of Optuna optimization trials.
        best_params: Best hyperparameters found.
        model: Trained XGBoost model.
        is_fitted: Whether the model has been trained.
        feature_names: Feature names used during training.
        feature_importances: Feature importance scores.
    """

    def __init__(
        self,
        n_trials: int = 50,
        cv_splits: int = 3,
        random_state: int = 42,
    ) -> None:
        """Initialize XGBoost with Optuna optimization.

        Args:
            n_trials: Number of Bayesian optimization trials.
            cv_splits: Number of TimeSeriesSplit folds.
            random_state: Random seed for reproducibility.
        """
        self.n_trials = n_trials
        self.cv_splits = cv_splits
        self.random_state = random_state
        self.best_params: Dict[str, Any] = {}
        self.model = None
        self.is_fitted = False
        self.feature_names: List[str] = []
        self.feature_importances: Dict[str, float] = {}

        logger.info("Initialized XGBoost with %d Optuna trials", self.n_trials)

    def _create_objective(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
    ):
        """Create Optuna objective with TimeSeriesSplit CV."""
        import xgboost as xgb

        tscv = TimeSeriesSplit(n_splits=self.cv_splits)

        def objective(trial) -> float:
            params = {
                "objective": "reg:squarederror",
                "eval_metric": "rmse",
                "tree_method": "hist",
                "random_state": self.random_state,
                "n_jobs": -1,
                "verbosity": 0,
                "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.3, log=True),
                "n_estimators": trial.suggest_int("n_estimators", 100, 1500),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
                "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
                "gamma": trial.suggest_float("gamma", 0.0, 5.0),
            }

            cv_scores = []
            for train_idx, val_idx in tscv.split(X_train):
                X_tr, X_va = X_train[train_idx], X_train[val_idx]
                y_tr, y_va = y_train[train_idx], y_train[val_idx]

                model = xgb.XGBRegressor(**params)
                model.fit(
                    X_tr, y_tr,
                    eval_set=[(X_va, y_va)],
                    verbose=False,
                )
                y_pred = model.predict(X_va)
                rmse = np.sqrt(np.mean((y_va - y_pred) ** 2))
                cv_scores.append(rmse)

            return np.mean(cv_scores)

        return objective

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None,
    ) -> "XGBoostOptimized":
        """Train with Bayesian hyperparameter optimization.

        Args:
            X_train: Training feature matrix.
            y_train: Training target values.
            X_val: Validation features (optional).
            y_val: Validation targets (optional).
            feature_names: Feature name list.

        Returns:
            Self for method chaining.
        """
        import xgboost as xgb
        import optuna

        optuna.logging.set_verbosity(optuna.logging.WARNING)
        self.feature_names = feature_names or [f"f{i}" for i in range(X_train.shape[1])]

        if X_val is None or y_val is None:
            split_idx = int(0.8 * len(X_train))
            X_val = X_train[split_idx:]
            y_val = y_train[split_idx:]
            X_train = X_train[:split_idx]
            y_train = y_train[:split_idx]

        logger.info(
            "Starting XGBoost Optuna: %d trials, train=%d, val=%d",
            self.n_trials, len(X_train), len(X_val),
        )

        study = optuna.create_study(
            direction="minimize",
            study_name="xgboost_aqi",
            sampler=optuna.samplers.TPESampler(seed=self.random_state),
        )
        objective = self._create_objective(X_train, y_train)
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=False)

        self.best_params = study.best_params
        logger.info("XGBoost best RMSE: %.4f", study.best_value)

        # Train final model
        final_params = {
            "objective": "reg:squarederror",
            "eval_metric": "rmse",
            "tree_method": "hist",
            "random_state": self.random_state,
            "n_jobs": -1,
            "verbosity": 0,
            **self.best_params,
        }

        self.model = xgb.XGBRegressor(**final_params)
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        importances = self.model.feature_importances_
        self.feature_importances = {
            name: float(imp)
            for name, imp in sorted(
                zip(self.feature_names, importances),
                key=lambda x: -x[1],
            )
        }

        self.is_fitted = True
        logger.info("XGBoost trained. Top 5 features: %s", list(self.feature_importances.keys())[:5])
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Model must be fitted before prediction")
        return np.clip(self.model.predict(X), 0, 500)

    def get_params(self) -> Dict[str, Any]:
        return {"model_type": "xgboost", "n_trials": self.n_trials, "best_params": self.best_params}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "model": self.model, "best_params": self.best_params,
                "feature_names": self.feature_names,
                "feature_importances": self.feature_importances,
                "is_fitted": self.is_fitted,
            }, f)
        logger.info("Saved XGBoost model to %s", path)

    @classmethod
    def load(cls, path: Path) -> "XGBoostOptimized":
        with open(path, "rb") as f:
            data = pickle.load(f)
        instance = cls()
        instance.model = data["model"]
        instance.best_params = data["best_params"]
        instance.feature_names = data["feature_names"]
        instance.feature_importances = data["feature_importances"]
        instance.is_fitted = data["is_fitted"]
        logger.info("Loaded XGBoost model from %s", path)
        return instance
