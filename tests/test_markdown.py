"""Unit tests for markdown liquidation and slow-moving stock optimization."""

import pytest
from src.analytics.markdown_optimizer import MarkdownOptimizer, MarkdownStep


def test_markdown_schedule_monotonicity_and_clearance():
    """Validates that discount percentages increase monotonically and inventory decreases."""
    schedule = MarkdownOptimizer.generate_schedule(
        current_stock=100,
        base_price=200.0,
        unit_cogs=100.0,
        weeks_horizon=6,
        elasticity=-1.8,
    )
    assert len(schedule) > 0
    assert len(schedule) <= 6

    prev_discount = 0.0
    prev_stock = 100
    for step in schedule:
        assert isinstance(step, MarkdownStep)
        # Monotonically increasing discounts
        assert step.discount_pct > prev_discount
        prev_discount = step.discount_pct

        # Non-negative remaining stock and monotonic decrease
        assert step.remaining_stock >= 0
        assert step.remaining_stock < prev_stock
        prev_stock = step.remaining_stock

        # Recommended price must be lower than base price
        assert step.recommended_price < 200.0
        assert step.cash_recovered_usd > 0


def test_markdown_summary_metrics():
    """Validates clearance performance summary calculations."""
    schedule = MarkdownOptimizer.generate_schedule(
        current_stock=50,
        base_price=100.0,
        unit_cogs=60.0,
        weeks_horizon=4,
        elasticity=-2.0,
    )
    summary = MarkdownOptimizer.summarize_clearance_plan(schedule, initial_stock=50, base_price=100.0)
    assert summary["initial_stock_units"] == 50
    assert summary["liquidated_units"] > 0
    assert summary["total_cash_recovered_usd"] > 0
    assert 0.0 <= summary["effective_recovery_rate_pct"] <= 100.0


def test_calculate_dio():
    """Validates Days of Inventory Outstanding (DIO) logic."""
    # 100 units on hand, 365 units sold annually -> DIO = 100 days
    dio = MarkdownOptimizer.calculate_dio(stock_on_hand=100, cogs_usd=50.0, annual_units_sold=365)
    assert dio == 100.0

    # Zero sales -> fallback 999.0
    dio_zero = MarkdownOptimizer.calculate_dio(stock_on_hand=50, cogs_usd=50.0, annual_units_sold=0)
    assert dio_zero == 999.0
