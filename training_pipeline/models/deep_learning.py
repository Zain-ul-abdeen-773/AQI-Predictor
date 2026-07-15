"""Bidirectional LSTM with Multi-Head Attention for AQI sequence prediction.

Implements a PyTorch Bi-LSTM model with custom attention mechanism for
processing multivariate time-series data. Takes 72 hours of historical
data as input and predicts the next 72 hours of AQI values.

Key features:
- Bidirectional LSTM for capturing forward and backward temporal patterns
- Multi-head attention mechanism for focusing on important time steps
- Asymmetric loss function penalizing hazardous under-predictions
- AdamW optimizer with OneCycleLR learning rate scheduler
- Dropout regularization throughout the network

Example:
    >>> from training_pipeline.models.deep_learning import BiLSTMAttention
    >>> model = BiLSTMAttention(input_size=40, hidden_size=128)
    >>> model.fit(X_train_seq, y_train_seq)
    >>> predictions = model.predict(X_test_seq)
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from config.settings import get_settings

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Multi-Head Attention Module
# ──────────────────────────────────────────────────────────────────────────────


class MultiHeadAttention(nn.Module):
    """Multi-head attention mechanism for temporal sequence focus.

    Learns to attend to the most relevant time steps in the LSTM output
    sequence for predicting future AQI values.

    Attributes:
        n_heads: Number of attention heads.
        head_dim: Dimension per attention head.
        scale: Scaling factor for dot-product attention.
    """

    def __init__(self, hidden_size: int, n_heads: int = 4) -> None:
        """Initialize multi-head attention.

        Args:
            hidden_size: LSTM hidden size (must be divisible by n_heads).
            n_heads: Number of parallel attention heads.
        """
        super().__init__()
        assert hidden_size % n_heads == 0, "hidden_size must be divisible by n_heads"

        self.n_heads = n_heads
        self.head_dim = hidden_size // n_heads
        self.scale = self.head_dim ** 0.5

        self.query = nn.Linear(hidden_size, hidden_size)
        self.key = nn.Linear(hidden_size, hidden_size)
        self.value = nn.Linear(hidden_size, hidden_size)
        self.output_proj = nn.Linear(hidden_size, hidden_size)

        self.dropout = nn.Dropout(0.1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Apply multi-head attention over the sequence.

        Args:
            x: LSTM output tensor (batch, seq_len, hidden_size).

        Returns:
            Tuple of:
            - Attended output (batch, seq_len, hidden_size)
            - Attention weights (batch, n_heads, seq_len, seq_len)
        """
        batch_size, seq_len, _ = x.shape

        # Project to Q, K, V
        Q = self.query(x).view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        K = self.key(x).view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        V = self.value(x).view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)

        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale
        weights = torch.softmax(scores, dim=-1)
        weights = self.dropout(weights)

        # Weighted sum
        attended = torch.matmul(weights, V)
        attended = attended.transpose(1, 2).contiguous().view(batch_size, seq_len, -1)

        output = self.output_proj(attended)
        return output, weights


# ──────────────────────────────────────────────────────────────────────────────
# Asymmetric Loss Function
# ──────────────────────────────────────────────────────────────────────────────


class AsymmetricMSELoss(nn.Module):
    """Asymmetric MSE loss penalizing under-prediction of hazardous AQI.

    When the true AQI is in hazardous range (>150) and the model
    under-predicts, the loss is amplified by a penalty factor.
    This ensures the model is conservative for dangerous air quality levels.

    Attributes:
        hazard_threshold: AQI value above which under-predictions are penalized.
        penalty_factor: Multiplier for under-prediction loss in hazardous range.
    """

    def __init__(
        self,
        hazard_threshold: float = 150.0,
        penalty_factor: float = 3.0,
    ) -> None:
        super().__init__()
        self.hazard_threshold = hazard_threshold
        self.penalty_factor = penalty_factor

    def forward(self, y_pred: torch.Tensor, y_true: torch.Tensor) -> torch.Tensor:
        """Compute asymmetric MSE loss.

        Args:
            y_pred: Predicted AQI values.
            y_true: True AQI values.

        Returns:
            torch.Tensor: Scalar loss value.
        """
        errors = y_true - y_pred
        squared_errors = errors ** 2

        # Identify under-predictions in hazardous range
        is_hazardous = y_true > self.hazard_threshold
        is_under_prediction = errors > 0  # y_true > y_pred

        # Apply penalty multiplier
        weights = torch.ones_like(squared_errors)
        weights[is_hazardous & is_under_prediction] = self.penalty_factor

        weighted_loss = (weights * squared_errors).mean()
        return weighted_loss


# ──────────────────────────────────────────────────────────────────────────────
# Bi-LSTM + Attention Network
# ──────────────────────────────────────────────────────────────────────────────


class BiLSTMNetwork(nn.Module):
    """Bidirectional LSTM with Multi-Head Attention for sequence-to-sequence prediction.

    Architecture:
    1. Bidirectional LSTM layers with dropout
    2. Multi-head attention over LSTM outputs
    3. Layer normalization
    4. Fully connected output layers producing (forecast_horizon, 1)

    Attributes:
        lstm: Bidirectional LSTM stack.
        attention: Multi-head attention module.
        layer_norm: Layer normalization.
        fc_layers: Fully connected output layers.
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
        forecast_horizon: int = 72,
        n_attention_heads: int = 4,
    ) -> None:
        """Initialize the Bi-LSTM network.

        Args:
            input_size: Number of input features per time step.
            hidden_size: LSTM hidden dimension.
            num_layers: Number of stacked LSTM layers.
            dropout: Dropout probability.
            forecast_horizon: Number of future time steps to predict.
            n_attention_heads: Number of attention heads.
        """
        super().__init__()

        self.hidden_size = hidden_size
        self.forecast_horizon = forecast_horizon

        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # Attention (operates on 2*hidden_size due to bidirectional)
        self.attention = MultiHeadAttention(
            hidden_size=hidden_size * 2,
            n_heads=n_attention_heads,
        )

        # Layer normalization
        self.layer_norm = nn.LayerNorm(hidden_size * 2)

        # Output projection
        self.dropout = nn.Dropout(dropout)

        self.fc_layers = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Dropout(dropout / 2),
            nn.Linear(hidden_size // 2, forecast_horizon),
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass through the network.

        Args:
            x: Input tensor (batch, lookback_window, input_size).

        Returns:
            Tuple of:
            - Predictions (batch, forecast_horizon, 1)
            - Attention weights (batch, n_heads, seq_len, seq_len)
        """
        # LSTM encoding
        lstm_out, _ = self.lstm(x)  # (batch, seq_len, 2*hidden)

        # Attention
        attended, attn_weights = self.attention(lstm_out)

        # Residual connection + layer norm
        attended = self.layer_norm(attended + lstm_out)

        # Global average pooling over time
        pooled = attended.mean(dim=1)  # (batch, 2*hidden)

        # Output projection
        pooled = self.dropout(pooled)
        output = self.fc_layers(pooled)  # (batch, forecast_horizon)

        return output.unsqueeze(-1), attn_weights  # (batch, 72, 1)


# ──────────────────────────────────────────────────────────────────────────────
# Training Wrapper
# ──────────────────────────────────────────────────────────────────────────────


class BiLSTMAttention:
    """High-level training wrapper for the Bi-LSTM + Attention model.

    Handles data preparation, training loop with OneCycleLR scheduler,
    early stopping, and model serialization.

    Attributes:
        input_size: Number of input features.
        hidden_size: LSTM hidden dimension.
        num_layers: Number of LSTM layers.
        dropout: Dropout rate.
        forecast_horizon: Steps to predict into the future.
        learning_rate: AdamW initial learning rate.
        epochs: Maximum training epochs.
        batch_size: Training batch size.
        device: Computation device (cuda or cpu).
        model: The neural network.
        is_fitted: Whether the model is trained.
    """

    def __init__(
        self,
        input_size: int = 40,
        hidden_size: Optional[int] = None,
        num_layers: Optional[int] = None,
        dropout: Optional[float] = None,
        forecast_horizon: Optional[int] = None,
        learning_rate: Optional[float] = None,
        epochs: Optional[int] = None,
        batch_size: Optional[int] = None,
    ) -> None:
        settings = get_settings()

        self.input_size = input_size
        self.hidden_size = hidden_size or settings.lstm_hidden_size
        self.num_layers = num_layers or settings.lstm_num_layers
        self.dropout = dropout or settings.lstm_dropout
        self.forecast_horizon = forecast_horizon or settings.forecast_horizon_hours
        self.learning_rate = learning_rate or settings.lstm_learning_rate
        self.epochs = epochs or settings.lstm_epochs
        self.batch_size = batch_size or settings.lstm_batch_size

        # Device selection
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Using device: %s", self.device)

        # Build network
        self.model = BiLSTMNetwork(
            input_size=self.input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout,
            forecast_horizon=self.forecast_horizon,
        ).to(self.device)

        self.is_fitted = False
        self.training_history: List[Dict[str, float]] = []
        self.feature_names: List[str] = []

        total_params = sum(p.numel() for p in self.model.parameters())
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        logger.info(
            "BiLSTM initialized: %d total params, %d trainable, horizon=%d",
            total_params, trainable, self.forecast_horizon,
        )

    @staticmethod
    def create_sequences(
        X: np.ndarray,
        y: np.ndarray,
        lookback: int = 72,
        horizon: int = 72,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create sliding window sequences for time-series training.

        Args:
            X: Feature matrix (n_timesteps, n_features).
            y: Target values (n_timesteps,).
            lookback: Number of historical time steps as input.
            horizon: Number of future time steps to predict.

        Returns:
            Tuple of:
            - Input sequences (n_sequences, lookback, n_features)
            - Target sequences (n_sequences, horizon)
        """
        X_seq, y_seq = [], []
        for i in range(lookback, len(X) - horizon + 1):
            X_seq.append(X[i - lookback: i])
            y_seq.append(y[i: i + horizon])
        return np.array(X_seq), np.array(y_seq)

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None,
        patience: int = 15,
    ) -> "BiLSTMAttention":
        """Train the Bi-LSTM model with OneCycleLR and early stopping.

        Args:
            X_train: Training sequences (n_seq, lookback, features).
            y_train: Target sequences (n_seq, horizon).
            X_val: Validation sequences (optional).
            y_val: Validation targets (optional).
            feature_names: Input feature names.
            patience: Early stopping patience (epochs).

        Returns:
            Self for method chaining.
        """
        self.feature_names = feature_names or [f"f{i}" for i in range(self.input_size)]

        # Convert to tensors
        X_tensor = torch.FloatTensor(X_train).to(self.device)
        y_tensor = torch.FloatTensor(y_train).to(self.device)

        dataset = TensorDataset(X_tensor, y_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        # Validation data
        has_val = X_val is not None and y_val is not None
        if has_val:
            X_val_tensor = torch.FloatTensor(X_val).to(self.device)
            y_val_tensor = torch.FloatTensor(y_val).to(self.device)

        # Optimizer and scheduler
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=1e-4,
        )
        scheduler = torch.optim.lr_scheduler.OneCycleLR(
            optimizer,
            max_lr=self.learning_rate * 10,
            epochs=self.epochs,
            steps_per_epoch=len(dataloader),
        )

        criterion = AsymmetricMSELoss(
            hazard_threshold=get_settings().aqi_alert_threshold,
            penalty_factor=3.0,
        )

        # ── Training Loop ──
        best_val_loss = float("inf")
        patience_counter = 0
        best_state = None

        logger.info(
            "Training Bi-LSTM: %d epochs, batch_size=%d, lr=%.6f",
            self.epochs, self.batch_size, self.learning_rate,
        )

        for epoch in range(self.epochs):
            self.model.train()
            epoch_losses = []

            for batch_X, batch_y in dataloader:
                optimizer.zero_grad()

                predictions, _ = self.model(batch_X)
                loss = criterion(predictions.squeeze(-1), batch_y)

                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                scheduler.step()

                epoch_losses.append(loss.item())

            train_loss = np.mean(epoch_losses)

            # Validation
            val_loss = float("inf")
            if has_val:
                self.model.eval()
                with torch.no_grad():
                    val_pred, _ = self.model(X_val_tensor)
                    val_loss = criterion(val_pred.squeeze(-1), y_val_tensor).item()

            # Log progress
            current_lr = optimizer.param_groups[0]["lr"]
            self.training_history.append({
                "epoch": epoch + 1,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "learning_rate": current_lr,
            })

            if (epoch + 1) % 10 == 0:
                logger.info(
                    "Epoch %d/%d — train_loss=%.4f, val_loss=%.4f, lr=%.6f",
                    epoch + 1, self.epochs, train_loss, val_loss, current_lr,
                )

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_state = {k: v.clone() for k, v in self.model.state_dict().items()}
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(
                        "Early stopping at epoch %d (best val_loss=%.4f)",
                        epoch + 1, best_val_loss,
                    )
                    break

        # Restore best weights
        if best_state is not None:
            self.model.load_state_dict(best_state)

        self.is_fitted = True
        logger.info("Training complete. Best validation loss: %.4f", best_val_loss)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate AQI forecast predictions.

        Args:
            X: Input sequences (n_seq, lookback, features).

        Returns:
            np.ndarray: Predictions (n_seq, forecast_horizon).

        Raises:
            RuntimeError: If model is not fitted.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        self.model.eval()
        X_tensor = torch.FloatTensor(X).to(self.device)

        with torch.no_grad():
            predictions, _ = self.model(X_tensor)

        result = predictions.squeeze(-1).cpu().numpy()
        return np.clip(result, 0, 500)

    def predict_with_attention(
        self, X: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate predictions with attention weights for interpretability.

        Args:
            X: Input sequences (n_seq, lookback, features).

        Returns:
            Tuple of:
            - Predictions (n_seq, forecast_horizon)
            - Attention weights (n_seq, n_heads, seq_len, seq_len)
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        self.model.eval()
        X_tensor = torch.FloatTensor(X).to(self.device)

        with torch.no_grad():
            predictions, attn_weights = self.model(X_tensor)

        preds = predictions.squeeze(-1).cpu().numpy()
        weights = attn_weights.cpu().numpy()
        return np.clip(preds, 0, 500), weights

    def get_params(self) -> Dict[str, Any]:
        """Get model architecture parameters.

        Returns:
            Dict of architecture hyperparameters.
        """
        return {
            "model_type": "bilstm_attention",
            "input_size": self.input_size,
            "hidden_size": self.hidden_size,
            "num_layers": self.num_layers,
            "dropout": self.dropout,
            "forecast_horizon": self.forecast_horizon,
            "learning_rate": self.learning_rate,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "total_params": sum(p.numel() for p in self.model.parameters()),
            "training_history": self.training_history[-5:] if self.training_history else [],
        }

    def save(self, path: Path) -> None:
        """Save model weights and configuration.

        Args:
            path: File path for saving (.pt).
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "model_state": self.model.state_dict(),
            "config": {
                "input_size": self.input_size,
                "hidden_size": self.hidden_size,
                "num_layers": self.num_layers,
                "dropout": self.dropout,
                "forecast_horizon": self.forecast_horizon,
            },
            "feature_names": self.feature_names,
            "training_history": self.training_history,
            "is_fitted": self.is_fitted,
        }, path)
        logger.info("Saved BiLSTM model to %s", path)

    @classmethod
    def load(cls, path: Path) -> "BiLSTMAttention":
        """Load a trained model from disk.

        Args:
            path: Path to saved model (.pt).

        Returns:
            BiLSTMAttention: Loaded model instance.
        """
        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        config = checkpoint["config"]

        instance = cls(
            input_size=config["input_size"],
            hidden_size=config["hidden_size"],
            num_layers=config["num_layers"],
            dropout=config["dropout"],
            forecast_horizon=config["forecast_horizon"],
        )

        instance.model.load_state_dict(checkpoint["model_state"])
        instance.feature_names = checkpoint.get("feature_names", [])
        instance.training_history = checkpoint.get("training_history", [])
        instance.is_fitted = checkpoint.get("is_fitted", True)

        logger.info("Loaded BiLSTM model from %s", path)
        return instance
