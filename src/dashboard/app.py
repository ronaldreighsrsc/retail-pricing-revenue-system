"""AURA-Pricing Engine: Autonomous Unified Revenue Analytics & Portfolio Optimization
Executive Commercial Decision Dashboard in Streamlit.
"""

import os
import sys
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.data_engine.repository import SQLiteRetailRepository
from src.data_engine.generator import RetailDataGenerator
from src.analytics.elasticity_engine import ElasticityEngine
from src.analytics.competitive_tracker import CompetitiveTracker
from src.analytics.promotion_simulator import PromotionScenario
from src.analytics.markdown_optimizer import MarkdownOptimizer
from src.reporting.sql_queries import RetailAnalyticsQueries
from src.reporting.excel_generator import CorporateExcelBuilder

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AURA-Pricing Engine | Executive Portal",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F2042 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .metric-card {
        background: #1E293B;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #334155;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.25);
        border-color: #38BDF8;
    }
    
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    
    .metric-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #F8FAFC;
    }
    
    .badge-approved {
        background: rgba(16, 185, 129, 0.2);
        color: #34D399;
        padding: 6px 14px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        border: 1px solid #059669;
        display: inline-block;
    }
    
    .badge-rejected {
        background: rgba(239, 68, 68, 0.2);
        color: #F87171;
        padding: 6px 14px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        border: 1px solid #DC2626;
        display: inline-block;
    }
    
    .badge-neutral {
        background: rgba(56, 189, 248, 0.15);
        color: #38BDF8;
        padding: 4px 10px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Data Loader & Repository Initialization
# -----------------------------------------------------------------------------
@st.cache_resource
def get_repository() -> SQLiteRetailRepository:
    db_path = "data/processed/retail_pricing.db"
    if not os.path.exists(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        gen = RetailDataGenerator(seed=42)
        prods = gen.generate_products(target_sku_count=350)
        quotes = gen.generate_competitor_scrap(prods)
        tx = gen.generate_transactions(prods)
        repo = SQLiteRetailRepository(db_path)
        repo.seed_data(prods, tx, quotes)
        repo.export_to_parquet("data/processed")
        CorporateExcelBuilder.build_full_workbook(prods, quotes, "data/excel/AURA_Pricing_Engine_Executive_Model.xlsx")
        return repo
    return SQLiteRetailRepository(db_path)


@st.cache_data(ttl=600)
def load_core_data():
    repo = get_repository()
    df_products = repo.get_products()
    df_competitors = repo.get_competitor_quotes()
    df_monthly = repo.execute_query(RetailAnalyticsQueries.get_monthly_financial_waterfall())
    df_margin_health = repo.execute_query(RetailAnalyticsQueries.get_margin_health_90d())
    df_slow_movers = repo.execute_query(RetailAnalyticsQueries.get_slow_moving_inventory())
    df_omnichannel = repo.execute_query(RetailAnalyticsQueries.get_omnichannel_price_coherence())
    return df_products, df_competitors, df_monthly, df_margin_health, df_slow_movers, df_omnichannel


df_products, df_competitors, df_monthly, df_margin_health, df_slow_movers, df_omnichannel = load_core_data()

# -----------------------------------------------------------------------------
# Sidebar Navigation & Filter Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=400&auto=format&fit=crop&q=80", use_container_width=True)
    st.markdown("## ⚙️ Parámetros Globales")
    
    selected_country = st.selectbox("🌐 Mercado / País", ["Todos (CL, MX, AR)", "Chile (CL)", "México (MX)", "Argentina (AR)"])
    country_filter = None
    if "Chile" in selected_country:
        country_filter = "CL"
    elif "México" in selected_country:
        country_filter = "MX"
    elif "Argentina" in selected_country:
        country_filter = "AR"

    categories = ["Todas"] + sorted(df_products["category"].unique().tolist())
    selected_cat = st.selectbox("📦 Categoría de Catálogo", categories)

    st.markdown("---")
    st.markdown("""
    **AURA-Pricing Engine v1.0**  
    *Clean Architecture + Econometrics*  
    Inspirado en operaciones reales de **IRONSIDE Fitness**.
    """)

# Filter products by selected category
filtered_products = df_products.copy()
if selected_cat != "Todas":
    filtered_products = filtered_products[filtered_products["category"] == selected_cat]

# -----------------------------------------------------------------------------
# Main Header Banner
# -----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin: 0; font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em;">
                🏷️ AURA-Pricing Engine
            </h1>
            <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 1.05rem;">
                Autonomous Unified Revenue Analytics & Portfolio Optimization • Multi-Channel & Multi-Country
            </p>
        </div>
        <div style="text-align: right;">
            <span class="badge-neutral" style="font-size: 0.9rem; padding: 6px 16px;">Operaciones: CL • MX • AR</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Executive Tabs
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Resumen Ejecutivo del Portafolio",
    "🎯 Radar Competitivo & Price Index",
    "⚡ Laboratorio de Campañas & CyberDay",
    "📦 Markdown Engine (Dead Stock)",
    "📑 Modelo Excel & Pipeline SQL",
])

# =============================================================================
# TAB 1: RESUMEN EJECUTIVO DEL PORTAFOLIO
# =============================================================================
with tab1:
    st.markdown("### 📈 Indicadores Financieros Clave (P&L Consolidado)")

    # Aggregate metrics
    total_rev = df_monthly["gross_revenue_usd"].sum()
    total_margin = df_monthly["gross_profit_usd"].sum()
    margin_pct = (total_margin / total_rev * 100.0) if total_rev > 0 else 0.0
    total_units = df_monthly["total_units"].sum()

    # Filtered products stats
    avg_elasticity = filtered_products["true_elasticity"].mean()
    skus_at_risk = len(df_margin_health[df_margin_health["financial_health_status"] == "CRÍTICO: Margen Insuficiente"])

    # Metric Cards Row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Revenue Acumulado (24M)</div>
            <div class="metric-value">${total_rev/1_000_000:.2f}M</div>
            <div style="color: #34D399; font-size: 0.85rem; margin-top: 4px;">USD Base Consolidado</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Margen Bruto Total</div>
            <div class="metric-value">${total_margin/1_000_000:.2f}M</div>
            <div style="color: #38BDF8; font-size: 0.85rem; margin-top: 4px;">{margin_pct:.1f}% del Revenue</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Unidades Totales</div>
            <div class="metric-value">{total_units:,.0f}</div>
            <div style="color: #94A3B8; font-size: 0.85rem; margin-top: 4px;">CL, MX y AR</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Elasticidad Promedio</div>
            <div class="metric-value">{avg_elasticity:.2f}</div>
            <div style="color: #FBBF24; font-size: 0.85rem; margin-top: 4px;">Portafolio Activo</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">SKUs en Riesgo (&lt;20%)</div>
            <div class="metric-value" style="color: #F87171;">{skus_at_risk}</div>
            <div style="color: #EF4444; font-size: 0.85rem; margin-top: 4px;">Alerta de Margen</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row 1: Margin vs Elasticity Scatter & Monthly Waterfall
    col_chart_left, col_chart_right = st.columns([1.1, 0.9])

    with col_chart_left:
        st.markdown("#### 🎯 Matriz de Decisión: Margen Bruto % vs. Elasticidad Precio (BCG-Pricing)")
        
        # Merge product info with margin
        prod_agg = df_margin_health.groupby("sku").agg(
            revenue=("revenue_usd", "sum"),
            profit=("profit_usd", "sum"),
        ).reset_index()
        prod_scatter = pd.merge(filtered_products, prod_agg, on="sku", how="inner")
        prod_scatter["margin_pct"] = (prod_scatter["profit"] / prod_scatter["revenue"] * 100.0).round(1)

        fig_scatter = px.scatter(
            prod_scatter,
            x="true_elasticity",
            y="margin_pct",
            size="revenue",
            color="category",
            hover_name="name",
            hover_data={"sku": True, "base_price_usd": True, "tier_segment": True},
            labels={"true_elasticity": "Elasticidad Precio (Epsilon)", "margin_pct": "Margen Bruto (%)", "category": "Categoría"},
            title="Cuadrantes Estratégicos: Elasticidad vs Rentabilidad",
            template="plotly_dark",
            height=430,
        )
        # Quadrant reference lines
        fig_scatter.add_vline(x=-1.0, line_dash="dash", line_color="#94A3B8", annotation_text="Epsilon = -1.0 (Límite Inelástico)")
        fig_scatter.add_hline(y=30.0, line_dash="dash", line_color="#94A3B8", annotation_text="Objetivo Margen 30%")
        fig_scatter.update_layout(paper_bgcolor="#1E293B", plot_bgcolor="#0F172A", margin=dict(l=40, r=40, t=50, b=40))
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_chart_right:
        st.markdown("#### 🌊 Trayectoria Mensual de Revenue y Utilidad (24 Meses)")
        fig_waterfall = go.Figure()
        fig_waterfall.add_trace(go.Bar(
            x=df_monthly["year_month"],
            y=df_monthly["gross_revenue_usd"],
            name="Revenue USD",
            marker_color="#38BDF8",
        ))
        fig_waterfall.add_trace(go.Scatter(
            x=df_monthly["year_month"],
            y=df_monthly["gross_profit_usd"],
            name="Margen Bruto USD",
            mode="lines+markers",
            marker=dict(color="#34D399", size=6),
            line=dict(color="#34D399", width=2.5),
            yaxis="y2",
        ))
        fig_waterfall.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1E293B",
            plot_bgcolor="#0F172A",
            height=430,
            yaxis=dict(title="Revenue USD ($)", showgrid=False),
            yaxis2=dict(title="Margen Bruto USD ($)", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=50, b=40),
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)

    # Health status summary table
    st.markdown("#### 🩺 Auditoría de Salud Financiera por SKU y Canal (Últimos 90 Días)")
    status_filter = st.radio("Filtrar por Diagnóstico Financiero:", ["Todos", "CRÍTICO: Margen Insuficiente", "SALUDABLE: En Rango", "ESTRELLA: Alto Retorno"], horizontal=True)
    df_display_health = df_margin_health.copy()
    if status_filter != "Todos":
        df_display_health = df_display_health[df_display_health["financial_health_status"] == status_filter]
    
    st.dataframe(
        df_display_health[["sku", "product_name", "category", "channel_id", "country_id", "revenue_usd", "profit_usd", "margin_percentage", "financial_health_status"]].head(50),
        column_config={
            "revenue_usd": st.column_config.NumberColumn("Revenue ($)", format="$%,.2f"),
            "profit_usd": st.column_config.NumberColumn("Ganancia Bruta ($)", format="$%,.2f"),
            "margin_percentage": st.column_config.ProgressColumn("Margen (%)", format="%.1f%%", min_value=0, max_value=60),
            "financial_health_status": st.column_config.TextColumn("Estado Financiero"),
        },
        use_container_width=True,
        height=320,
    )


# =============================================================================
# TAB 2: RADAR COMPETITIVO & PRICE INDEX
# =============================================================================
with tab2:
    st.markdown("### 🎯 Benchmark de Competidores y Price Indexing Continuo")
    st.markdown("""
    Calcula la dispersión de precios frente a las principales marcas del mercado (*Spartan, Rogue, SDmed, Tayga*).
    Clasifica cada SKU según la **Matriz Ejecutiva de Price Index**:
    - **Overpriced (>115)**: Riesgo de fuga de demanda.
    - **Healthy Premium (105-115)**: Posicionamiento saludable respaldado en servicio y garantía.
    - **Competitive Parity (98-105)**: Paridad de mercado.
    - **Underpriced (<95)**: **Fuga de margen** — Oportunidad de subir precio.
    """)

    # Merge competitor quotes with our catalog
    df_comp_active = df_competitors.copy()
    if country_filter:
        df_comp_active = df_comp_active[df_comp_active["country_id"] == country_filter]

    merged_prices = pd.merge(
        df_comp_active,
        df_products[["sku", "name", "category", "base_price_usd", "true_elasticity"]],
        on="sku",
        how="inner",
    )
    merged_prices.rename(columns={"base_price_usd": "our_price", "competitor_price_usd": "competitor_price"}, inplace=True)
    
    indexed_df = CompetitiveTracker.calculate_price_index(merged_prices)

    # Summary metric row
    pi_col1, pi_col2, pi_col3, pi_col4 = st.columns(4)
    overpriced_count = len(indexed_df[indexed_df["competitive_tier"] == "Overpriced (High Risk)"])
    underpriced_count = len(indexed_df[indexed_df["competitive_tier"] == "Underpriced (Margin Leakage)"])
    parity_count = len(indexed_df[indexed_df["competitive_tier"] == "Competitive Parity"])
    mean_pi = indexed_df["price_index"].mean()

    with pi_col1:
        st.metric("Price Index Promedio Global", f"{mean_pi:.1f}%", delta=f"{mean_pi - 100.0:+.1f}% vs Paridad")
    with pi_col2:
        st.metric("SKUs Desalineados Baratos (Fuga Margen)", underpriced_count, help="Oportunidad inmediata de captura de margen")
    with pi_col3:
        st.metric("SKUs en Paridad Competitiva", parity_count)
    with pi_col4:
        st.metric("SKUs Desalineados Caros (Riesgo Venta)", overpriced_count)

    st.markdown("<br>", unsafe_allow_html=True)

    # PI Distribution Chart & Brand Radar
    pi_left, pi_right = st.columns([1, 1])

    with pi_left:
        st.markdown("#### 📊 Distribución de Price Index por Nivel Estratégico")
        fig_tier_pie = px.pie(
            indexed_df,
            names="competitive_tier",
            title="Segmentación del Catálogo por Posicionamiento Competitivo",
            color="competitive_tier",
            color_discrete_map={
                "Overpriced (High Risk)": "#EF4444",
                "Healthy Premium": "#38BDF8",
                "Competitive Parity": "#10B981",
                "Underpriced (Margin Leakage)": "#F59E0B",
                "Slightly Discounted": "#6366F1",
            },
            hole=0.45,
            template="plotly_dark",
            height=380,
        )
        fig_tier_pie.update_layout(paper_bgcolor="#1E293B", plot_bgcolor="#0F172A", margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_tier_pie, use_container_width=True)

    with pi_right:
        st.markdown("#### 🏢 Price Index Promedio por Marca Competidora")
        brand_summary = CompetitiveTracker.summarize_by_brand(indexed_df)
        fig_brand_bar = px.bar(
            brand_summary,
            x="competitor_brand",
            y="mean_price_index",
            color="mean_price_index",
            color_continuous_scale="Blues",
            title="Nuestra Posición de Precio Frente a Cada Competidor (100 = Paridad)",
            labels={"competitor_brand": "Competidor", "mean_price_index": "Price Index Promedio (%)"},
            template="plotly_dark",
            height=380,
        )
        fig_brand_bar.add_hline(y=100.0, line_dash="dash", line_color="#EF4444", annotation_text="Paridad (100)")
        fig_brand_bar.update_layout(paper_bgcolor="#1E293B", plot_bgcolor="#0F172A", margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_brand_bar, use_container_width=True)

    # Arbitrage Opportunities Table
    st.markdown("#### 💎 Oportunidades de Captura de Margen Inmediata (SKUs Baratos e Inelásticos)")
    st.caption("Productos donde nuestro precio está por debajo del mercado (PI < 95) y la demanda es inelástica (epsilon > -1.0). Se recomienda aumento de precio sin riesgo de volumen.")

    df_elasticity_sub = filtered_products[["sku", "true_elasticity"]].rename(columns={"true_elasticity": "elasticity_coefficient"})
    df_elasticity_sub["demand_regime"] = np.where(df_elasticity_sub["elasticity_coefficient"] > -1.0, "Inelastic", "Elastic")
    arbitrage_df = CompetitiveTracker.identify_arbitrage_opportunities(indexed_df, df_elasticity_sub)

    st.dataframe(
        arbitrage_df[["sku", "name", "competitor_brand", "country_id", "our_price", "competitor_price", "price_index", "elasticity_coefficient", "priority_score", "pricing_action"]].head(40),
        column_config={
            "our_price": st.column_config.NumberColumn("Nuestro Precio ($)", format="$%,.2f"),
            "competitor_price": st.column_config.NumberColumn("Competidor ($)", format="$%,.2f"),
            "price_index": st.column_config.NumberColumn("Price Index (%)", format="%.1f%%"),
            "elasticity_coefficient": st.column_config.NumberColumn("Elasticidad (Eps)", format="%.2f"),
            "priority_score": st.column_config.TextColumn("Prioridad de Ajuste"),
            "pricing_action": st.column_config.TextColumn("Acción Recomendada"),
        },
        use_container_width=True,
        height=320,
    )


# =============================================================================
# TAB 3: LABORATORIO DE CAMPAÑAS & CYBERDAY
# =============================================================================
with tab3:
    st.markdown("### ⚡ Simulador de Promociones, Incrementalidad y Break-Even Volume Lift")
    st.markdown("""
    Resuelve la pregunta clave para eventos como **CyberDay, Black Friday y Hot Sale**:  
    *¿Cuántas unidades adicionales necesitamos vender si aplicamos un descuento del **X%** para no destruir margen bruto?*
    $$\\text{Lift}_{BE} = \\frac{d}{M_0 - d}$$
    """)

    sim_col_controls, sim_col_results = st.columns([1, 1.4])

    with sim_col_controls:
        st.markdown("#### 🎛️ Configuración del Escenario Comercial")
        
        # Select SKU to simulate
        sku_options = filtered_products["sku"].tolist()
        default_sku = sku_options[0] if sku_options else "IRN-FUE-BAR-0001"
        selected_sku = st.selectbox("Seleccione SKU para Simulación:", sku_options, index=0)
        
        sku_info = filtered_products[filtered_products["sku"] == selected_sku].iloc[0]
        st.info(f"**{sku_info['name']}**  \nCategoría: {sku_info['category']} | Tier: {sku_info['tier_segment']}")

        base_p = float(sku_info["base_price_usd"])
        unit_c = float(sku_info["cogs_usd"])
        eps = float(sku_info.get("true_elasticity", -1.8))
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            sim_price = st.number_input("Precio Lista Base (USD):", min_value=1.0, value=base_p, step=5.0)
            sim_vol = st.number_input("Volumen Base Mensual (uds):", min_value=5, value=120, step=10)
        with col_p2:
            sim_cogs = st.number_input("Costo Unitario COGS (USD):", min_value=1.0, value=unit_c, step=5.0)
            sim_eps = st.number_input("Elasticidad Precio (Eps):", value=eps, step=0.1)

        sim_discount = st.slider("Porcentaje de Descuento Propuesto (%):", min_value=0.0, max_value=50.0, value=15.0, step=1.0) / 100.0
        marketing_spend = st.number_input("Inversión en Publicidad / Pauta Marketing ($ USD):", min_value=0.0, value=250.0, step=50.0)

    # Run simulation
    scenario = PromotionScenario(
        sku=selected_sku,
        current_price=sim_price,
        current_volume=int(sim_vol),
        unit_cogs=sim_cogs,
        proposed_discount_pct=sim_discount,
        price_elasticity=sim_eps,
        marketing_cost_allocated_usd=marketing_spend,
    )
    res = scenario.evaluate()

    with sim_col_results:
        st.markdown("#### 📊 Dictamen y Resultados Financieros")

        # Recommendation Banner
        if res["is_viable"]:
            st.markdown(f'<div class="badge-approved" style="font-size: 1.1rem; padding: 10px 24px; margin-bottom: 16px;">✅ PROMOCIÓN APROBADA: Genera +${res["incremental_profit_usd"]:,.2f} USD de Ganancia Neta</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="badge-rejected" style="font-size: 1.1rem; padding: 10px 24px; margin-bottom: 16px;">❌ VETADA POR GERENCIA: Destruye -${abs(res["incremental_profit_usd"]):,.2f} USD de Margen Bruto</div>', unsafe_allow_html=True)

        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("Lift de Equilibrio (Break-Even)", f"{res['break_even_volume_lift_pct']:.1f}%", help="Volumen adicional mínimo para empatar la utilidad original")
        with k2:
            st.metric("Lift Esperado (Elasticidad)", f"{res['expected_volume_lift_pct']:.1f}%", delta=f"{res['expected_volume_lift_pct'] - res['break_even_volume_lift_pct']:+.1f}% vs Equilibrio")
        with k3:
            st.metric("Precio Promocional", f"${res['promo_price']:.2f} USD", delta=f"-{sim_discount*100:.0f}%")

        k4, k5, k6 = st.columns(3)
        with k4:
            st.metric("Ganancia Base (Sin Promo)", f"${res['baseline_profit_usd']:,.2f}")
        with k5:
            st.metric("Ganancia Proyectada Promo", f"${res['expected_profit_usd']:,.2f}")
        with k6:
            st.metric("Ganancia Incremental Neta", f"${res['incremental_profit_usd']:,.2f}", delta=f"{res['incremental_profit_usd']:+,.2f}")

        # Sensitivity Curve: Profit vs Discount %
        discount_range = np.linspace(0.01, 0.45, 30)
        curve_data = []
        for d_test in discount_range:
            sc_test = PromotionScenario(
                sku=selected_sku,
                current_price=sim_price,
                current_volume=int(sim_vol),
                unit_cogs=sim_cogs,
                proposed_discount_pct=d_test,
                price_elasticity=sim_eps,
                marketing_cost_allocated_usd=marketing_spend,
            )
            eval_test = sc_test.evaluate()
            curve_data.append({
                "discount_pct": d_test * 100.0,
                "profit_usd": eval_test["expected_profit_usd"],
                "is_viable": eval_test["is_viable"],
            })
        df_curve = pd.DataFrame(curve_data)

        fig_curve = px.line(
            df_curve,
            x="discount_pct",
            y="profit_usd",
            title=f"Curva de Sensibilidad: Utilidad Neta vs % Descuento ({selected_sku})",
            labels={"discount_pct": "Descuento Comercial (%)", "profit_usd": "Ganancia Neta Esperada (USD)"},
            template="plotly_dark",
            height=280,
        )
        fig_curve.add_hline(y=res["baseline_profit_usd"], line_dash="dash", line_color="#EF4444", annotation_text="Línea Base Sin Descuento")
        fig_curve.add_vline(x=sim_discount * 100.0, line_dash="dot", line_color="#FBBF24", annotation_text="Punto Evaluado")
        fig_curve.update_layout(paper_bgcolor="#1E293B", plot_bgcolor="#0F172A", margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_curve, use_container_width=True)


# =============================================================================
# TAB 4: MARKDOWN ENGINE (DEAD STOCK CLEARANCE)
# =============================================================================
with tab4:
    st.markdown("### 📦 Algoritmo de Liquidación Dinámica de Inventario (Markdown Schedule)")
    st.markdown("""
    Optimiza la salida de productos con **Días de Inventario elevados ($DIO > 180$)** o en fase de liquidación (*Clearance*).
    Aplica una escalera descendente de precios (*Markdown Ladder*) acelerando la velocidad de venta antes de incurrir en costos de almacenamiento crítico.
    """)

    # Filter slow-moving products
    st.markdown("#### 🚨 Radar de Inventario Crítico (Slow-Movers & Dead Stock)")
    st.dataframe(
        df_slow_movers[["sku", "name", "category", "lifecycle_status", "stock_on_hand", "capital_tied_up_cogs_usd", "estimated_dio", "inventory_health_action"]].head(25),
        column_config={
            "capital_tied_up_cogs_usd": st.column_config.NumberColumn("Capital Inmovilizado ($)", format="$%,.2f"),
            "estimated_dio": st.column_config.NumberColumn("DIO (Días)", format="%.0f días"),
            "inventory_health_action": st.column_config.TextColumn("Acción Operativa"),
        },
        use_container_width=True,
        height=240,
    )

    st.markdown("---")
    st.markdown("#### 🗓️ Generador Interactivo de Calendario de Rebajas")

    col_mk_ctrl, col_mk_view = st.columns([1, 1.4])
    with col_mk_ctrl:
        slow_sku_options = df_slow_movers["sku"].tolist()
        mk_sku = st.selectbox("Seleccione SKU para Liquidar:", slow_sku_options, index=0)
        slow_prod = df_slow_movers[df_slow_movers["sku"] == mk_sku].iloc[0]

        mk_stock = int(slow_prod["stock_on_hand"])
        mk_price = float(slow_prod["base_price_usd"])
        mk_cogs = float(slow_prod["cogs_usd"])

        st.write(f"**Stock en Bodega:** {mk_stock} unidades")
        st.write(f"**Precio de Lista:** ${mk_price:,.2f} USD | **COGS:** ${mk_cogs:,.2f} USD")

        mk_horizon = st.slider("Horizonte de Liquidación (Semanas):", min_value=3, max_value=6, value=6)
        mk_eps = st.slider("Elasticidad Precio Estimada:", min_value=-3.5, max_value=-1.0, value=-1.8, step=0.1)

    schedule = MarkdownOptimizer.generate_schedule(
        current_stock=mk_stock,
        base_price=mk_price,
        unit_cogs=mk_cogs,
        weeks_horizon=mk_horizon,
        elasticity=mk_eps,
    )
    summary_plan = MarkdownOptimizer.summarize_clearance_plan(schedule, mk_stock, mk_price)

    with col_mk_view:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Caja Total Recuperada", f"${summary_plan['total_cash_recovered_usd']:,.2f}")
        with m2:
            st.metric("Tasa de Recuperación", f"{summary_plan['effective_recovery_rate_pct']:.1f}%")
        with m3:
            st.metric("Unidades Liquidadas", f"{summary_plan['liquidated_units']} / {mk_stock}")
        with m4:
            st.metric("Ahorro Bodegaje", f"${summary_plan['holding_cost_saved_usd']:,.2f}")

        # Trajectory Table
        df_schedule = pd.DataFrame([{
            "Semana": s.week_number,
            "Descuento (%)": f"{s.discount_pct:.0f}%",
            "Precio Rebajado ($)": f"${s.recommended_price:,.2f}",
            "Ventas Proyectadas (uds)": s.projected_sales_units,
            "Stock Remanente (uds)": s.remaining_stock,
            "Caja Ingresada ($)": f"${s.cash_recovered_usd:,.2f}",
            "Ahorro Bodega ($)": f"${s.holding_cost_saved_usd:,.2f}",
        } for s in schedule])

        st.table(df_schedule)

        # Plot stock drawdown
        fig_stock = go.Figure()
        fig_stock.add_trace(go.Bar(
            x=[f"Semana {s.week_number}" for s in schedule],
            y=[s.cash_recovered_usd for s in schedule],
            name="Caja Semanal Recuperada ($)",
            marker_color="#38BDF8",
        ))
        fig_stock.add_trace(go.Scatter(
            x=[f"Semana {s.week_number}" for s in schedule],
            y=[s.remaining_stock for s in schedule],
            name="Stock Restante (uds)",
            mode="lines+markers",
            marker=dict(color="#F87171", size=8),
            yaxis="y2",
        ))
        fig_stock.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1E293B",
            plot_bgcolor="#0F172A",
            height=280,
            yaxis=dict(title="Caja ($)", showgrid=False),
            yaxis2=dict(title="Stock Remanente", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=30, b=20, l=20, r=20),
        )
        st.plotly_chart(fig_stock, use_container_width=True)


# =============================================================================
# TAB 5: MODELO EXCEL & PIPELINE SQL
# =============================================================================
with tab5:
    st.markdown("### 📑 Modelo Corporativo en Excel con Fórmulas Encadenadas y Consultas SQL")
    st.markdown("""
    Generación de modelos financieros en **Microsoft Excel (.xlsx)** sincronizados con el motor de optimización en Python.
    Cumple con los estándares más rigurosos de **modelado financiero comercial (C-Level ready)**.
    """)

    excel_col_left, excel_col_right = st.columns([1, 1])

    with excel_col_left:
        st.markdown("#### 📥 Descargar Libro de Cálculo Corporativo")
        excel_path = "data/excel/AURA_Pricing_Engine_Executive_Model.xlsx"
        
        if os.path.exists(excel_path):
            with open(excel_path, "rb") as f:
                excel_bytes = f.read()
            st.download_button(
                label="📥 Descargar Modelo Financiero Completo (.xlsx)",
                data=excel_bytes,
                file_name="AURA_Pricing_Engine_Executive_Model.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.success(f"Archivo generado: `{excel_path}` ({len(excel_bytes)/1024:.1f} KB)")
        else:
            st.warning("El modelo aún no ha sido compilado. Ejecute `py scripts/seed_data.py`.")

        st.markdown("""
        **Arquitectura de Fórmulas Encadenadas en el Modelo:**
        1. **Búsqueda Dinámica de Costos y Elasticidades:**  
           `=VLOOKUP(A2, Catalogo_Productos!$A$2:$I$351, 6, FALSE)`
        2. **Cálculo de Fee Multicanal Dinámico:**  
           `=IF(B2="MELI_FULL", 0.14, IF(B2="D2C_SHOPIFY", 0.025, 0.01))`
        3. **Margen Bruto Unitario Dinámico ($):**  
           `=H2 - F2 - (D2 * G2)`
        4. **Lift de Equilibrio Condicional (%):**  
           `=IF(E2>=J2, 9.99, E2 / (J2 - E2))`
        5. **Dictamen de Aprobación Comercial:**  
           `=IF(S2 > 0, "APROBADA", "RECHAZADA")`
        6. **Validación de Datos Integrada:**  
           Listas desplegables para Canal y Moneda; restricción para impedir descuentos &gt; 60%.
        """)

    with excel_col_right:
        st.markdown("#### 🔍 Explorador de Consultas SQL Analíticas")
        sql_choice = st.selectbox(
            "Seleccionar Consulta Analítica en SQLite:",
            [
                "Análisis de Coherencia Multicanal & Canibalización",
                "Diagnóstico de Margen a 90 Días",
                "Waterfall Financiero Mensual (24M)",
                "Auditoría de Inventario y Dead Stock",
            ]
        )

        query_map = {
            "Análisis de Coherencia Multicanal & Canibalización": RetailAnalyticsQueries.get_omnichannel_price_coherence(),
            "Diagnóstico de Margen a 90 Días": RetailAnalyticsQueries.get_margin_health_90d(),
            "Waterfall Financiero Mensual (24M)": RetailAnalyticsQueries.get_monthly_financial_waterfall(),
            "Auditoría de Inventario y Dead Stock": RetailAnalyticsQueries.get_slow_moving_inventory(),
        }

        selected_sql = query_map[sql_choice]
        st.code(selected_sql, language="sql")

        df_query_result = get_repository().execute_query(selected_sql)
        st.markdown(f"**Resultado de Consulta ({len(df_query_result)} registros):**")
        st.dataframe(df_query_result.head(20), use_container_width=True, height=220)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748B;'>AURA-Pricing Engine © 2026 • Diseñado para IRONSIDE, Falabella y Mercado Libre</p>", unsafe_allow_html=True)
