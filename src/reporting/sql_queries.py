"""Analytical SQL query library with Window Functions, CTEs, and cohort aggregations."""


class RetailAnalyticsQueries:
    """Production-grade SQL analytical queries for margin protection and omnichannel pricing."""

    @staticmethod
    def get_margin_health_90d() -> str:
        """Evaluates margin health by SKU, category, channel, and country over the last 90 days.
        
        Classifies into:
            - CRÍTICO: Margen Insuficiente (<20%)
            - SALUDABLE: En Rango (20-35%)
            - ESTRELLA: Alto Retorno (>35%)
        """
        return """
        WITH GrossMarginAnalysis AS (
            SELECT 
                p.sku,
                p.name AS product_name,
                p.category,
                p.tier_segment,
                t.channel_id,
                t.country_id,
                SUM(t.units_sold) AS total_units,
                SUM(t.net_revenue_usd) AS total_revenue_usd,
                SUM(t.net_revenue_usd - (t.units_sold * p.cogs_usd) - t.channel_fee_usd - t.shipping_cost_usd) AS total_gross_profit_usd,
                (SUM(t.net_revenue_usd - (t.units_sold * p.cogs_usd) - t.channel_fee_usd - t.shipping_cost_usd) * 1.0 / NULLIF(SUM(t.net_revenue_usd), 0)) * 100.0 AS margin_pct
            FROM fct_transactions t
            JOIN dim_products p ON t.sku = p.sku
            WHERE t.date >= DATE((SELECT MAX(date) FROM fct_transactions), '-90 days')
            GROUP BY p.sku, p.name, p.category, p.tier_segment, t.channel_id, t.country_id
        )
        SELECT 
            sku,
            product_name,
            category,
            tier_segment,
            channel_id,
            country_id,
            total_units,
            ROUND(total_revenue_usd, 2) AS revenue_usd,
            ROUND(total_gross_profit_usd, 2) AS profit_usd,
            ROUND(margin_pct, 2) AS margin_percentage,
            CASE 
                WHEN margin_pct < 20.0 THEN 'CRÍTICO: Margen Insuficiente'
                WHEN margin_pct BETWEEN 20.0 AND 35.0 THEN 'SALUDABLE: En Rango'
                ELSE 'ESTRELLA: Alto Retorno'
            END AS financial_health_status
        FROM GrossMarginAnalysis
        ORDER BY total_gross_profit_usd DESC;
        """

    @staticmethod
    def get_omnichannel_price_coherence() -> str:
        """Identifies price disparities across D2C Shopify, Mercado Libre, and B2B Gym.
        
        Detects channel conflict and cannibalization risk using window functions.
        """
        return """
        WITH ChannelStats AS (
            SELECT 
                t.sku,
                p.name,
                p.category,
                t.country_id,
                t.channel_id,
                AVG(t.net_price_local) AS avg_net_price,
                SUM(t.units_sold) AS units_sold,
                SUM(t.net_revenue_usd) AS revenue_usd
            FROM fct_transactions t
            JOIN dim_products p ON t.sku = p.sku
            GROUP BY t.sku, p.name, p.category, t.country_id, t.channel_id
        ),
        ChannelPivoted AS (
            SELECT 
                sku,
                name,
                category,
                country_id,
                MAX(CASE WHEN channel_id = 'D2C_SHOPIFY' THEN avg_net_price END) AS shopify_price,
                MAX(CASE WHEN channel_id = 'MELI_FULL' THEN avg_net_price END) AS meli_price,
                MAX(CASE WHEN channel_id = 'B2B_GYM' THEN avg_net_price END) AS b2b_price,
                SUM(units_sold) AS total_units,
                SUM(revenue_usd) AS total_revenue
            FROM ChannelStats
            GROUP BY sku, name, category, country_id
        )
        SELECT 
            sku,
            name,
            category,
            country_id,
            ROUND(shopify_price, 2) AS price_shopify,
            ROUND(meli_price, 2) AS price_meli,
            ROUND(b2b_price, 2) AS price_b2b,
            ROUND(((meli_price - shopify_price) * 1.0 / NULLIF(shopify_price, 0)) * 100.0, 2) AS meli_vs_shopify_spread_pct,
            total_units,
            ROUND(total_revenue, 2) AS total_revenue_usd,
            CASE 
                WHEN meli_price < shopify_price THEN 'ALERTA: Mercado Libre canibalizando Shopify D2C'
                WHEN shopify_price > (b2b_price * 1.6) THEN 'ALERTA: Sobreprecio en Shopify frente a Distribución B2B'
                ELSE 'COHERENTE: Política de Canales Equilibrada'
            END AS channel_arbitrage_risk
        FROM ChannelPivoted
        ORDER BY total_revenue DESC;
        """

    @staticmethod
    def get_slow_moving_inventory() -> str:
        """Identifies slow-moving inventory with high DIO (Days of Inventory Outstanding).
        
        Calculates run-rate over the last 180 days and projects stock runout.
        """
        return """
        WITH RecentVelocity AS (
            SELECT 
                t.sku,
                SUM(t.units_sold) AS units_sold_180d,
                SUM(t.units_sold * 1.0) / 180.0 AS daily_sales_velocity
            FROM fct_transactions t
            WHERE t.date >= DATE((SELECT MAX(date) FROM fct_transactions), '-180 days')
            GROUP BY t.sku
        )
        SELECT 
            p.sku,
            p.name,
            p.category,
            p.lifecycle_status,
            p.cogs_usd,
            p.base_price_usd,
            p.stock_on_hand,
            ROUND(p.stock_on_hand * p.cogs_usd, 2) AS capital_tied_up_cogs_usd,
            COALESCE(v.units_sold_180d, 0) AS units_sold_180d,
            ROUND(COALESCE(v.daily_sales_velocity, 0), 3) AS daily_velocity,
            ROUND(
                CASE 
                    WHEN COALESCE(v.daily_sales_velocity, 0) > 0 THEN p.stock_on_hand / v.daily_sales_velocity
                    ELSE 999.0
                END, 1
            ) AS estimated_dio,
            CASE 
                WHEN COALESCE(v.daily_sales_velocity, 0) = 0 OR (p.stock_on_hand / NULLIF(v.daily_sales_velocity, 0)) > 240.0
                    THEN 'DEAD STOCK CRÍTICO: Iniciar Markdown Escalado'
                WHEN (p.stock_on_hand / NULLIF(v.daily_sales_velocity, 0)) BETWEEN 120.0 AND 240.0 
                    THEN 'ATENCIÓN: Riesgo de Obsolescencia'
                ELSE 'SALUDABLE: Rotación Normal'
            END AS inventory_health_action
        FROM dim_products p
        LEFT JOIN RecentVelocity v ON p.sku = v.sku
        WHERE p.stock_on_hand > 0
        ORDER BY capital_tied_up_cogs_usd DESC;
        """

    @staticmethod
    def get_monthly_financial_waterfall() -> str:
        """Generates monthly P&L waterfall across the full 24-month horizon."""
        return """
        SELECT 
            SUBSTR(t.date, 1, 7) AS year_month,
            COUNT(DISTINCT t.transaction_id) AS total_orders,
            SUM(t.units_sold) AS total_units,
            ROUND(SUM(t.net_revenue_usd), 2) AS gross_revenue_usd,
            ROUND(SUM(t.units_sold * p.cogs_usd), 2) AS total_cogs_usd,
            ROUND(SUM(t.channel_fee_usd), 2) AS total_fees_usd,
            ROUND(SUM(t.shipping_cost_usd), 2) AS total_shipping_usd,
            ROUND(SUM(t.gross_margin_usd), 2) AS gross_profit_usd,
            ROUND((SUM(t.gross_margin_usd) * 1.0 / NULLIF(SUM(t.net_revenue_usd), 0)) * 100.0, 2) AS gross_margin_pct,
            SUM(t.is_promo) AS promo_transactions_count
        FROM fct_transactions t
        JOIN dim_products p ON t.sku = p.sku
        GROUP BY SUBSTR(t.date, 1, 7)
        ORDER BY year_month ASC;
        """
