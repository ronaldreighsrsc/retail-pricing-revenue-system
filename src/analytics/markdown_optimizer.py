"""Dynamic markdown and inventory clearance optimization for slow-moving stock."""

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from src.core.base_optimizer import BaseOptimizer


@dataclass
class MarkdownStep:
    week_number: int
    discount_pct: float
    recommended_price: float
    projected_sales_units: int
    remaining_stock: int
    cash_recovered_usd: float
    holding_cost_saved_usd: float


class MarkdownOptimizer(BaseOptimizer):
    """Dynamic programming and discount ladder optimizer for slow-moving dead stock."""

    def optimize(self, **kwargs) -> List[MarkdownStep]:
        """Runs markdown trajectory optimization."""
        return self.generate_schedule(
            current_stock=kwargs.get("current_stock", 100),
            base_price=kwargs.get("base_price", 100.0),
            unit_cogs=kwargs.get("unit_cogs", 60.0),
            weeks_horizon=kwargs.get("weeks_horizon", 6),
            elasticity=kwargs.get("elasticity", -1.8),
            weekly_holding_cost_rate=kwargs.get("weekly_holding_cost_rate", 0.005),
        )

    @staticmethod
    def calculate_dio(stock_on_hand: int, cogs_usd: float, annual_units_sold: int) -> float:
        """Calculates Days of Inventory Outstanding (DIO).
        
        DIO = (Current Stock Value / Annual COGS Sold) * 365
        """
        if annual_units_sold <= 0 or cogs_usd <= 0:
            return 999.0
        return round((stock_on_hand / annual_units_sold) * 365.0, 1)

    @staticmethod
    def generate_schedule(
        current_stock: int,
        base_price: float,
        unit_cogs: float,
        weeks_horizon: int = 6,
        elasticity: float = -1.8,
        weekly_holding_cost_rate: float = 0.005,  # 0.5% per week of holding cost (storage + capital)
    ) -> List[MarkdownStep]:
        """Generates a monotonic weekly markdown discount schedule.
        
        Accelerates sales velocity while protecting recovered cash.
        """
        schedule: List[MarkdownStep] = []
        stock = current_stock
        
        # Monotonic stepped discount ladder (10% to 60%)
        default_ladder = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60]
        ladder = default_ladder[:weeks_horizon]

        # Base weekly sales run-rate without extra discount (conservative baseline: 5% of stock or 4 units)
        base_weekly_sales = max(3, int(current_stock * 0.05))

        for w_idx, disc in enumerate(ladder):
            price = round(base_price * (1.0 - disc), 2)
            
            # Demand acceleration factor from elasticity
            velocity_boost = 1.0 + (abs(elasticity) * disc)
            projected_sales = min(stock, max(1, int(round(base_weekly_sales * velocity_boost))))
            
            stock -= projected_sales
            cash = round(projected_sales * price, 2)
            
            # Holding cost saved on units liquidated
            holding_cost_saved = round(projected_sales * unit_cogs * weekly_holding_cost_rate * (weeks_horizon - w_idx), 2)

            schedule.append(
                MarkdownStep(
                    week_number=w_idx + 1,
                    discount_pct=round(disc * 100, 1),
                    recommended_price=price,
                    projected_sales_units=projected_sales,
                    remaining_stock=stock,
                    cash_recovered_usd=cash,
                    holding_cost_saved_usd=holding_cost_saved,
                )
            )

            if stock <= 0:
                break

        return schedule

    @classmethod
    def summarize_clearance_plan(cls, schedule: List[MarkdownStep], initial_stock: int, base_price: float) -> Dict[str, float]:
        """Aggregates clearance trajectory performance metrics."""
        total_cash = sum(step.cash_recovered_usd for step in schedule)
        total_units = sum(step.projected_sales_units for step in schedule)
        total_holding_saved = sum(step.holding_cost_saved_usd for step in schedule)
        theoretical_max_cash = initial_stock * base_price
        recovery_rate = (total_cash / theoretical_max_cash * 100.0) if theoretical_max_cash > 0 else 0.0

        return {
            "initial_stock_units": initial_stock,
            "liquidated_units": total_units,
            "stock_clearance_pct": round((total_units / initial_stock * 100.0), 1) if initial_stock > 0 else 0.0,
            "total_cash_recovered_usd": round(total_cash, 2),
            "holding_cost_saved_usd": round(total_holding_saved, 2),
            "effective_recovery_rate_pct": round(recovery_rate, 1),
            "weeks_to_clear": len(schedule),
        }
