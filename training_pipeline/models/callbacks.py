"""Reusable training callbacks for PyTorch models.

Provides modular, composable callbacks for common training patterns:
- EarlyStopping with best-weight restoration
- ModelCheckpoint for periodic saving
- GradientAccumulator for simulating large batches
- TrainingLogger for metrics tracking

Example:
    >>> from training_pipeline.models.callbacks import EarlyStopping, ModelCheckpoint
    >>> early_stop = EarlyStopping(patience=15, min_delta=1e-4)
    >>> checkpoint = ModelCheckpoint(save_dir="models/checkpoints")
    >>> # In training loop:
    >>> early_stop.step(val_loss, model)
    >>> if early_stop.should_stop:
    ...     break
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Early Stopping
# ──────────────────────────────────────────────────────────────────────────────


class EarlyStopping:
    """Early stopping with best model state restoration.

    Monitors a validation metric and stops training when no improvement
    is observed for a specified number of epochs. Automatically saves
    and restores the best model weights.

    Attributes:
        patience: Number of epochs to wait for improvement.
        min_delta: Minimum change to qualify as improvement.
        best_score: Best validation score observed.
        best_epoch: Epoch at which best score was observed.
        counter: Number of epochs without improvement.
        should_stop: Whether training should be stopped.
        best_state: State dict of the best model.
    """

    def __init__(
        self,
        patience: int = 15,
        min_delta: float = 1e-4,
        mode: str = "min",
    ) -> None:
        """Initialize early stopping.

        Args:
            patience: Epochs to wait before stopping.
            min_delta: Minimum improvement threshold.
            mode: 'min' for loss (lower is better), 'max' for metrics (higher is better).
        """
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.best_score: Optional[float] = None
        self.best_epoch: int = 0
        self.counter: int = 0
        self.should_stop: bool = False
        self.best_state: Optional[Dict[str, Any]] = None

    def _is_improvement(self, current: float) -> bool:
        """Check if current score is an improvement over best."""
        if self.best_score is None:
            return True
        if self.mode == "min":
            return current < (self.best_score - self.min_delta)
        return current > (self.best_score + self.min_delta)

    def step(self, score: float, model: nn.Module, epoch: int = 0) -> bool:
        """Update early stopping state with new validation score.

        Args:
            score: Current validation metric value.
            model: PyTorch model to save state from.
            epoch: Current epoch number.

        Returns:
            True if training should stop, False otherwise.
        """
        if self._is_improvement(score):
            self.best_score = score
            self.best_epoch = epoch
            self.counter = 0
            # Deep copy model state
            self.best_state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True
                logger.info(
                    "Early stopping triggered at epoch %d "
                    "(best=%.6f at epoch %d, patience=%d)",
                    epoch, self.best_score, self.best_epoch, self.patience,
                )

        return self.should_stop

    def restore_best(self, model: nn.Module) -> None:
        """Restore the best model weights.

        Args:
            model: PyTorch model to restore weights into.
        """
        if self.best_state is not None:
            model.load_state_dict(self.best_state)
            logger.info(
                "Restored best model from epoch %d (score=%.6f)",
                self.best_epoch, self.best_score,
            )


# ──────────────────────────────────────────────────────────────────────────────
# Model Checkpoint
# ──────────────────────────────────────────────────────────────────────────────


class ModelCheckpoint:
    """Save model checkpoints during training.

    Saves the model state dict to disk whenever a new best score
    is achieved, with optional periodic saving every N epochs.

    Attributes:
        save_dir: Directory for checkpoint files.
        best_score: Best validation score observed.
        save_every: Save a checkpoint every N epochs (0 = only on improvement).
    """

    def __init__(
        self,
        save_dir: Path,
        filename_prefix: str = "checkpoint",
        save_every: int = 0,
        mode: str = "min",
    ) -> None:
        """Initialize checkpoint manager.

        Args:
            save_dir: Directory to save checkpoints.
            filename_prefix: Prefix for checkpoint filenames.
            save_every: Save every N epochs (0 = best only).
            mode: 'min' for loss, 'max' for accuracy.
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.filename_prefix = filename_prefix
        self.save_every = save_every
        self.mode = mode
        self.best_score: Optional[float] = None

    def _is_improvement(self, current: float) -> bool:
        if self.best_score is None:
            return True
        if self.mode == "min":
            return current < self.best_score
        return current > self.best_score

    def step(
        self,
        score: float,
        model: nn.Module,
        epoch: int,
        optimizer: Optional[torch.optim.Optimizer] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Optional[Path]:
        """Save checkpoint if conditions are met.

        Args:
            score: Current validation metric.
            model: Model to checkpoint.
            epoch: Current epoch.
            optimizer: Optional optimizer state to save.
            extra: Optional extra metadata.

        Returns:
            Path to saved checkpoint, or None if not saved.
        """
        save_path = None

        # Save on improvement
        if self._is_improvement(score):
            self.best_score = score
            save_path = self.save_dir / f"{self.filename_prefix}_best.pt"
            self._save(save_path, model, epoch, optimizer, extra)
            logger.info("Checkpoint saved (best=%.6f): %s", score, save_path)

        # Periodic save
        if self.save_every > 0 and (epoch + 1) % self.save_every == 0:
            periodic_path = self.save_dir / f"{self.filename_prefix}_epoch{epoch+1}.pt"
            self._save(periodic_path, model, epoch, optimizer, extra)

        return save_path

    def _save(
        self,
        path: Path,
        model: nn.Module,
        epoch: int,
        optimizer: Optional[torch.optim.Optimizer] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "best_score": self.best_score,
        }
        if optimizer is not None:
            checkpoint["optimizer_state_dict"] = optimizer.state_dict()
        if extra is not None:
            checkpoint["extra"] = extra
        torch.save(checkpoint, path)


# ──────────────────────────────────────────────────────────────────────────────
# Gradient Accumulation
# ──────────────────────────────────────────────────────────────────────────────


class GradientAccumulator:
    """Simulate larger batch sizes via gradient accumulation.

    Accumulates gradients over multiple mini-batches before performing
    an optimizer step, effectively multiplying the batch size without
    increasing memory usage.

    Attributes:
        accumulation_steps: Number of mini-batches to accumulate.
        current_step: Current step within the accumulation window.
    """

    def __init__(self, accumulation_steps: int = 4) -> None:
        """Initialize gradient accumulator.

        Args:
            accumulation_steps: Number of steps to accumulate before update.
        """
        self.accumulation_steps = max(1, accumulation_steps)
        self.current_step = 0

    def should_step(self) -> bool:
        """Check if optimizer should perform an update step.

        Returns:
            True if accumulated enough gradients.
        """
        self.current_step += 1
        return self.current_step % self.accumulation_steps == 0

    def scale_loss(self, loss: torch.Tensor) -> torch.Tensor:
        """Scale loss by accumulation steps for correct gradient magnitude.

        Args:
            loss: Raw loss tensor.

        Returns:
            Scaled loss tensor.
        """
        return loss / self.accumulation_steps

    def reset(self) -> None:
        """Reset the step counter (call at epoch start)."""
        self.current_step = 0


# ──────────────────────────────────────────────────────────────────────────────
# Training Logger
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class EpochMetrics:
    """Metrics for a single training epoch."""
    epoch: int
    train_loss: float
    val_loss: float = float("inf")
    learning_rate: float = 0.0
    grad_norm: float = 0.0
    epoch_time_s: float = 0.0


class TrainingLogger:
    """Records and exports training metrics.

    Tracks per-epoch metrics (loss, LR, gradient norms) and provides
    export functionality for analysis and visualization.

    Attributes:
        history: List of per-epoch metrics.
        start_time: Training start timestamp.
    """

    def __init__(self) -> None:
        self.history: List[EpochMetrics] = []
        self.start_time: float = time.time()

    def log_epoch(self, metrics: EpochMetrics) -> None:
        """Record metrics for one epoch.

        Args:
            metrics: Epoch metrics to record.
        """
        self.history.append(metrics)

    def get_best_epoch(self, metric: str = "val_loss", mode: str = "min") -> Optional[EpochMetrics]:
        """Get the epoch with the best metric value.

        Args:
            metric: Name of the metric field.
            mode: 'min' or 'max'.

        Returns:
            EpochMetrics for the best epoch, or None if empty.
        """
        if not self.history:
            return None
        key = lambda m: getattr(m, metric, float("inf"))
        if mode == "min":
            return min(self.history, key=key)
        return max(self.history, key=key)

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert history to list of dicts for JSON serialization."""
        return [
            {
                "epoch": m.epoch,
                "train_loss": m.train_loss,
                "val_loss": m.val_loss,
                "learning_rate": m.learning_rate,
                "grad_norm": m.grad_norm,
                "epoch_time_s": m.epoch_time_s,
            }
            for m in self.history
        ]

    def save(self, path: Path) -> None:
        """Save training history to JSON file.

        Args:
            path: Output file path.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict_list(), f, indent=2)
        logger.info("Training history saved to %s (%d epochs)", path, len(self.history))

    @property
    def total_time_s(self) -> float:
        """Total training time in seconds."""
        return time.time() - self.start_time
