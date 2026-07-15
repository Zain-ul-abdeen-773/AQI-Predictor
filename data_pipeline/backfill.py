"""Historical data backfill pipeline.

Generates training data by running the feature pipeline across a range of
past dates. Supports chunked batch writes to prevent memory overflows
and resumable state for long-running backfill operations.

Example:
    >>> from data_pipeline.backfill import BackfillPipeline
    >>> pipeline = BackfillPipeline()
    >>> df = pipeline.run(years=5)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import pandas as pd

from config.settings import get_settings, Settings
from config.schemas import RawDataPayload
from data_pipeline.ingest import SyntheticDataGenerator
from data_pipeline.transformers import FeatureEngineer

logger = logging.getLogger(__name__)


class BackfillPipeline:
    """Historical data backfill pipeline for generating training data.

    Generates hourly synthetic data for the configured number of past years,
    applies feature engineering, and writes results in configurable batch
    sizes to prevent memory overflow.

    Supports checkpoint/resume for interrupted backfill operations.

    Attributes:
        settings: Application settings instance.
        generator: Synthetic data generator.
        engineer: Feature engineering transformer.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.generator = SyntheticDataGenerator(self.settings)
        self.engineer = FeatureEngineer(self.settings)
        self._checkpoint_path = self.settings.data_dir / "backfill_checkpoint.json"

    def generate_timestamps(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        freq_hours: int = 1,
    ) -> List[datetime]:
        """Generate a list of hourly timestamps for the backfill period.

        Args:
            start: Start datetime (defaults to N years ago).
            end: End datetime (defaults to now).
            freq_hours: Frequency in hours between data points.

        Returns:
            List[datetime]: Ordered list of UTC timestamps.
        """
        if end is None:
            end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        if start is None:
            start = end - timedelta(days=365 * self.settings.backfill_years)

        timestamps: List[datetime] = []
        current = start
        while current <= end:
            timestamps.append(current)
            current += timedelta(hours=freq_hours)

        logger.info(
            "Generated %d timestamps from %s to %s",
            len(timestamps), start.isoformat(), end.isoformat(),
        )
        return timestamps

    def _save_checkpoint(self, last_processed_idx: int, total: int) -> None:
        """Save backfill progress checkpoint for resume capability.

        Args:
            last_processed_idx: Index of the last successfully processed batch.
            total: Total number of timestamps to process.
        """
        checkpoint = {
            "last_processed_idx": last_processed_idx,
            "total": total,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        self._checkpoint_path.write_text(json.dumps(checkpoint, indent=2))
        logger.debug("Checkpoint saved: %d/%d", last_processed_idx, total)

    def _load_checkpoint(self) -> Optional[int]:
        """Load the last checkpoint index, if available.

        Returns:
            Optional[int]: Last processed index, or None if no checkpoint.
        """
        if self._checkpoint_path.exists():
            try:
                data = json.loads(self._checkpoint_path.read_text())
                idx = data.get("last_processed_idx", 0)
                logger.info("Resuming from checkpoint: index %d", idx)
                return idx
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Invalid checkpoint file: %s", e)
        return None

    def _clear_checkpoint(self) -> None:
        """Remove checkpoint file after successful completion."""
        if self._checkpoint_path.exists():
            self._checkpoint_path.unlink()
            logger.info("Backfill checkpoint cleared")

    def run(
        self,
        years: Optional[int] = None,
        batch_size: Optional[int] = None,
        output_path: Optional[Path] = None,
        resume: bool = True,
    ) -> pd.DataFrame:
        """Execute the full backfill pipeline.

        Generates synthetic historical data, applies feature engineering,
        and saves results in batches. Supports resume from checkpoint.

        Args:
            years: Number of years to backfill (overrides settings).
            batch_size: Rows per batch (overrides settings).
            output_path: Path to save final CSV (defaults to data_dir).
            resume: Whether to resume from last checkpoint.

        Returns:
            pd.DataFrame: Complete backfilled feature DataFrame.
        """
        if years is not None:
            self.settings.backfill_years = years
        if batch_size is None:
            batch_size = self.settings.backfill_batch_size
        if output_path is None:
            output_path = self.settings.data_dir / "backfill_features.csv"

        timestamps = self.generate_timestamps()
        total = len(timestamps)

        # ── Resume from checkpoint ──
        start_idx = 0
        if resume:
            checkpoint = self._load_checkpoint()
            if checkpoint is not None:
                start_idx = checkpoint

        logger.info(
            "Starting backfill: %d timestamps, batch_size=%d, starting at idx=%d",
            total, batch_size, start_idx,
        )

        all_dfs: List[pd.DataFrame] = []

        for batch_start in range(start_idx, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch_timestamps = timestamps[batch_start:batch_end]

            logger.info(
                "Processing batch %d-%d / %d (%.1f%%)",
                batch_start, batch_end, total,
                100 * batch_end / total,
            )

            # ── Generate synthetic payloads ──
            payloads: List[RawDataPayload] = []
            for ts in batch_timestamps:
                payload = self.generator.generate_for_timestamp(ts)
                payloads.append(payload)

            # ── Apply feature engineering ──
            batch_df = self.engineer.transform_batch(payloads)
            batch_df = self.engineer.impute_missing_lags(batch_df)
            all_dfs.append(batch_df)

            # ── Save checkpoint ──
            self._save_checkpoint(batch_end, total)

            logger.info(
                "Batch complete: %d rows (cumulative: %d)",
                len(batch_df), sum(len(d) for d in all_dfs),
            )

        # ── Concatenate all batches ──
        if all_dfs:
            final_df = pd.concat(all_dfs, ignore_index=True)
        else:
            final_df = pd.DataFrame()

        # ── Save to CSV ──
        final_df.to_csv(output_path, index=False)
        logger.info(
            "Backfill complete: %d rows × %d cols → %s",
            len(final_df), len(final_df.columns), output_path,
        )

        # ── EDA Summary Statistics ──
        self._log_eda_summary(final_df)

        self._clear_checkpoint()
        return final_df

    def _log_eda_summary(self, df: pd.DataFrame) -> None:
        """Log exploratory data analysis summary statistics.

        Prints key distribution statistics for the backfilled dataset
        to facilitate initial data exploration.

        Args:
            df: The backfilled feature DataFrame.
        """
        if df.empty:
            logger.warning("Empty DataFrame — no EDA summary available")
            return

        logger.info("=" * 60)
        logger.info("BACKFILL EDA SUMMARY")
        logger.info("=" * 60)
        logger.info("Shape: %d rows × %d columns", *df.shape)

        if "aqi_value" in df.columns:
            aqi = df["aqi_value"].dropna()
            logger.info(
                "AQI Distribution: mean=%.1f, std=%.1f, min=%.1f, max=%.1f",
                aqi.mean(), aqi.std(), aqi.min(), aqi.max(),
            )
            # AQI category distribution
            categories = {
                "Good (0-50)": ((aqi >= 0) & (aqi <= 50)).sum(),
                "Moderate (51-100)": ((aqi > 50) & (aqi <= 100)).sum(),
                "Unhealthy-Sensitive (101-150)": ((aqi > 100) & (aqi <= 150)).sum(),
                "Unhealthy (151-200)": ((aqi > 150) & (aqi <= 200)).sum(),
                "Very Unhealthy (201-300)": ((aqi > 200) & (aqi <= 300)).sum(),
                "Hazardous (301+)": (aqi > 300).sum(),
            }
            for cat, count in categories.items():
                pct = 100 * count / len(aqi) if len(aqi) > 0 else 0
                logger.info("  %s: %d (%.1f%%)", cat, count, pct)

        # Missing values report
        missing = df.isnull().sum()
        cols_with_missing = missing[missing > 0]
        if not cols_with_missing.empty:
            logger.info("Columns with missing values:")
            for col, count in cols_with_missing.items():
                logger.info("  %s: %d (%.1f%%)", col, count, 100 * count / len(df))

        logger.info("=" * 60)


# ──────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point for running the backfill pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="AQI Data Backfill Pipeline")
    parser.add_argument("--years", type=int, default=None, help="Years to backfill")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh")
    args = parser.parse_args()

    output = Path(args.output) if args.output else None

    pipeline = BackfillPipeline()
    df = pipeline.run(
        years=args.years,
        batch_size=args.batch_size,
        output_path=output,
        resume=not args.no_resume,
    )
    print(f"\nBackfill complete: {len(df)} rows saved.")


if __name__ == "__main__":
    main()
