"""Unit tests for RetailDataGenerator and SQLiteRetailRepository."""

import os
import pandas as pd
import pytest
from src.data_engine.generator import RetailDataGenerator
from src.data_engine.repository import SQLiteRetailRepository


def test_generator_products_and_competitor_quotes():
    """Validates generation of product catalog and competitor quotes."""
    gen = RetailDataGenerator(seed=123)
    df_prods = gen.generate_products(target_sku_count=20)
    assert len(df_prods) == 20
    assert "sku" in df_prods.columns
    assert "cogs_usd" in df_prods.columns
    assert "true_elasticity" in df_prods.columns
    assert df_prods["cogs_usd"].min() > 0

    df_quotes = gen.generate_competitor_scrap(df_prods)
    assert not df_quotes.empty
    assert "competitor_price_usd" in df_quotes.columns
    assert "competitor_brand" in df_quotes.columns


def test_generator_transactions():
    """Validates transactional generation over sample horizon."""
    gen = RetailDataGenerator(seed=123)
    df_prods = gen.generate_products(target_sku_count=10)
    df_tx = gen.generate_transactions(df_prods, start_date="2026-01-01", end_date="2026-03-01")
    assert not df_tx.empty
    assert "net_revenue_usd" in df_tx.columns
    assert "gross_margin_usd" in df_tx.columns
    assert "channel_fee_usd" in df_tx.columns


def test_sqlite_repository_crud(tmp_path):
    """Validates SQLite schema init, data seeding, queries, and parquet export."""
    db_file = str(tmp_path / "test_retail.db")
    repo = SQLiteRetailRepository(db_file)
    
    gen = RetailDataGenerator(seed=999)
    df_prods = gen.generate_products(target_sku_count=15)
    df_quotes = gen.generate_competitor_scrap(df_prods)
    df_tx = gen.generate_transactions(df_prods, start_date="2026-01-01", end_date="2026-02-15")

    repo.seed_data(df_prods, df_tx, df_quotes)

    # Test gets
    prods = repo.get_products()
    assert len(prods) == 15

    tx = repo.get_transactions()
    assert not tx.empty

    quotes = repo.get_competitor_quotes()
    assert not quotes.empty

    # Test parquet export
    pq_dir = str(tmp_path / "parquet")
    paths = repo.export_to_parquet(pq_dir)
    assert len(paths) == 3
    for tbl, p in paths.items():
        assert os.path.exists(p)
