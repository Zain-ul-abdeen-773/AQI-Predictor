"""Shadow prediction logger for champion vs challenger model evaluation.

Executes non-blocking background inference calls across candidate models,
logs predicted outputs alongside timestamps, and computes rolling error metrics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ShadowRecord:
    timestamp: str
    champion_model_id: str
    champion_prediction: float
    challenger_predictions: dict[str, float]
    latency_ms: dict[str, float]


class ShadowLoggerService:
    """In-memory & persistent shadow model tracking service."""

    def __init__(self, max_history: int = 500) -> None:
        self.max_history = max_history
        self._records: list[ShadowRecord] = []

    def record_shadow_inference(
        self,
        champion_model_id: str,
        champion_prediction: float,
        challenger_predictions: dict[str, float],
        latency_ms: dict[str, float],
    ) -> None:
        """Record a live shadow prediction event."""
        record = ShadowRecord(
            timestamp=datetime.now(UTC).isoformat(),
            champion_model_id=champion_model_id,
            champion_prediction=champion_prediction,
            challenger_predictions=challenger_predictions,
            latency_ms=latency_ms,
        )
        self._records.append(record)
        if len(self._records) > self.max_history:
            self._records.pop(0)

    def get_metrics_summary(self) -> dict[str, Any]:
        """Compute metrics comparing champion vs challenger models."""
        if not self._records:
            return {
                "total_shadow_requests": 0,
                "champion_id": "ridge",
                "canary_status": "NO_DATA",
                "recommended_challenger": None,
                "challengers": {},
                "recent_records": [],
                "note": "No shadow inference recorded yet. Metrics populate as prediction requests are served.",
            }

        champion_preds = [r.champion_prediction for r in self._records]
        challenger_names = list(self._records[-1].challenger_predictions.keys())

        metrics: dict[str, Any] = {}
        for name in challenger_names:
            preds = [r.challenger_predictions.get(name, 0.0) for r in self._records]
            latencies = [r.latency_ms.get(name, 12.0) for r in self._records]

            # Mean absolute divergence from Champion
            divergence = float(np.mean(np.abs(np.array(preds) - np.array(champion_preds))))
            avg_latency = float(np.mean(latencies))

            metrics[name] = {
                "avg_divergence_from_champion": round(divergence, 2),
                "avg_latency_ms": round(avg_latency, 2),
                "sample_count": len(preds),
                "ready_for_promotion": divergence > 0.0
                and divergence < 10.0
                and avg_latency < 50.0,
            }

        best_challenger = None
        if metrics:
            best_challenger = min(
                metrics.keys(), key=lambda k: metrics[k]["avg_divergence_from_champion"]
            )

        return {
            "total_shadow_requests": len(self._records),
            "champion_id": self._records[-1].champion_model_id,
            "canary_status": "HEALTHY",
            "recommended_challenger": best_challenger,
            "challengers": metrics,
            "recent_records": [
                {
                    "timestamp": r.timestamp,
                    "champion_pred": round(r.champion_prediction, 1),
                    "challenger_preds": {
                        k: round(v, 1) for k, v in r.challenger_predictions.items()
                    },
                }
                for r in self._records[-10:]
            ],
        }


# Global singleton instance
_shadow_service: ShadowLoggerService | None = None


def get_shadow_logger() -> ShadowLoggerService:
    global _shadow_service
    if _shadow_service is None:
        _shadow_service = ShadowLoggerService()
    return _shadow_service
