"""AWS SageMaker Model Registry operations.

Handles model versioning, metadata storage, and champion/challenger
model management using AWS SageMaker Model Registry.

Example:
    >>> from training_pipeline.registry import ModelRegistryManager
    >>> registry = ModelRegistryManager()
    >>> registry.register_model(model, metrics, params)
"""

from __future__ import annotations

import json
import logging
import pickle
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import get_settings, Settings
from training_pipeline.evaluation import EvaluationMetrics

logger = logging.getLogger(__name__)


class ModelRegistryManager:
    """Manages model lifecycle in AWS SageMaker Model Registry with local fallback.

    Handles model registration, versioning, metadata attachment,
    and champion/challenger comparison for automated model promotion.

    Attributes:
        settings: Application settings instance.
        _session: boto3 session.
        _sm_client: SageMaker client.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._session = None
        self._sm_client = None

    def _connect(self) -> None:
        """Establish AWS SageMaker connection."""
        if self._session is not None:
            return

        try:
            import boto3

            self._session = boto3.Session(region_name=self.settings.aws_region)
            self._sm_client = self._session.client("sagemaker")
            logger.info("Connected to AWS SageMaker Model Registry")

            # Ensure model package group exists
            self._ensure_model_package_group()
        except (ImportError, Exception) as e:
            logger.warning("AWS SageMaker unavailable: %s — using local registry", e)
            self._session = None
            self._sm_client = None

    def _ensure_model_package_group(self) -> None:
        """Create model package group if it doesn't exist."""
        group_name = self.settings.model_registry_name
        try:
            self._sm_client.describe_model_package_group(
                ModelPackageGroupName=group_name
            )
            logger.info("Model package group '%s' exists", group_name)
        except self._sm_client.exceptions.ClientError:
            try:
                self._sm_client.create_model_package_group(
                    ModelPackageGroupName=group_name,
                    ModelPackageGroupDescription="Sargodha AQI forecast model registry",
                )
                logger.info("Created model package group: %s", group_name)
            except Exception as e:
                logger.warning("Failed to create model package group: %s", e)

    def register_model(
        self,
        model: Any,
        metrics: EvaluationMetrics,
        params: Dict[str, Any],
        explainer: Any = None,
        model_type: str = "unknown",
    ) -> str:
        """Register a trained model in the registry.

        Saves model artifacts, evaluation metrics, and hyperparameters.
        Creates a versioned directory structure for local storage.

        Args:
            model: Trained model object.
            metrics: Evaluation metrics for the model.
            params: Model hyperparameters.
            explainer: Optional SHAP explainer to serialize with model.
            model_type: Model architecture identifier.

        Returns:
            str: Version identifier of the registered model.
        """
        self._connect()

        version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        model_name = self.settings.model_registry_name

        # ── Prepare model artifacts ──
        artifacts_dir = self.settings.models_dir / model_name / version
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Save model
        model_path = artifacts_dir / "model.pkl"
        if hasattr(model, "save"):
            model.save(model_path)
        else:
            with open(model_path, "wb") as f:
                pickle.dump(model, f)

        # Save metrics
        metrics_path = artifacts_dir / "metrics.json"
        metrics_path.write_text(json.dumps(metrics.to_dict(), indent=2))

        # Save hyperparameters
        params_path = artifacts_dir / "params.json"
        # Filter non-serializable params
        serializable_params = {}
        for k, v in params.items():
            try:
                json.dumps(v)
                serializable_params[k] = v
            except (TypeError, ValueError):
                serializable_params[k] = str(v)
        params_path.write_text(json.dumps(serializable_params, indent=2))

        # Save explainer if provided
        if explainer is not None:
            explainer_path = artifacts_dir / "explainer.pkl"
            if hasattr(explainer, "save"):
                explainer.save(explainer_path)
            else:
                with open(explainer_path, "wb") as f:
                    pickle.dump(explainer, f)

        # Save model metadata
        metadata = {
            "model_name": model_name,
            "model_type": model_type,
            "version": version,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics.to_dict(),
            "has_explainer": explainer is not None,
        }
        metadata_path = artifacts_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2))

        # ── Try SageMaker registration ──
        if self._sm_client is not None:
            try:
                # Upload artifacts to S3
                s3_client = self._session.client("s3")
                bucket = self.settings.s3_feature_store_bucket
                s3_prefix = f"models/{model_name}/{version}/"

                for file_path in artifacts_dir.iterdir():
                    if file_path.is_file():
                        s3_key = s3_prefix + file_path.name
                        s3_client.upload_file(
                            str(file_path), bucket, s3_key
                        )

                # Create model package
                model_package_input = {
                    "ModelPackageGroupName": model_name,
                    "ModelPackageDescription": f"{model_type} model for Sargodha AQI prediction",
                    "InferenceSpecification": {
                        "Containers": [{
                            "Image": "763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-inference:2.0-cpu-py310",
                            "ModelDataUrl": f"s3://{bucket}/{s3_prefix}model.pkl",
                        }],
                        "SupportedContentTypes": ["application/json"],
                        "SupportedResponseMIMETypes": ["application/json"],
                    },
                    "ModelApprovalStatus": "Approved",
                    "CustomerMetadataProperties": {
                        "rmse": str(metrics.rmse),
                        "r2": str(metrics.r2),
                        "mae": str(metrics.mae),
                        "model_type": model_type,
                        "version": version,
                    },
                }

                response = self._sm_client.create_model_package(**model_package_input)
                sm_version = response.get("ModelPackageArn", version)
                logger.info(
                    "Registered model in SageMaker: %s (ARN: %s)",
                    model_name, sm_version,
                )
                return version
            except Exception as e:
                logger.warning("SageMaker registration failed: %s", e)

        logger.info(
            "Registered model locally: %s/%s (RMSE=%.4f, R2=%.4f)",
            model_name, version, metrics.rmse, metrics.r2,
        )
        return version

    def get_champion(self) -> Optional[Dict[str, Any]]:
        """Get the current champion model metadata.

        The champion is the model with the lowest RMSE.

        Returns:
            Optional[Dict]: Champion model metadata, or None.
        """
        self._connect()

        model_dir = self.settings.models_dir / self.settings.model_registry_name

        if not model_dir.exists():
            logger.info("No models registered yet")
            return None

        # Find all versions and their metrics
        best_version = None
        best_rmse = float("inf")
        best_metadata = None

        for version_dir in sorted(model_dir.iterdir()):
            if not version_dir.is_dir():
                continue

            metrics_file = version_dir / "metrics.json"
            metadata_file = version_dir / "metadata.json"

            if metrics_file.exists():
                metrics = json.loads(metrics_file.read_text())
                rmse = metrics.get("rmse", float("inf"))

                if rmse < best_rmse:
                    best_rmse = rmse
                    best_version = version_dir.name

                    if metadata_file.exists():
                        best_metadata = json.loads(metadata_file.read_text())
                    else:
                        best_metadata = {"version": best_version, "metrics": metrics}

        if best_metadata:
            best_metadata["artifacts_dir"] = str(model_dir / best_version)
            logger.info(
                "Champion model: %s (RMSE=%.4f)",
                best_version, best_rmse,
            )

        return best_metadata

    def load_champion_model(self) -> Optional[Any]:
        """Load the current champion model from the registry.

        Returns:
            The loaded model object, or None if no champion exists.
        """
        champion = self.get_champion()
        if champion is None:
            return None

        model_path = Path(champion["artifacts_dir"]) / "model.pkl"
        if not model_path.exists():
            logger.error("Champion model file not found: %s", model_path)
            return None

        with open(model_path, "rb") as f:
            model = pickle.load(f)

        logger.info("Loaded champion model from %s", model_path)
        return model

    def should_promote_challenger(
        self,
        challenger_metrics: EvaluationMetrics,
        improvement_threshold: float = 0.01,
    ) -> bool:
        """Determine if a challenger model should replace the champion.

        Args:
            challenger_metrics: Metrics of the candidate model.
            improvement_threshold: Minimum RMSE improvement required.

        Returns:
            bool: True if the challenger should be promoted.
        """
        champion = self.get_champion()

        if champion is None:
            logger.info("No existing champion — challenger auto-promoted")
            return True

        champion_rmse = champion.get("metrics", {}).get("rmse", float("inf"))
        challenger_rmse = challenger_metrics.rmse

        improvement = (champion_rmse - challenger_rmse) / champion_rmse

        if improvement >= improvement_threshold:
            logger.info(
                "Challenger promoted: RMSE improved by %.2f%% (%.4f -> %.4f)",
                improvement * 100, champion_rmse, challenger_rmse,
            )
            return True
        else:
            logger.info(
                "Challenger NOT promoted: improvement %.2f%% < %.2f%% threshold",
                improvement * 100, improvement_threshold * 100,
            )
            return False
