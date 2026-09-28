"""Competitive benchmark tracker and Price Indexing (PI) analytics."""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from src.domain.value_objects import CompetitiveTier


class CompetitiveTracker:
    """Calculates and audits the Price Index (PI) against direct market competitors."""

    @staticmethod
    def calculate_price_index(df_prices: pd.DataFrame) -> pd.DataFrame:
        """Calculates Price Index and assigns strategic competitive tiers.
        
        Args:
            df_prices: DataFrame containing at least:
                ['sku', 'our_price', 'competitor_price']
                Optional: ['competitor_brand', 'category', 'country_id']
        """
        df = df_prices.copy()
        
        # Ensure positive competitor prices
        valid_mask = (df["competitor_price"] > 0) & (df["our_price"] > 0)
        df = df[valid_mask].copy()

        df["price_index"] = ((df["our_price"] / df["competitor_price"]) * 100.0).round(2)

        # Tier classification according to executive matrix
        conditions = [
            (df["price_index"] > 115.0),
            (df["price_index"] >= 105.0) & (df["price_index"] <= 115.0),
            (df["price_index"] >= 98.0) & (df["price_index"] < 105.0),
            (df["price_index"] < 95.0),
        ]
        
        choices = [
            CompetitiveTier.OVERPRICED.value,
            CompetitiveTier.HEALTHY_PREMIUM.value,
            CompetitiveTier.COMPETITIVE_PARITY.value,
            CompetitiveTier.UNDERPRICED.value,
        ]
        
        # Use np.select for vectorized classification
        df["competitive_tier"] = np.select(conditions, choices, default=CompetitiveTier.SLIGHTLY_DISCOUNTED.value)

        # Strategic Action Mapping
        action_map = {
            CompetitiveTier.OVERPRICED.value: "Revisar justificación de marca o aplicar descuento táctico para frenar fuga de demanda.",
            CompetitiveTier.HEALTHY_PREMIUM.value: "Sostener margen. Explotar atributos de servicio, disponibilidad inmediata y garantía extendida.",
            CompetitiveTier.COMPETITIVE_PARITY.value: "Paridad de mercado. Monitorear disponibilidad de inventario de competidores.",
            CompetitiveTier.UNDERPRICED.value: "Oportunidad de captura: SUBIR PRECIO de inmediato para erradicar fuga de margen.",
            CompetitiveTier.SLIGHTLY_DISCOUNTED.value: "Leve descuento. Mantener salvo que la demanda requiera paridad estricta.",
        }
        df["pricing_action"] = df["competitive_tier"].map(action_map)

        return df

    @staticmethod
    def summarize_by_brand(df_indexed: pd.DataFrame) -> pd.DataFrame:
        """Aggregates average Price Index and position by competitor brand."""
        if "competitor_brand" not in df_indexed.columns:
            return pd.DataFrame()

        summary = (
            df_indexed.groupby("competitor_brand")
            .agg(
                tracked_skus=("sku", "nunique"),
                mean_price_index=("price_index", "mean"),
                median_price_index=("price_index", "median"),
                min_price_index=("price_index", "min"),
                max_price_index=("price_index", "max"),
            )
            .reset_index()
        )
        summary["mean_price_index"] = summary["mean_price_index"].round(1)
        summary["median_price_index"] = summary["median_price_index"].round(1)
        return summary

    @staticmethod
    def identify_arbitrage_opportunities(
        df_indexed: pd.DataFrame,
        df_elasticity: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """Flags high-impact margin recovery opportunities:
        SKUs that are Underpriced (PI < 95) and have Inelastic demand (can raise prices safely).
        """
        underpriced = df_indexed[df_indexed["competitive_tier"] == CompetitiveTier.UNDERPRICED.value].copy()
        
        if df_elasticity is not None and not df_elasticity.empty:
            merged = pd.merge(underpriced, df_elasticity[["sku", "elasticity_coefficient", "demand_regime"]], on="sku", how="inner")
            # Filter for inelastic or moderate demand
            merged["priority_score"] = np.where(merged["demand_regime"] == "Inelastic", "ALTA PRIORIDAD (Inelástico)", "MEDIA PRIORIDAD")
            return merged.sort_values(by="price_index", ascending=True)
            
        return underpriced.sort_values(by="price_index", ascending=True)
