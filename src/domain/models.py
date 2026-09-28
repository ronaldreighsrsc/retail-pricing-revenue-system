"""Domain models and entities representing the retail catalog and commercial transactions."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    sku: str
    name: str
    category: str
    sub_category: str
    tier_segment: str  # Good, Better, Best
    cogs_usd: float
    shipping_weight_kg: float
    lifecycle_status: str  # Launch, Active, Harvest, Clearance, Discontinued
    stock_on_hand: int
    base_price_usd: float


@dataclass
class Transaction:
    transaction_id: str
    date: str  # YYYY-MM-DD
    sku: str
    country_id: str  # CL, MX, AR
    channel_id: str  # D2C_SHOPIFY, MELI_FULL, B2B_GYM
    units_sold: int
    list_price_local: float
    discount_pct: float
    net_price_local: float
    net_revenue_usd: float
    channel_fee_usd: float
    shipping_cost_usd: float
    gross_margin_usd: float
    is_promo: int = 0


@dataclass
class CompetitorQuote:
    date: str  # YYYY-MM-DD
    sku: str
    competitor_brand: str  # Spartan, Rogue, SDmed, Tayga
    competitor_price_local: float
    competitor_price_usd: float
    stock_status: str  # In Stock, Out of Stock
    promotion_flag: int = 0
