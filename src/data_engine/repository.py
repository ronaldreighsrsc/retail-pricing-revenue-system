"""SQLite repository with WAL mode and Parquet optimization for retail pricing analytics."""

import os
import sqlite3
from typing import Any, Dict, List, Optional
import pandas as pd

from src.core.base_repository import BaseRepository


class SQLiteRetailRepository(BaseRepository):
    """Production-grade SQLite data access layer with Write-Ahead Logging (WAL) and indexing."""

    def __init__(self, db_path: str = "data/processed/retail_pricing.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_connection()

    def _init_connection(self) -> None:
        """Configures SQLite connection for high concurrency and performance."""
        with sqlite3.connect(self.db_path) as conn:
            # Enable WAL mode for high read/write throughput
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA foreign_keys=ON;")

    def get_connection(self) -> sqlite3.Connection:
        """Returns a connection instance to the SQLite database."""
        return sqlite3.connect(self.db_path)

    def init_schema(self) -> None:
        """Creates the relational retail pricing schema and performance indexes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Dim Products
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_products (
                sku TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                sub_category TEXT NOT NULL,
                tier_segment TEXT NOT NULL,
                cogs_usd REAL NOT NULL,
                shipping_weight_kg REAL NOT NULL,
                lifecycle_status TEXT NOT NULL,
                stock_on_hand INTEGER NOT NULL,
                base_price_usd REAL NOT NULL,
                true_elasticity REAL
            );
            """)

            # Fct Transactions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS fct_transactions (
                transaction_id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                sku TEXT NOT NULL,
                country_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                units_sold INTEGER NOT NULL,
                list_price_local REAL NOT NULL,
                discount_pct REAL NOT NULL,
                net_price_local REAL NOT NULL,
                net_revenue_usd REAL NOT NULL,
                channel_fee_usd REAL NOT NULL,
                shipping_cost_usd REAL NOT NULL,
                gross_margin_usd REAL NOT NULL,
                is_promo INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (sku) REFERENCES dim_products (sku)
            );
            """)

            # Fct Competitor Scrap
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS fct_competitor_scrap (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                sku TEXT NOT NULL,
                country_id TEXT NOT NULL,
                competitor_brand TEXT NOT NULL,
                competitor_price_local REAL NOT NULL,
                competitor_price_usd REAL NOT NULL,
                stock_status TEXT NOT NULL,
                promotion_flag INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (sku) REFERENCES dim_products (sku)
            );
            """)

            # Strategic Indexes for rapid analytics
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_sku_date ON fct_transactions(sku, date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_country_channel ON fct_transactions(country_id, channel_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_comp_sku_brand ON fct_competitor_scrap(sku, competitor_brand);")
            conn.commit()

    def seed_data(
        self,
        df_products: pd.DataFrame,
        df_transactions: pd.DataFrame,
        df_competitor: pd.DataFrame,
    ) -> None:
        """Populates tables with DataFrames."""
        self.init_schema()
        with sqlite3.connect(self.db_path) as conn:
            df_products.to_sql("dim_products", conn, if_exists="replace", index=False)
            df_transactions.to_sql("fct_transactions", conn, if_exists="replace", index=False)
            df_competitor.to_sql("fct_competitor_scrap", conn, if_exists="replace", index=False)

    def get_products(self) -> pd.DataFrame:
        """Retrieves all products from dim_products."""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query("SELECT * FROM dim_products ORDER BY category, sku;", conn)

    def get_transactions(
        self,
        sku: Optional[str] = None,
        country_id: Optional[str] = None,
        channel_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """Retrieves transactions with optional filters."""
        query = "SELECT * FROM fct_transactions WHERE 1=1"
        params: List[Any] = []
        if sku:
            query += " AND sku = ?"
            params.append(sku)
        if country_id:
            query += " AND country_id = ?"
            params.append(country_id)
        if channel_id:
            query += " AND channel_id = ?"
            params.append(channel_id)
        query += " ORDER BY date ASC;"

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_competitor_quotes(
        self,
        sku: Optional[str] = None,
        country_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """Retrieves competitor quotes with optional filters."""
        query = "SELECT * FROM fct_competitor_scrap WHERE 1=1"
        params: List[Any] = []
        if sku:
            query += " AND sku = ?"
            params.append(sku)
        if country_id:
            query += " AND country_id = ?"
            params.append(country_id)
        query += " ORDER BY date DESC;"

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def execute_query(self, sql_query: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
        """Executes an arbitrary SQL query and returns results as DataFrame."""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(sql_query, conn, params=params or [])

    def export_to_parquet(self, output_dir: str = "data/processed") -> Dict[str, str]:
        """Exports all core tables to Apache Parquet for high-speed columnar analytical caching."""
        os.makedirs(output_dir, exist_ok=True)
        paths = {}
        with sqlite3.connect(self.db_path) as conn:
            for table in ["dim_products", "fct_transactions", "fct_competitor_scrap"]:
                df = pd.read_sql_query(f"SELECT * FROM {table};", conn)
                parquet_path = os.path.join(output_dir, f"{table}.parquet")
                df.to_parquet(parquet_path, index=False)
                paths[table] = parquet_path
        return paths
