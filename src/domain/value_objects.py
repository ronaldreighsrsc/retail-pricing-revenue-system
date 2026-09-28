"""Domain value objects for retail pricing and revenue optimization."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class Currency(str, Enum):
    USD = "USD"
    CLP = "CLP"
    MXN = "MXN"
    ARS = "ARS"


class Country(str, Enum):
    CL = "CL"
    MX = "MX"
    AR = "AR"


class Channel(str, Enum):
    D2C_SHOPIFY = "D2C_SHOPIFY"
    MELI_FULL = "MELI_FULL"
    B2B_GYM = "B2B_GYM"


class TierSegment(str, Enum):
    GOOD = "Good"
    BETTER = "Better"
    BEST = "Best"


class LifecycleStatus(str, Enum):
    LAUNCH = "Launch"
    ACTIVE = "Active"
    HARVEST = "Harvest"
    CLEARANCE = "Clearance"
    DISCONTINUED = "Discontinued"


class CompetitiveTier(str, Enum):
    OVERPRICED = "Overpriced (High Risk)"
    HEALTHY_PREMIUM = "Healthy Premium"
    COMPETITIVE_PARITY = "Competitive Parity"
    UNDERPRICED = "Underpriced (Margin Leakage)"
    SLIGHTLY_DISCOUNTED = "Slightly Discounted"


# Mapping Country to default local Currency
COUNTRY_TO_CURRENCY: Dict[str, str] = {
    Country.CL.value: Currency.CLP.value,
    Country.MX.value: Currency.MXN.value,
    Country.AR.value: Currency.ARS.value,
}

# Standard benchmark FX rates (Local currency units per 1 USD)
FX_RATES_TO_USD: Dict[str, float] = {
    "USD": 1.0,
    "CLP": 940.0,
    "MXN": 18.5,
    "ARS": 1150.0,
    "CL": 940.0,
    "MX": 18.5,
    "AR": 1150.0,
}

# Standard marketplace commission percentages
CHANNEL_COMMISSION_RATES: Dict[str, float] = {
    Channel.D2C_SHOPIFY.value: 0.025,  # Payment gateway ~ 2.5%
    Channel.MELI_FULL.value: 0.140,    # Marketplace commission ~ 14.0%
    Channel.B2B_GYM.value: 0.010,      # Invoicing / processing ~ 1.0%
}


@dataclass(frozen=True)
class MarginMetrics:
    gross_revenue_usd: float
    cogs_usd: float
    shipping_cost_usd: float
    channel_fees_usd: float
    net_margin_usd: float
    margin_percentage: float

    @classmethod
    def calculate(
        cls,
        selling_price_usd: float,
        cogs_usd: float,
        shipping_cost_usd: float,
        channel_fee_usd: float,
        units: int = 1,
    ) -> "MarginMetrics":
        total_rev = selling_price_usd * units
        total_cogs = cogs_usd * units
        total_shipping = shipping_cost_usd * units
        total_fees = channel_fee_usd * units
        net_margin = total_rev - total_cogs - total_shipping - total_fees
        margin_pct = (net_margin / total_rev * 100.0) if total_rev > 0 else 0.0
        return cls(
            gross_revenue_usd=round(total_rev, 2),
            cogs_usd=round(total_cogs, 2),
            shipping_cost_usd=round(total_shipping, 2),
            channel_fees_usd=round(total_fees, 2),
            net_margin_usd=round(net_margin, 2),
            margin_percentage=round(margin_pct, 2),
        )


@dataclass(frozen=True)
class PriceRange:
    min_floor_price: float
    base_list_price: float
    max_ceiling_price: float
    recommended_price: float
