"""Tests for the feature pipeline module."""

from __future__ import annotations
import pandas as pd

def test_feature_store_manager_init():
    from feature_pipeline.register import FeatureStoreManager
    manager = FeatureStoreManager()
    assert manager is not None
