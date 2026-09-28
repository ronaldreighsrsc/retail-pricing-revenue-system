"""Unit tests for competitive benchmarking and Price Index (PI) classification."""

import pandas as pd
import pytest
from src.analytics.competitive_tracker import CompetitiveTracker
from src.domain.value_objects import CompetitiveTier


def test_price_index_calculation_and_tier_classification():
    """Validates Price Index formula and action tier assignment."""
    df_prices = pd.DataFrame({
        "sku": ["SKU-OVER", "SKU-PREM", "SKU-PAR", "SKU-UNDER"],
        "our_price": [125.0, 110.0, 100.0, 90.0],
        "competitor_price": [100.0, 100.0, 100.0, 100.0],
        "competitor_brand": ["Spartan", "Rogue", "Tayga", "SDmed"],
    })

    indexed = CompetitiveTracker.calculate_price_index(df_prices)
    
    # SKU-OVER: PI = 125.0 -> Overpriced (>115)
    row_over = indexed[indexed["sku"] == "SKU-OVER"].iloc[0]
    assert row_over["price_index"] == 125.0
    assert row_over["competitive_tier"] == CompetitiveTier.OVERPRICED.value
    assert "revisar" in row_over["pricing_action"].lower()

    # SKU-PREM: PI = 110.0 -> Healthy Premium (105-115)
    row_prem = indexed[indexed["sku"] == "SKU-PREM"].iloc[0]
    assert round(float(row_prem["price_index"]), 1) == 110.0
    assert row_prem["competitive_tier"] == CompetitiveTier.HEALTHY_PREMIUM.value

    # SKU-PAR: PI = 100.0 -> Competitive Parity (98-105)
    row_par = indexed[indexed["sku"] == "SKU-PAR"].iloc[0]
    assert row_par["price_index"] == 100.0
    assert row_par["competitive_tier"] == CompetitiveTier.COMPETITIVE_PARITY.value

    # SKU-UNDER: PI = 90.0 -> Underpriced (<95)
    row_under = indexed[indexed["sku"] == "SKU-UNDER"].iloc[0]
    assert row_under["price_index"] == 90.0
    assert row_under["competitive_tier"] == CompetitiveTier.UNDERPRICED.value
    assert "subir precio" in row_under["pricing_action"].lower()


def test_identify_arbitrage_opportunities():
    """Validates detection of Underpriced SKUs with Inelastic demand."""
    df_indexed = pd.DataFrame({
        "sku": ["SKU-A", "SKU-B"],
        "our_price": [85.0, 110.0],
        "competitor_price": [100.0, 100.0],
        "price_index": [85.0, 110.0],
        "competitive_tier": [CompetitiveTier.UNDERPRICED.value, CompetitiveTier.HEALTHY_PREMIUM.value],
    })

    df_elasticity = pd.DataFrame({
        "sku": ["SKU-A", "SKU-B"],
        "elasticity_coefficient": [-0.8, -2.1],
        "demand_regime": ["Inelastic", "Elastic"],
    })

    opps = CompetitiveTracker.identify_arbitrage_opportunities(df_indexed, df_elasticity)
    assert len(opps) == 1
    assert opps.iloc[0]["sku"] == "SKU-A"
    assert opps.iloc[0]["priority_score"] == "ALTA PRIORIDAD (Inelástico)"
