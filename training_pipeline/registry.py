"""Model Registry – ClearML + local manifest.

Handles uploading trained models to ClearML, tracking their metadata,
managing versions, and pulling models for inference.  Now supports
registering **all** trained models (not just the champion) so the API
can offer a full model‑zoo selection to end‑users.
"""

from __future__ import annotations

import json
import logging
import pickle
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.settings import Settings, get_settings
from training_pipeline.evaluation import EvaluationMetrics

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Local manifest helpers
# ---------------------------------------------------------------------------
MANIFEST_FILENAME = "model_registry.json"


def _load_manifest(models_dir: Path) -> dict[str, Any]:
    """Load or initialise the local model registry manifest."""
    manifest_path = models_dir / MANIFEST_FILENAME
    if manifest_path.exists():
        return json.loads(manifest_path.read_text())
    return {"models": {}, "champion": None, "updated_at": None}


def _save_manifest(models_dir: Path, manifest: dict[str, Any]) -> None:
    manifest_path = models_dir / MANIFEST_FILENAME
    manifest["updated_at"] = datetime.now(UTC).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str))
    logger.info("Saved model registry manifest to %s", manifest_path)


# ---------------------------------------------------------------------------
# Registry Manager
# ---------------------------------------------------------------------------
class ModelRegistryManager:
    """Manages model artifacts using ClearML + local manifest."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    # ------------------------------------------------------------------
    # Champion promotion heuristic
    # ------------------------------------------------------------------
    def should_promote_challenger(self, metrics: EvaluationMetrics) -> bool:
        """Determine if the new model is better than the current champion.

        Compares the challenger's RMSE against the current champion from
        the local manifest. Promotes if RMSE improves by at least 1%.
        """
        manifest = _load_manifest(self.settings.models_dir)
        champion_id = manifest.get("champion")
        if not champion_id:
            return True  # No existing champion, always promote

        champion_entry = manifest.get("models", {}).get(champion_id)
        if not champion_entry:
            return True

        current_rmse = champion_entry.get("metrics", {}).get("rmse", float("inf"))
        improvement_threshold = 0.99  # Require at least 1% RMSE improvement
        return metrics.rmse < current_rmse * improvement_threshold

    # ------------------------------------------------------------------
    # Single‑model registration (kept for backward compat)
    # ------------------------------------------------------------------
    def register_model(
        self,
        model: Any,
        metrics: EvaluationMetrics,
        params: dict[str, Any],
        explainer: Any | None = None,
        model_type: str = "bilstm_attention",
    ) -> str:
        """Upload a single model artifact and explainer to ClearML.

        Returns:
            Version string (ClearML Task ID or 'local').
        """
        # Save locally first
        export_dir = self._save_model_locally(model, model_type, metrics, params, explainer)

        # Upload to ClearML
        clearml_id = self._upload_to_clearml(export_dir, model_type, metrics)
        return clearml_id

    # ------------------------------------------------------------------
    # Multi‑model registration (NEW)
    # ------------------------------------------------------------------
    def register_all_models(
        self,
        trained_models: dict[str, Any],
        results: dict[str, EvaluationMetrics],
        champion_name: str | None = None,
        explainer: Any | None = None,
    ) -> dict[str, str]:
        """Register every trained model in the registry.

        Each model is saved locally under ``models/<model_id>/`` and
        uploaded to ClearML as an individual artifact.  A JSON manifest
        (``models/model_registry.json``) is written so the API can
        discover models without ClearML at startup.

        Args:
            trained_models: Mapping of ``model_name → trained_model_object``.
            results: Mapping of ``model_name → EvaluationMetrics``.
            champion_name: Name of the champion model.
            explainer: Optional SHAP explainer (saved with champion only).

        Returns:
            Dict mapping model_name → version string.
        """
        versions: dict[str, str] = {}
        manifest = _load_manifest(self.settings.models_dir)

        for name, model_obj in trained_models.items():
            model_id = self._normalize_id(name)
            metrics = results.get(name)
            if metrics is None:
                continue

            params = model_obj.get_params() if hasattr(model_obj, "get_params") else {}

            # Attach explainer only to champion
            expl = explainer if (name == champion_name) else None

            export_dir = self._save_model_locally(model_obj, model_id, metrics, params, expl)
            clearml_id = self._upload_to_clearml(
                export_dir, model_id, metrics, is_champion=(name == champion_name)
            )
            versions[name] = clearml_id

            # Update manifest entry
            manifest["models"][model_id] = {
                "id": model_id,
                "name": name,
                "path": str(export_dir),
                "metrics": metrics.to_dict(),
                "params": {k: str(v) for k, v in params.items()},
                "clearml_id": clearml_id,
                "is_champion": (name == champion_name),
                "registered_at": datetime.now(UTC).isoformat(),
            }

        manifest["champion"] = self._normalize_id(champion_name) if champion_name else None
        _save_manifest(self.settings.models_dir, manifest)

        logger.info(
            "Registered %d models – champion: %s",
            len(versions),
            champion_name,
        )
        return versions

    # ------------------------------------------------------------------
    # Retrieval helpers
    # ------------------------------------------------------------------
    def list_registered_models(self) -> list[dict[str, Any]]:
        """Return metadata for every registered model from the local manifest."""
        manifest = _load_manifest(self.settings.models_dir)
        return list(manifest.get("models", {}).values())

    def get_model_by_id(self, model_id: str) -> tuple[Path, dict[str, Any]] | None:
        """Load a specific model from disk by its ID.

        Returns:
            Tuple of (path_to_model_file, metadata_dict) or None.
        """
        manifest = _load_manifest(self.settings.models_dir)
        entry = manifest.get("models", {}).get(model_id)
        if entry is None:
            logger.warning("Model %s not found in manifest", model_id)
            return None

        export_dir = Path(entry["path"])
        model_file = self._find_model_file(export_dir, model_id)
        if model_file is None:
            return None

        return model_file, entry

    def get_champion_model(
        self, model_id: str = "bilstm_attention"
    ) -> tuple[Path, dict[str, Any]] | None:
        """Download the champion model artifacts.

        Tries local manifest first, then ClearML.
        """
        # Try manifest‑based lookup
        manifest = _load_manifest(self.settings.models_dir)
        champion_id = manifest.get("champion")

        # If a specific model_id was requested, use that
        if model_id != "bilstm_attention":
            champion_id = model_id

        if champion_id and champion_id in manifest.get("models", {}):
            result = self.get_model_by_id(champion_id)
            if result is not None:
                return result

        # Fallback: ClearML lookup (original behaviour)
        return self._get_from_clearml(model_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_id(name: str) -> str:
        """Convert a display name like 'GradientBoosting' → 'gradient_boosting'."""
        if name is None:
            return "unknown"
        # Insert underscore before uppercase letters, then lowercase
        import re

        s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _save_model_locally(
        self,
        model: Any,
        model_id: str,
        metrics: EvaluationMetrics,
        params: dict[str, Any],
        explainer: Any | None = None,
    ) -> Path:
        """Persist model artifacts to ``models/<model_id>/``."""
        export_dir = self.settings.models_dir / model_id
        export_dir.mkdir(parents=True, exist_ok=True)

        is_pytorch = hasattr(model, "model_state_dict") or "lstm" in model_id.lower()
        model_ext = ".pt" if is_pytorch else ".pkl"
        model_path = export_dir / f"model{model_ext}"

        if is_pytorch:
            if hasattr(model, "save"):
                model.save(export_dir)
                if not model_path.exists():
                    for p in export_dir.glob("*.pt"):
                        shutil.copy(p, model_path)
            else:
                import torch

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

        # Explainer
        if explainer:
            with open(export_dir / "explainer.pkl", "wb") as f:
                pickle.dump(explainer, f)

        # Metrics JSON
        (export_dir / "metrics.json").write_text(
            json.dumps(metrics.to_dict(), indent=2, default=str)
        )

        logger.info("Saved model %s to %s", model_id, export_dir)
        return export_dir

    def _upload_to_clearml(
        self,
        export_dir: Path,
        model_id: str,
        metrics: EvaluationMetrics,
        is_champion: bool = False,
    ) -> str:
        """Upload model directory to ClearML as an artifact."""
        try:
            from clearml import Task

            task = Task.current_task()
            if not task:
                task = Task.init(
                    project_name=self.settings.clearml_project_name,
                    task_name=f"Model Upload - {model_id}",
                )

            # Log metrics
            metrics_dict = metrics.to_dict()
            for k, v in metrics_dict.items():
                if isinstance(v, (int, float)):
                    task.get_logger().report_scalar(
                        f"Evaluation/{model_id}", k, iteration=0, value=v
                    )

            artifact_name = f"{self.settings.model_registry_name}-{model_id}"
            task.upload_artifact(name=artifact_name, artifact_object=str(export_dir))

            tags = [model_id]
            if is_champion:
                tags.append("champion")
            task.set_tags(tags)

            logger.info("Uploaded %s to ClearML", model_id)
            return task.id
        except ImportError:
            logger.warning("ClearML not installed – model saved locally only.")
            return "local"
        except Exception as e:
            logger.error("ClearML upload failed for %s: %s", model_id, e)
            return "local"

    def _get_from_clearml(self, model_id: str) -> tuple[Path, dict[str, Any]] | None:
        """Retrieve a model from ClearML (legacy fallback)."""
        try:
            from clearml import Task

            target_name = f"{self.settings.model_registry_name}-{model_id}"

            tasks = Task.get_tasks(
                project_name=self.settings.clearml_project_name,
                tags=["champion", model_id],
            )
            if not tasks:
                tasks = Task.get_tasks(
                    project_name=self.settings.clearml_project_name,
                    tags=[model_id],
                )
            if not tasks:
                logger.warning("No ClearML artifacts found for %s", target_name)
                return None

            best_task = tasks[0]

            if target_name in best_task.artifacts:
                local_path = best_task.artifacts[target_name].get_local_copy()
            else:
                logger.warning("Artifact %s not found in Task", target_name)
                return None

            if not local_path:
                return None

            download_dir = Path(local_path)
            model_file = self._find_model_file(download_dir, model_id)
            if model_file is None:
                return None

            metadata = {"id": model_id, "clearml_task_id": best_task.id}
            return model_file, metadata
        except ImportError:
            logger.error("ClearML package not installed.")
            return None
        except Exception as e:
            logger.error("ClearML retrieval failed for %s: %s", model_id, e)
            return None

    @staticmethod
    def _find_model_file(directory: Path, model_id: str) -> Path | None:
        """Locate the primary model file inside *directory*."""
        is_pytorch = "lstm" in model_id.lower()
        model_ext = ".pt" if is_pytorch else ".pkl"

        model_file = directory / f"model{model_ext}"
        if model_file.exists():
            return model_file

        candidates = list(directory.glob(f"*{model_ext}"))
        if candidates:
            return candidates[0]

        # Try the other extension as fallback
        alt_ext = ".pkl" if is_pytorch else ".pt"
        alt_file = directory / f"model{alt_ext}"
        if alt_file.exists():
            return alt_file

        alt_candidates = list(directory.glob(f"*{alt_ext}"))
        if alt_candidates:
            return alt_candidates[0]

        logger.warning("No model file found in %s", directory)
        return None
