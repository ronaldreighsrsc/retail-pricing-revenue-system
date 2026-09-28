"""Smoke and integration tests for dashboard components and data loading."""

import os
import pytest
from src.dashboard.app import get_repository, load_core_data


def test_dashboard_repository_and_data_loading():
    """Validates that dashboard can initialize its data pipeline and query components."""
    repo = get_repository()
    assert repo is not None
    
    prods, comps, monthly, margin_h, slow_m, omni = load_core_data()
    assert not prods.empty
    assert len(prods) == 350
    assert not comps.empty
    assert not monthly.empty
    assert not margin_h.empty
    assert not slow_m.empty
    assert not omni.empty
