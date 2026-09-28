"""Unit tests for domain value objects and core entities."""

import pytest
from src.domain.value_objects import MarginMetrics, PriceRange, Currency, Country, Channel
from src.domain.models import Product, Transaction, CompetitorQuote


def test_margin_metrics_calculation():
    """Validates exact calculation of gross margin and margin percentage."""
    # Selling Price = $100, COGS = $50, Shipping = $10, Channel Fee = $5
    # Total revenue = $100, Net margin = $35, Margin % = 35%
    metrics = MarginMetrics.calculate(
        selling_price_usd=100.0,
        cogs_usd=50.0,
        shipping_cost_usd=10.0,
        channel_fee_usd=5.0,
        units=2,
    )
    assert metrics.gross_revenue_usd == 200.0
    assert metrics.cogs_usd == 100.0
    assert metrics.shipping_cost_usd == 20.0
    assert metrics.channel_fees_usd == 10.0
    assert metrics.net_margin_usd == 70.0
    assert metrics.margin_percentage == 35.0


def test_product_dataclass_initialization():
    """Ensures Product model holds retail attributes accurately."""
    product = Product(
        sku="IRN-BAR-TEST-001",
        name="IRONSIDE Cerakote Barbell 20kg",
        category="Fuerza Libre",
        sub_category="Barras Olímpicas",
        tier_segment="Best",
        cogs_usd=90.0,
        shipping_weight_kg=22.0,
        lifecycle_status="Active",
        stock_on_hand=50,
        base_price_usd=180.0,
    )
    assert product.sku == "IRN-BAR-TEST-001"
    assert product.base_price_usd == 180.0
    assert product.tier_segment == "Best"
