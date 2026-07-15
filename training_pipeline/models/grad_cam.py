"""Temporal Grad-CAM for LSTM-based time-series models.

Implements gradient-weighted class activation mapping adapted for
temporal sequences, highlighting which time steps and features in
the lookback window contributed most to each prediction.

Example:
    >>> from training_pipeline.models.grad_cam import TemporalGradCAM
    >>> grad_cam = TemporalGradCAM(model.model)
    >>> heatmap, preds = grad_cam.generate(X_input)
    >>> # heatmap shape: (batch, lookback, n_features)
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class TemporalGradCAM:
    """Gradient-weighted activation mapping for temporal sequences.

    Hooks into a target layer (typically the LSTM output) and computes
    how much each time step and feature contributes to the final prediction
    by examining the gradients flowing back through the network.

    Attributes:
        model: The PyTorch model to explain.
        target_layer: The layer to hook for activations/gradients.
        activations: Cached forward activations.
        gradients: Cached backward gradients.
    """

    def __init__(
        self,
        model: nn.Module,
        target_layer: Optional[nn.Module] = None,
    ) -> None:
        """Initialize Temporal Grad-CAM.

        Args:
            model: PyTorch model (e.g., BiLSTMNetwork).
            target_layer: Layer to hook. If None, auto-detects the LSTM layer.
        """
        self.model = model
        self.activations: Optional[torch.Tensor] = None
        self.gradients: Optional[torch.Tensor] = None

        # Auto-detect target layer
        if target_layer is None:
            target_layer = self._find_lstm_layer(model)

        if target_layer is None:
            raise ValueError("Could not find LSTM layer. Specify target_layer explicitly.")

        self.target_layer = target_layer

        # Register hooks
        self._forward_hook = target_layer.register_forward_hook(self._save_activation)
        self._backward_hook = target_layer.register_full_backward_hook(self._save_gradient)

    def _find_lstm_layer(self, model: nn.Module) -> Optional[nn.Module]:
        """Auto-detect the LSTM layer in the model."""
        for name, module in model.named_modules():
            if isinstance(module, nn.LSTM):
                logger.info("Grad-CAM: auto-detected LSTM layer '%s'", name)
                return module
        return None

    def _save_activation(
        self,
        module: nn.Module,
        input: Tuple[torch.Tensor, ...],
        output: torch.Tensor,
    ) -> None:
        """Forward hook to cache activations."""
        if isinstance(output, tuple):
            # LSTM returns (output, (h_n, c_n))
            self.activations = output[0].detach()
        else:
            self.activations = output.detach()

    def _save_gradient(
        self,
        module: nn.Module,
        grad_input: Tuple[torch.Tensor, ...],
        grad_output: Tuple[torch.Tensor, ...],
    ) -> None:
        """Backward hook to cache gradients."""
        self.gradients = grad_output[0].detach()

    def generate(
        self,
        x: torch.Tensor,
        target_timestep: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate Grad-CAM heatmap for input sequences.

        Args:
            x: Input tensor (batch, lookback, features).
            target_timestep: Which forecast timestep to explain.
                If None, uses the mean of all forecast outputs.

        Returns:
            Tuple of:
            - heatmap: (batch, lookback) temporal importance weights
            - predictions: (batch, forecast_horizon) raw predictions
        """
        self.model.eval()
        x = x.clone().requires_grad_(True)

        # Forward pass
        output, _ = self.model(x)
        predictions = output.squeeze(-1).detach().cpu().numpy()

        # Select target for backprop
        if target_timestep is not None:
            target = output[:, target_timestep, :].sum()
        else:
            target = output.sum()

        # Backward pass
        self.model.zero_grad()
        target.backward(retain_graph=True)

        if self.gradients is None or self.activations is None:
            logger.warning("Grad-CAM: No gradients/activations captured.")
            return np.zeros((x.shape[0], x.shape[1])), predictions

        # Compute importance weights via global average pooling of gradients
        # gradients shape: (batch, seq_len, hidden_dim)
        weights = self.gradients.mean(dim=-1)  # (batch, seq_len)

        # Weighted activation (element-wise along hidden dim, then sum)
        # activations shape: (batch, seq_len, hidden_dim)
        cam = (self.activations * self.gradients).sum(dim=-1)  # (batch, seq_len)

        # ReLU — only keep positive contributions
        cam = torch.relu(cam)

        # Normalize per sample
        cam_min = cam.min(dim=1, keepdim=True).values
        cam_max = cam.max(dim=1, keepdim=True).values
        cam_range = cam_max - cam_min
        cam_range[cam_range == 0] = 1.0
        cam = (cam - cam_min) / cam_range

        heatmap = cam.cpu().numpy()

        logger.info(
            "Grad-CAM generated: %d samples, lookback=%d",
            heatmap.shape[0], heatmap.shape[1],
        )

        return heatmap, predictions

    def generate_feature_heatmap(
        self,
        x: torch.Tensor,
        feature_names: Optional[List[str]] = None,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """Generate per-feature importance using input gradients.

        Uses the gradient of the output with respect to the input tensor
        directly (not through a hooked layer) to compute feature-level
        importance across all time steps.

        Args:
            x: Input tensor (batch, lookback, features).
            feature_names: Names for each feature dimension.

        Returns:
            Tuple of:
            - feature_time_heatmap: (lookback, n_features) importance matrix
            - feature_importance: Dict mapping feature names to aggregate scores
        """
        self.model.eval()
        x = x.clone().requires_grad_(True)

        output, _ = self.model(x)
        target = output.sum()

        self.model.zero_grad()
        target.backward()

        if x.grad is None:
            logger.warning("No input gradients computed.")
            n_features = x.shape[2]
            return np.zeros((x.shape[1], n_features)), {}

        # Input gradient importance: |grad| averaged over batch
        input_grads = x.grad.abs().mean(dim=0).cpu().numpy()  # (lookback, features)

        # Aggregate per-feature importance
        feature_scores = input_grads.mean(axis=0)  # (features,)
        n_features = len(feature_scores)

        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(n_features)]

        feature_importance = {
            name: float(score)
            for name, score in sorted(
                zip(feature_names, feature_scores),
                key=lambda x: -x[1],
            )
        }

        return input_grads, feature_importance

    def cleanup(self) -> None:
        """Remove hooks to prevent memory leaks."""
        self._forward_hook.remove()
        self._backward_hook.remove()
        self.activations = None
        self.gradients = None

    def __del__(self) -> None:
        try:
            self.cleanup()
        except Exception:
            pass
