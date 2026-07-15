"""FastAPI dependency injection for model loading and feature store access.

Provides cached singleton dependencies for the prediction service
including model loading, feature store connection, and SHAP explainer.
"""

from __future__ import annotations

import logging
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import get_settings, Settings

logger = logging.getLogger(__name__)

# Global state for service uptime tracking
_start_time = time.time()


class ModelService:
    """Singleton service for model loading and prediction.

    Caches the loaded model and explainer to avoid repeated disk I/O.

    Attributes:
        model: Loaded champion model.
        explainer: SHAP explainer instance.
        model_metadata: Model registry metadata.
    """

    def __init__(self) -> None:
        self.model: Any = None
        self.explainer: Any = None
        self.model_metadata: Dict[str, Any] = {}
        self._loaded = False

    def load(self) -> None:
        """Load the champion model and explainer from registry."""
        if self._loaded:
            return

        settings = get_settings()

        try:
            from training_pipeline.registry import ModelRegistryManager

            registry = ModelRegistryManager(settings)
            champion = registry.get_champion()

            if champion:
                self.model_metadata = champion
                artifacts_dir = Path(champion["artifacts_dir"])

                # Load model
                import pickle
                import torch
                model_path = artifacts_dir / "model.pkl"
                if model_path.exists():
                    try:
                        with open(model_path, "rb") as f:
                            data = pickle.load(f)
                    except Exception:
                        data = torch.load(model_path, map_location="cpu", weights_only=False)
                        
                    if "pipeline" in data:
                        from training_pipeline.models.baseline import BaselineRegressor
                        self.model = BaselineRegressor.load(model_path)
                    elif "model_state" in data:
                        from training_pipeline.models.deep_learning import BiLSTMRegressor
                        self.model = BiLSTMRegressor.load(model_path)
                    else:
                        from training_pipeline.models.tree_ensemble import TreeEnsembleRegressor
                        self.model = TreeEnsembleRegressor.load(model_path)
                        
                    logger.info("Loaded champion model from %s", model_path)

                # Load explainer
                explainer_path = artifacts_dir / "explainer.pkl"
                if explainer_path.exists():
                    with open(explainer_path, "rb") as f:
                        self.explainer = pickle.load(f)
                    logger.info("Loaded SHAP explainer from %s", explainer_path)

                self._loaded = True
            else:
                logger.warning("No champion model found in registry")
        except Exception as e:
            logger.error("Failed to load model: %s", e)

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded and ready for inference."""
        return self._loaded and self.model is not None


class FeatureService:
    """Singleton service for feature store access.

    Provides cached access to the feature store for fetching
    latest features during inference.
    """

    def __init__(self) -> None:
        self._manager = None
        self._connected = False

    def connect(self) -> None:
        """Establish feature store connection."""
        if self._connected:
            return

        try:
            from feature_pipeline.register import FeatureStoreManager

            self._manager = FeatureStoreManager()
            self._connected = True
            logger.info("Feature store service connected")
        except Exception as e:
            logger.error("Feature store connection failed: %s", e)

    def get_latest_features(self, n_hours: int = 72) -> Any:
        """Fetch the most recent features for inference.

        Args:
            n_hours: Number of recent hours to fetch.

        Returns:
            DataFrame of recent features.
        """
        self.connect()
        if self._manager:
            return self._manager.get_latest_features(n_hours)
        return None

    @property
    def is_connected(self) -> bool:
        """Check if feature store is connected."""
        return self._connected


# ── Singleton instances ──────────────────────────────────────────────────────

_model_service: Optional[ModelService] = None
_feature_service: Optional[FeatureService] = None


def get_model_service() -> ModelService:
    """Get or create the singleton ModelService.

    Returns:
        ModelService: Cached model service instance.
    """
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
        _model_service.load()
    return _model_service


def get_feature_service() -> FeatureService:
    """Get or create the singleton FeatureService.

    Returns:
        FeatureService: Cached feature service instance.
    """
    global _feature_service
    if _feature_service is None:
        _feature_service = FeatureService()
        _feature_service.connect()
    return _feature_service


def get_uptime_seconds() -> float:
    """Get service uptime in seconds."""
    return time.time() - _start_time
