"""Unit tests for econometric elasticity estimation and Amoroso-Robinson pricing."""

import numpy as np
import pandas as pd
import pytest
from src.analytics.elasticity_engine import ElasticityEngine, ElasticityResult


def test_elasticity_engine_estimation_accuracy():
    """Validates that log-log regression recovers true known elasticity parameter."""
    engine = ElasticityEngine()
    
    # Generate synthetic observations with true elasticity = -1.8
    true_beta = -1.80
    prices = np.linspace(80.0, 130.0, 50)
    base_q = 500.0
    
    # ln(Q) = ln(base_q) + beta * ln(P/100) + noise
    log_q = np.log(base_q) + (true_beta * np.log(prices / 100.0)) + np.random.normal(0, 0.02, size=len(prices))
    quantities = np.exp(log_q)

    df_sku = pd.DataFrame({
        "sku": "IRN-TEST-001",
        "category": "Fuerza Libre",
        "units_sold": quantities,
        "net_price_local": prices,
    })

    result = engine.fit_sku(df_sku, sku="IRN-TEST-001")
    assert isinstance(result, ElasticityResult)
    # Recovered elasticity should be within +/- 0.15 of true -1.80
    assert abs(result.elasticity_coefficient - true_beta) < 0.15
    assert result.demand_regime == "Elastic"
    assert result.p_value < 0.01
    assert result.r_squared > 0.85


def test_elasticity_insufficient_data_fallback():
    """Validates safe portfolio fallback when SKU has fewer than 5 data points."""
    engine = ElasticityEngine()
    df_sparse = pd.DataFrame({
        "sku": "IRN-NEW-002",
        "category": "Cardio",
        "units_sold": [10, 12],
        "net_price_local": [100.0, 100.0],
    })

    result = engine.fit_sku(df_sparse, sku="IRN-NEW-002")
    assert result.elasticity_coefficient == -1.20
    assert result.r_squared == 0.0
    assert "insuficientes" in result.recommended_action.lower()


def test_optimal_pricing_amoroso_robinson():
    """Validates optimal price calculation under Amoroso-Robinson / Lerner rule."""
    engine = ElasticityEngine()
    cogs = 50.0
    
    # Inelastic demand: bounded markup
    price_inelastic = engine.calculate_optimal_price(cogs_usd=cogs, elasticity=-0.8)
    assert price_inelastic == 80.0  # 60% markup

    # Elastic demand (e.g. -2.0): factor = -2 / (1 - 2) = 2.0 -> P* = 100.0
    price_elastic = engine.calculate_optimal_price(cogs_usd=cogs, elasticity=-2.0)
    assert price_elastic == 100.0
