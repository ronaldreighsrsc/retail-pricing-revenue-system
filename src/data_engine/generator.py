"""Synthetic data generator for retail pricing and multi-country e-commerce portfolio."""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

from src.domain.value_objects import (
    Currency,
    Country,
    Channel,
    TierSegment,
    LifecycleStatus,
    FX_RATES_TO_USD,
    CHANNEL_COMMISSION_RATES,
)


class RetailDataGenerator:
    """Generates a realistic 350-SKU fitness equipment catalog and 24-month multi-country transaction history."""

    CATEGORIES = {
        "Fuerza Libre": [
            ("Barras Olímpicas", ["Cerakote 20kg", "Hard Chrome 20kg", "Women 15kg", "Trap Bar Hex", "EZ Curl Bar", "Shorty 10kg"], (45.0, 180.0), (10.0, 25.0)),
            ("Discos Bumper", ["Hi-Temp Recycled 5kg", "Hi-Temp 10kg", "Hi-Temp 15kg", "Hi-Temp 20kg", "Hi-Temp 25kg", "Competition Urethane 10kg", "Competition Urethane 20kg", "Fractional Plate Set"], (12.0, 140.0), (5.0, 25.0)),
            ("Mancuernas", ["Hex Dumbbell 2.5kg", "Hex Dumbbell 5kg", "Hex Dumbbell 10kg", "Hex Dumbbell 15kg", "Hex Dumbbell 20kg", "Hex Dumbbell 25kg", "Hex Dumbbell 30kg", "Round Urethane Dumbbell 20kg"], (8.0, 110.0), (2.5, 35.0)),
            ("Kettlebells", ["Competition Russian 8kg", "Competition Russian 12kg", "Competition Russian 16kg", "Competition Russian 20kg", "Competition Russian 24kg", "Competition Russian 32kg", "Cast Iron Powder Coat 16kg"], (15.0, 95.0), (8.0, 32.0)),
        ],
        "Racks & Estructuras": [
            ("Power Racks", ["Commercial Monster Rack 3x3", "Standard Power Cage 75x75", "Half Rack Commercial", "Wall-Mount Folding Rack"], (250.0, 1100.0), (75.0, 180.0)),
            ("Squat Stands", ["Independent Squat Stand Pro", "Yoke Squat Stand Heavy", "Compact Stand Home Gym"], (110.0, 380.0), (35.0, 65.0)),
            ("Bancos", ["Flat Competition Bench", "Adjustable Incline/Decline FID Bench", "Zero Gap Commercial Bench", "Foldable Utility Bench"], (65.0, 320.0), (18.0, 48.0)),
            ("Accesorios Racks", ["Sandwich J-Cups Pair", "Spotter Safety Arms", "Dip Station Attachment", "Jammer Arms Set", "Landmine Heavy Attachment"], (25.0, 190.0), (4.0, 28.0)),
        ],
        "Cardio": [
            ("Air Bikes", ["Commercial Wind Resistance Air Bike", "Pro Heavy-Duty Fan Bike", "Compact Air Bike"], (290.0, 750.0), (48.0, 65.0)),
            ("Remos", ["Air Rower with PM5 Performance Monitor", "Magnetic Resistance Water Rower", "Commercial Foldable Rower"], (320.0, 890.0), (38.0, 52.0)),
            ("Ski Trainers", ["Wall Mount Ski Ergometer", "Floor Stand Platform Ski Erg"], (340.0, 850.0), (42.0, 58.0)),
            ("Cintas Curvas", ["Non-Motorized Commercial Curved Treadmill", "Pro Runner Self-Powered Slat Treadmill"], (850.0, 2400.0), (120.0, 165.0)),
        ],
        "Peso Integrado": [
            ("Poleas Funcionales", ["Dual Adjustable Pulley 90kg x 2", "Functional Trainer Compact", "Cable Crossover Commercial"], (650.0, 2200.0), (140.0, 290.0)),
            ("Máquinas de Placas", ["Lat Pulldown / Low Row Combo 100kg", "Leg Extension / Leg Curl Combo", "Seated Chest Press 80kg", "Leg Press Hack Squat 45deg"], (580.0, 1950.0), (130.0, 310.0)),
            ("Smith Machines", ["Commercial Counter-Balanced Smith Machine", "Multi-Power 3D Smith Machine"], (620.0, 1800.0), (115.0, 230.0)),
        ],
        "Accesorios & Movilidad": [
            ("Bandas y Agarre", ["Loop Resistance Bands 5-Pack", "Leather Lifting Straps", "Gym Chalk Block 8-Pack", "Barbell Collars Aluminum", "Weightlifting Belt 10mm"], (5.0, 35.0), (0.4, 2.5)),
            ("Pisos y Protección", ["Rubber Floor Roll 8mm (10m2)", "High Impact Interlocking Tile 25mm 1x1m", "Drop Pads Noise Dampening Pair"], (35.0, 160.0), (12.0, 45.0)),
            ("Balones & Plyo", ["Slam Ball 5kg", "Slam Ball 10kg", "Slam Ball 15kg", "Foam 3-in-1 Soft Plyo Box", "Wood CNC Plyo Box", "Wall Ball 9kg"], (15.0, 95.0), (5.0, 22.0)),
        ],
    }

    COMPETITORS = ["Spartan", "Rogue", "SDmed", "Tayga"]

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

    def generate_products(self, target_sku_count: int = 350) -> pd.DataFrame:
        """Generates a catalog of target_sku_count products with realistic retail attributes."""
        products = []
        sku_counter = 1

        # Flatten subcategories
        flat_catalog = []
        for cat, subcats in self.CATEGORIES.items():
            for subcat, items, cogs_range, weight_range in subcats:
                for item in items:
                    flat_catalog.append((cat, subcat, item, cogs_range, weight_range))

        while len(products) < target_sku_count:
            idx = (sku_counter - 1) % len(flat_catalog)
            cat, subcat, item_name, cogs_range, weight_range = flat_catalog[idx]
            
            # Variant tier
            tier = random.choices(
                [TierSegment.GOOD.value, TierSegment.BETTER.value, TierSegment.BEST.value],
                weights=[0.35, 0.45, 0.20],
            )[0]
            
            tier_mult = 1.0 if tier == TierSegment.GOOD.value else (1.35 if tier == TierSegment.BETTER.value else 1.85)
            cogs = round(random.uniform(*cogs_range) * (0.85 + 0.3 * (tier_mult - 1)), 2)
            weight = round(random.uniform(*weight_range), 1)
            
            # Markup based on tier: Good (40-50%), Better (50-65%), Best (65-85%)
            markup = random.uniform(0.40, 0.55) if tier == TierSegment.GOOD.value else (
                random.uniform(0.55, 0.70) if tier == TierSegment.BETTER.value else random.uniform(0.70, 0.95)
            )
            base_price = round(cogs * (1.0 + markup), 2)
            
            # Lifecycle status
            lifecycle = random.choices(
                [
                    LifecycleStatus.ACTIVE.value,
                    LifecycleStatus.LAUNCH.value,
                    LifecycleStatus.HARVEST.value,
                    LifecycleStatus.CLEARANCE.value,
                ],
                weights=[0.70, 0.12, 0.10, 0.08],
            )[0]
            
            # Slower moving items for clearance
            if lifecycle == LifecycleStatus.CLEARANCE.value:
                stock = random.randint(80, 450)
            else:
                stock = random.randint(15, 250)

            # Underlying price elasticity parameter for synthetic ground truth (-0.6 to -2.8)
            # Heavy equipment or high-end Best tends to be more inelastic (-0.7 to -1.2)
            # Accessories or Good tier tend to be more elastic (-1.6 to -2.8)
            if cat in ["Accesorios & Movilidad", "Fuerza Libre"] and tier == TierSegment.GOOD.value:
                true_elasticity = round(random.uniform(-2.8, -1.6), 2)
            elif tier == TierSegment.BEST.value or cat in ["Peso Integrado", "Cardio"]:
                true_elasticity = round(random.uniform(-1.2, -0.6), 2)
            else:
                true_elasticity = round(random.uniform(-1.7, -1.1), 2)

            sku_prefix = f"IRN-{cat[:3].upper()}-{subcat[:3].upper()}"
            sku = f"{sku_prefix}-{sku_counter:04d}"
            name = f"IRONSIDE {item_name} [{tier.upper()}]"

            products.append({
                "sku": sku,
                "name": name,
                "category": cat,
                "sub_category": subcat,
                "tier_segment": tier,
                "cogs_usd": cogs,
                "shipping_weight_kg": weight,
                "lifecycle_status": lifecycle,
                "stock_on_hand": stock,
                "base_price_usd": base_price,
                "true_elasticity": true_elasticity,
            })
            sku_counter += 1

        df_products = pd.DataFrame(products)
        return df_products

    def generate_competitor_scrap(self, df_products: pd.DataFrame) -> pd.DataFrame:
        """Generates realistic competitor market quotes for each SKU."""
        quotes = []
        today = datetime(2026, 9, 28)
        
        for _, prod in df_products.iterrows():
            sku = prod["sku"]
            base_usd = prod["base_price_usd"]
            tier = prod["tier_segment"]
            
            # Competitors track a subset of products
            sampled_competitors = random.sample(self.COMPETITORS, k=random.randint(2, 4))
            
            for comp in sampled_competitors:
                # Competitor pricing spread relative to ours
                # Rogue: tends to be 10-25% more expensive (premium benchmark)
                # Tayga / SDmed: tends to be 5-15% cheaper (budget pressure)
                # Spartan: close to par (+/- 8%)
                if comp == "Rogue":
                    ratio = random.uniform(1.08, 1.28)
                elif comp in ["Tayga", "SDmed"]:
                    ratio = random.uniform(0.84, 0.98)
                else:
                    ratio = random.uniform(0.94, 1.07)
                    
                comp_price_usd = round(base_usd * ratio, 2)
                stock_status = "In Stock" if random.random() < 0.90 else "Out of Stock"
                promo_flag = 1 if random.random() < 0.18 else 0
                if promo_flag:
                    comp_price_usd = round(comp_price_usd * random.uniform(0.85, 0.92), 2)
                
                # Multi-country localized prices
                for country_code in ["CL", "MX", "AR"]:
                    fx = FX_RATES_TO_USD.get(country_code, 1.0)
                    comp_price_local = round(comp_price_usd * fx, 0 if country_code != "MX" else 2)
                    
                    quotes.append({
                        "date": today.strftime("%Y-%m-%d"),
                        "sku": sku,
                        "country_id": country_code,
                        "competitor_brand": comp,
                        "competitor_price_local": comp_price_local,
                        "competitor_price_usd": comp_price_usd,
                        "stock_status": stock_status,
                        "promotion_flag": promo_flag,
                    })

        return pd.DataFrame(quotes)

    def generate_transactions(
        self,
        df_products: pd.DataFrame,
        start_date: str = "2024-10-01",
        end_date: str = "2026-09-28",
    ) -> pd.DataFrame:
        """Generates 24 months of multi-channel, multi-country transactional records with realistic demand dynamics."""
        transactions = []
        dt_start = datetime.strptime(start_date, "%Y-%m-%d")
        dt_end = datetime.strptime(end_date, "%Y-%m-%d")
        total_weeks = int((dt_end - dt_start).days / 7)
        
        tx_id_seq = 1

        # Precompute base metrics per SKU
        sku_lookup = df_products.set_index("sku").to_dict("index")

        for week_idx in range(total_weeks):
            current_week_dt = dt_start + timedelta(weeks=week_idx)
            date_str = current_week_dt.strftime("%Y-%m-%d")
            month = current_week_dt.month
            
            # Seasonal market multipliers
            # May: CyberDay Chile / Hot Sale Mexico
            # October: CyberDay 2
            # November: Black Friday
            # January: New Year Fitness resolution
            season_mult = 1.0
            is_cyber_season = False
            if month == 5:
                season_mult = 1.65
                is_cyber_season = True
            elif month == 10:
                season_mult = 1.45
                is_cyber_season = True
            elif month == 11:
                season_mult = 1.85
                is_cyber_season = True
            elif month == 1:
                season_mult = 1.35
            elif month in [7, 8]:
                season_mult = 0.85  # Winter lull

            # Sample active transactions for this week
            # We sample ~60-80% of SKUs per week to maintain realistic frequency
            sampled_skus = random.sample(list(sku_lookup.keys()), k=int(len(sku_lookup) * 0.70))

            for sku in sampled_skus:
                prod = sku_lookup[sku]
                base_usd = prod["base_price_usd"]
                cogs_usd = prod["cogs_usd"]
                weight_kg = prod["shipping_weight_kg"]
                true_eps = prod["true_elasticity"]

                # Countries distribution: CL (50%), MX (35%), AR (15%)
                country = random.choices(["CL", "MX", "AR"], weights=[0.50, 0.35, 0.15])[0]
                channel = random.choices(
                    [Channel.D2C_SHOPIFY.value, Channel.MELI_FULL.value, Channel.B2B_GYM.value],
                    weights=[0.45, 0.40, 0.15],
                )[0]

                fx = FX_RATES_TO_USD[country]
                list_price_local = round(base_usd * fx, 0 if country != "MX" else 2)

                # Promotion strategy
                is_promo = 1 if (is_cyber_season and random.random() < 0.65) or (random.random() < 0.12) else 0
                if is_promo:
                    discount_pct = random.choice([0.10, 0.15, 0.20, 0.25, 0.30])
                else:
                    discount_pct = 0.0

                net_price_local = round(list_price_local * (1.0 - discount_pct), 0 if country != "MX" else 2)
                net_price_usd = net_price_local / fx

                # Econometric quantity generated via true demand function:
                # ln(Q) = alpha + beta * ln(P/P_base) + gamma * promo + seasonal + noise
                price_ratio = (net_price_usd / base_usd) if base_usd > 0 else 1.0
                base_volume = max(2.0, (1200.0 / (cogs_usd + 20.0)))  # cheaper goods sell higher base volume
                
                # Demand equation
                log_q = (
                    np.log(base_volume)
                    + (true_eps * np.log(price_ratio))
                    + (0.35 * is_promo)
                    + np.log(season_mult)
                    + np.random.normal(0, 0.18)
                )
                units_sold = max(1, int(np.exp(log_q)))

                # Channel adjustments: B2B sells larger batches but fewer orders
                if channel == Channel.B2B_GYM.value:
                    units_sold = int(units_sold * random.uniform(2.5, 5.0))

                net_revenue_usd = round(net_price_usd * units_sold, 2)
                
                # Cost components:
                # Channel fee
                fee_rate = CHANNEL_COMMISSION_RATES[channel]
                channel_fee_usd = round(net_revenue_usd * fee_rate, 2)
                
                # Shipping cost per kg absorbed by seller
                shipping_rate_per_kg = 1.10 if country == "CL" else (1.40 if country == "MX" else 1.70)
                shipping_cost_usd = round(max(3.5, weight_kg * shipping_rate_per_kg * units_sold * 0.4), 2)
                
                # Gross margin
                total_cogs_usd = cogs_usd * units_sold
                gross_margin_usd = round(net_revenue_usd - total_cogs_usd - channel_fee_usd - shipping_cost_usd, 2)

                transactions.append({
                    "transaction_id": f"TX-{country}-{tx_id_seq:07d}",
                    "date": date_str,
                    "sku": sku,
                    "country_id": country,
                    "channel_id": channel,
                    "units_sold": units_sold,
                    "list_price_local": list_price_local,
                    "discount_pct": discount_pct,
                    "net_price_local": net_price_local,
                    "net_revenue_usd": net_revenue_usd,
                    "channel_fee_usd": channel_fee_usd,
                    "shipping_cost_usd": shipping_cost_usd,
                    "gross_margin_usd": gross_margin_usd,
                    "is_promo": is_promo,
                })
                tx_id_seq += 1

        df_tx = pd.DataFrame(transactions)
        return df_tx
