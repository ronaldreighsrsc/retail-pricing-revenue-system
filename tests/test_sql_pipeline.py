"""Integration tests for analytical SQL queries and database execution."""

import os
import pandas as pd
import pytest
from src.data_engine.repository import SQLiteRetailRepository
from src.reporting.sql_queries import RetailAnalyticsQueries


@pytest.fixture(scope="module")
def seeded_repo():
    """Returns a connected repository from the seeded database or creates a test one."""
    db_path = "data/processed/retail_pricing.db"
    if not os.path.exists(db_path):
        pytest.skip("Database not seeded yet.")
    return SQLiteRetailRepository(db_path)


def test_sql_margin_health_90d(seeded_repo):
    """Validates 90-day margin health analytical query with financial classifications."""
    sql = RetailAnalyticsQueries.get_margin_health_90d()
    df = seeded_repo.execute_query(sql)
    assert not df.empty
    expected_cols = {"sku", "category", "channel_id", "country_id", "revenue_usd", "profit_usd", "margin_percentage", "financial_health_status"}
    assert expected_cols.issubset(set(df.columns))
    # Statuses should conform to design
    valid_statuses = {"CRÍTICO: Margen Insuficiente", "SALUDABLE: En Rango", "ESTRELLA: Alto Retorno"}
    assert set(df["financial_health_status"].unique()).issubset(valid_statuses)


def test_sql_omnichannel_coherence(seeded_repo):
    """Validates omnichannel cross-channel price coherence query."""
    sql = RetailAnalyticsQueries.get_omnichannel_price_coherence()
    df = seeded_repo.execute_query(sql)
    assert not df.empty
    assert "meli_vs_shopify_spread_pct" in df.columns
    assert "channel_arbitrage_risk" in df.columns


def test_sql_slow_moving_inventory(seeded_repo):
    """Validates inventory health and slow-moving DIO query."""
    sql = RetailAnalyticsQueries.get_slow_moving_inventory()
    df = seeded_repo.execute_query(sql)
    assert not df.empty
    assert "estimated_dio" in df.columns
    assert "inventory_health_action" in df.columns


def test_sql_monthly_waterfall(seeded_repo):
    """Validates monthly P&L waterfall query."""
    sql = RetailAnalyticsQueries.get_monthly_financial_waterfall()
    df = seeded_repo.execute_query(sql)
    assert not df.empty
    assert "year_month" in df.columns
    assert "gross_revenue_usd" in df.columns
    assert "gross_margin_pct" in df.columns
    assert len(df) >= 12  # At least 1 year of months
