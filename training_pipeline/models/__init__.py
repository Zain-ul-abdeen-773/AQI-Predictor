"""Model implementations for the AQI prediction pipeline.

Exports all model classes for easy import:
- BaselineRegressor (Ridge, ElasticNet)
- LightGBMOptimized (LightGBM + Optuna)
- XGBoostOptimized (XGBoost + Optuna)
- RandomForestModel, ExtraTreesModel, GradientBoostingModel, SVRModel
- BiLSTMAttention (Bi-LSTM + Multi-Head Attention)
"""

from training_pipeline.models.baseline import BaselineRegressor
from training_pipeline.models.tree_ensemble import LightGBMOptimized
from training_pipeline.models.deep_learning import BiLSTMAttention
from training_pipeline.models.ensemble_trees import (
    ExtraTreesModel,
    GradientBoostingModel,
    RandomForestModel,
    SVRModel,
)

# Conditionally import XGBoost (requires xgboost package)
try:
    from training_pipeline.models.xgboost_model import XGBoostOptimized
except ImportError:
    XGBoostOptimized = None  # type: ignore

__all__ = [
    "BaselineRegressor",
    "LightGBMOptimized",
    "XGBoostOptimized",
    "RandomForestModel",
    "ExtraTreesModel",
    "GradientBoostingModel",
    "SVRModel",
    "BiLSTMAttention",
]
