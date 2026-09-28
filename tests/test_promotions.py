"""Unit tests for promotion simulation and Break-Even Lift validation."""

import pytest
from src.analytics.promotion_simulator import PromotionScenario, CampaignSimulator


def test_break_even_lift_exact_calculation():
    """Valida la fórmula de Break-Even Lift: Lift = d / (M0 - d)."""
    # M0 = (100 - 60) / 100 = 0.40 (40%)
    # d = 0.20 (20%)
    # Lift_BE = 0.20 / (0.40 - 0.20) = 1.0 -> 100.0%
    scenario = PromotionScenario(
        sku="IRN-BAR-TEST",
        current_price=100.0,
        current_volume=100,
        unit_cogs=60.0,
        proposed_discount_pct=0.20,
        price_elasticity=-2.5,  # Expected lift = |-2.5| * 0.20 = 50%
    )
    result = scenario.evaluate()
    assert result["break_even_volume_lift_pct"] == 100.0
    assert result["expected_volume_lift_pct"] == 50.0
    # Expected lift (50%) < Break-even lift (100%) -> Destroys profit!
    assert not result["is_viable"]
    assert "RECHAZADA" in result["recommendation"]


def test_viable_elastic_promotion_approval():
    """Validates promotion approval when expected lift exceeds break-even lift."""
    # M0 = (100 - 50) / 100 = 0.50 (50%)
    # d = 0.10 (10%)
    # Lift_BE = 0.10 / (0.50 - 0.10) = 25.0%
    # Elasticity = -3.5 -> Expected lift = |-3.5| * 0.10 = 35% > 25% -> Incremental profit!
    scenario = PromotionScenario(
        sku="IRN-ACC-TEST",
        current_price=100.0,
        current_volume=200,
        unit_cogs=50.0,
        proposed_discount_pct=0.10,
        price_elasticity=-3.5,
    )
    result = scenario.evaluate()
    assert result["break_even_volume_lift_pct"] == 25.0
    assert result["expected_volume_lift_pct"] == 35.0
    assert result["is_viable"]
    assert result["incremental_profit_usd"] > 0
    assert result["recommendation"] == "APROBADA"


def test_destructive_discount_veto():
    """Validates that a discount higher than gross margin is unconditionally rejected."""
    scenario = PromotionScenario(
        sku="IRN-POW-TEST",
        current_price=100.0,
        current_volume=50,
        unit_cogs=80.0,  # M0 = 20%
        proposed_discount_pct=0.25,  # 25% discount > 20% margin
        price_elasticity=-2.0,
    )
    result = scenario.evaluate()
    assert not result["is_viable"]
    assert "Descuento >= Margen Bruto" in result["recommendation"]


def test_campaign_portfolio_orchestrator():
    """Validates multi-SKU campaign simulation with shared marketing ad spend."""
    scenarios = [
        PromotionScenario("SKU-1", 100.0, 100, 50.0, 0.10, -3.5),  # Viable
        PromotionScenario("SKU-2", 100.0, 100, 80.0, 0.25, -2.0),  # Not viable
    ]
    camp = CampaignSimulator.simulate_campaign(scenarios, total_marketing_budget_usd=100.0)
    assert camp["summary"]["total_skus_evaluated"] == 2
    assert camp["summary"]["skus_approved"] == 1
    assert camp["summary"]["skus_rejected"] == 1
    assert "sku_details" in camp
