"""ClearML Model Registry integration.

Handles uploading trained models to ClearML, tracking their metadata,
managing versions, and pulling models for inference.
"""

from __future__ import annotations

import logging
import os
import shutil
import pickle
import torch
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from config.settings import get_settings, Settings
from training_pipeline.evaluation import EvaluationMetrics

logger = logging.getLogger(__name__)

class ModelRegistryManager:
    """Manages model artifacts using ClearML."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    def should_promote_challenger(self, metrics: EvaluationMetrics) -> bool:
        """Determine if the new model is better than the current champion.
        
        For simplicity in this pipeline, we assume True, but in production
        this would query ClearML to compare R2 scores.
        """
        return True

    def register_model(
        self,
        model: Any,
        metrics: EvaluationMetrics,
        params: Dict[str, Any],
        explainer: Optional[Any] = None,
        model_type: str = "bilstm_attention",
    ) -> str:
        """Upload model artifact and explainer to ClearML.

        Args:
            model: Trained model object.
            metrics: Evaluation metrics.
            params: Model parameters.
            explainer: Optional SHAP explainer.
            model_type: String identifier.

        Returns:
            Version string (ClearML Task ID).
        """
        try:
            from clearml import Task
            
            task = Task.current_task()
            if not task:
                task = Task.init(
                    project_name=self.settings.clearml_project_name,
                    task_name=f"Model Upload - {model_type}"
                )
            
            # Log metrics
            metrics_dict = metrics.to_dict()
            for k, v in metrics_dict.items():
                if isinstance(v, (int, float)):
                    task.get_logger().report_scalar("Evaluation", k, iteration=0, value=v)
            
            # Save artifacts locally first
            export_dir = self.settings.models_dir / f"export_{model_type}"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Model specific saving
            is_pytorch = hasattr(model, "model_state_dict") or "lstm" in model_type.lower()
            model_ext = ".pt" if is_pytorch else ".pkl"
            model_path = export_dir / f"model{model_ext}"
            
            if is_pytorch:
                # Save PyTorch using custom save method if available, else torch.save
                if hasattr(model, "save"):
                    model.save(export_dir)
                    if not model_path.exists():
                        # If save method used a different name, copy it
                        for p in export_dir.glob("*.pt"):
                            shutil.copy(p, model_path)
                else:
                    torch.save(model.state_dict(), model_path)
            else:
                if hasattr(model, "save"):
                    model.save(export_dir)
                    if not model_path.exists():
                        for p in export_dir.glob("*.pkl"):
                            if "explainer" not in p.name:
                                shutil.copy(p, model_path)
                else:
                    with open(model_path, "wb") as f:
                        pickle.dump(model, f)
            
            # Explainer saving
            if explainer:
                explainer_path = export_dir / "explainer.pkl"
                with open(explainer_path, "wb") as f:
                    pickle.dump(explainer, f)
            
            # Upload directory to ClearML
            # Using artifacts feature instead of Model Registry for easier multi-file handling
            task.upload_artifact(
                name=f"{self.settings.model_registry_name}-{model_type}",
                artifact_object=str(export_dir)
            )
            
            task.set_tags([model_type, "champion"])
            
            logger.info("Registered model %s in ClearML", model_type)
            return task.id
        except ImportError:
            logger.error("ClearML package not installed.")
            return "local"
        except Exception as e:
            logger.error("Failed to register model in ClearML: %s", e)
            return "local"

    def get_champion_model(self, model_id: str = "bilstm_attention") -> Optional[Tuple[Path, Dict[str, Any]]]:
        """Download the champion model artifacts from ClearML.

        Args:
            model_id: The model identifier to retrieve.

        Returns:
            Tuple of (Local Path to downloaded model file, Model Metadata Dict).
        """
        try:
            from clearml import Task
            
            target_name = f"{self.settings.model_registry_name}-{model_id}"
            
            # Find task with champion tag
            tasks = Task.get_tasks(
                project_name=self.settings.clearml_project_name,
                tags=["champion", model_id]
            )
            
            if not tasks:
                tasks = Task.get_tasks(
                    project_name=self.settings.clearml_project_name,
                    tags=[model_id]
                )
            
            if not tasks:
                logger.warning("No model artifacts found in ClearML for %s", target_name)
                return None
                
            best_task = tasks[0]
            
            # Get artifact
            if target_name in best_task.artifacts:
                local_path = best_task.artifacts[target_name].get_local_copy()
            else:
                logger.warning("Artifact %s not found in Task", target_name)
                return None
                
            if not local_path:
                logger.warning("Failed to download local copy of the model from ClearML.")
                return None
                
            download_dir = Path(local_path)
            
            # Find model file inside directory
            is_pytorch = "lstm" in model_id.lower()
            model_ext = ".pt" if is_pytorch else ".pkl"
            
            # Look for model.pt / model.pkl directly
            model_file = download_dir / f"model{model_ext}"
            
            # If not there, look for any .pt or .pkl
            if not model_file.exists():
                candidates = list(download_dir.glob(f"*{model_ext}"))
                if candidates:
                    model_file = candidates[0]
                else:
                    logger.warning("No model file found in %s", download_dir)
                    return None

            logger.info("Downloaded champion model to %s", model_file)

            metadata = {"id": model_id, "clearml_task_id": best_task.id}
            return model_file, metadata
        except ImportError:
            logger.error("ClearML package not installed.")
            return None
        except Exception as e:
            logger.error("Failed to retrieve champion model from ClearML: %s", e)
            return None
