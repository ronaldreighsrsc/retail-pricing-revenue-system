"""Promotion and campaign simulator with Break-Even Volume Lift analytics and margin protection."""

from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd


@dataclass
class PromotionScenario:
    """Evaluates a proposed discount on a single SKU against econometric demand elasticity."""

    sku: str
    current_price: float
    current_volume: int
    unit_cogs: float
    proposed_discount_pct: float
    price_elasticity: float
    marketing_cost_allocated_usd: float = 0.0

    def evaluate(self) -> Dict[str, any]:
        """Calculates Break-Even Lift, expected lift, financial margins, and commercial recommendation."""
        discount = self.proposed_discount_pct
        current_margin_pct = (self.current_price - self.unit_cogs) / self.current_price if self.current_price > 0 else 0.0

        # 1. Break-Even Volume Lift: Lift_BE = d / (M0 - d)
        if discount >= current_margin_pct:
            break_even_lift = float("inf")
        else:
            break_even_lift = discount / (current_margin_pct - discount)

        # 2. Expected Volume Lift based on Price Elasticity (|epsilon| * d)
        expected_volume_lift = abs(self.price_elasticity) * discount

        # 3. Financial calculations
        promo_price = self.current_price * (1.0 - discount)
        expected_volume = int(round(self.current_volume * (1.0 + expected_volume_lift)))

        baseline_total_revenue = self.current_price * self.current_volume
        promo_total_revenue = promo_price * expected_volume

        baseline_total_margin = (self.current_price - self.unit_cogs) * self.current_volume
        promo_total_margin = ((promo_price - self.unit_cogs) * expected_volume) - self.marketing_cost_allocated_usd

        incremental_profit = promo_total_margin - baseline_total_margin
        is_financially_viable = (incremental_profit > 0) and (discount < current_margin_pct)

        # Recommendation logic
        if discount >= current_margin_pct:
            recommendation = "RECHAZADA (Destruye Margen: Descuento >= Margen Bruto)"
        elif not is_financially_viable:
            recommendation = f"RECHAZADA (Destruye Margen: Lift Esperado {expected_volume_lift*100:.1f}% < Lift Equilibrio {break_even_lift*100:.1f}%)"
        else:
            recommendation = "APROBADA"

        return {
            "sku": self.sku,
            "current_price": round(self.current_price, 2),
            "promo_price": round(promo_price, 2),
            "discount_pct": round(discount * 100, 1),
            "initial_margin_pct": round(current_margin_pct * 100, 1),
            "break_even_volume_lift_pct": round(break_even_lift * 100, 2) if break_even_lift != float("inf") else 9999.0,
            "expected_volume_lift_pct": round(expected_volume_lift * 100, 2),
            "baseline_volume": self.current_volume,
            "projected_volume": expected_volume,
            "baseline_profit_usd": round(baseline_total_margin, 2),
            "expected_profit_usd": round(promo_total_margin, 2),
            "incremental_profit_usd": round(incremental_profit, 2),
            "is_viable": is_financially_viable,
            "recommendation": recommendation,
        }


class CampaignSimulator:
    """Multi-SKU campaign orchestrator (CyberDay, Black Friday, Hot Sale)."""

    @staticmethod
    def simulate_campaign(
        scenarios: List[PromotionScenario],
        total_marketing_budget_usd: float = 0.0,
    ) -> Dict[str, any]:
        """Simulates an entire promotional portfolio under shared marketing investment."""
        results = []
        total_baseline_profit = 0.0
        total_expected_profit = 0.0
        total_baseline_revenue = 0.0
        total_expected_revenue = 0.0

        for sc in scenarios:
            eval_res = sc.evaluate()
            results.append(eval_res)
            total_baseline_profit += eval_res["baseline_profit_usd"]
            total_expected_profit += eval_res["expected_profit_usd"]
            total_baseline_revenue += sc.current_price * sc.current_volume
            total_expected_revenue += eval_res["promo_price"] * eval_res["projected_volume"]

        net_campaign_profit = total_expected_profit - total_marketing_budget_usd
        net_incremental_profit = net_campaign_profit - total_baseline_profit
        roi_pct = (net_incremental_profit / total_marketing_budget_usd * 100.0) if total_marketing_budget_usd > 0 else 0.0

        df_results = pd.DataFrame(results)

        return {
            "summary": {
                "total_skus_evaluated": len(scenarios),
                "skus_approved": int(df_results["is_viable"].sum()) if not df_results.empty else 0,
                "skus_rejected": int((~df_results["is_viable"]).sum()) if not df_results.empty else 0,
                "baseline_revenue_usd": round(total_baseline_revenue, 2),
                "projected_revenue_usd": round(total_expected_revenue, 2),
                "baseline_profit_usd": round(total_baseline_profit, 2),
                "expected_gross_profit_usd": round(total_expected_profit, 2),
                "marketing_budget_usd": round(total_marketing_budget_usd, 2),
                "net_incremental_profit_usd": round(net_incremental_profit, 2),
                "campaign_roi_pct": round(roi_pct, 1),
            },
            "sku_details": df_results,
        }
