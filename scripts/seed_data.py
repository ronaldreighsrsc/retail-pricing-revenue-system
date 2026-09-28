"""Pipeline execution script to generate retail data, seed SQLite, export Parquet, and build Excel model."""

import os
import sys
import time

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.data_engine.generator import RetailDataGenerator
from src.data_engine.repository import SQLiteRetailRepository
from src.reporting.excel_generator import CorporateExcelBuilder


def main():
    print("=" * 80)
    print("🚀 AURA-Pricing Engine: Ingestion & Pipeline Orchestration")
    print("=" * 80)

    start_time = time.time()
    generator = RetailDataGenerator(seed=42)

    # 1. Generate 350 SKUs
    print("\n[1/5] Generando catálogo de 350 SKUs representativos (IRONSIDE inspiration)...")
    df_products = generator.generate_products(target_sku_count=350)
    print(f"  ✓ {len(df_products)} productos generados en 5 categorías.")

    # 2. Competitor quotes
    print("\n[2/5] Generando cotizaciones de mercado de competidores (Spartan, Rogue, SDmed, Tayga)...")
    df_competitor = generator.generate_competitor_scrap(df_products)
    print(f"  ✓ {len(df_competitor)} cotizaciones competitivas generadas.")

    # 3. 24 months transactions
    print("\n[3/5] Generando transacciones multicanal (Shopify, Mercado Libre, B2B) y multipaís (CL, MX, AR)...")
    df_transactions = generator.generate_transactions(
        df_products,
        start_date="2024-10-01",
        end_date="2026-09-28",
    )
    print(f"  ✓ {len(df_transactions)} transacciones generadas en horizonte de 24 meses.")
    total_rev = df_transactions["net_revenue_usd"].sum()
    total_profit = df_transactions["gross_margin_usd"].sum()
    print(f"  ✓ Revenue Total: ${total_rev:,.2f} USD | Margen Bruto: ${total_profit:,.2f} USD ({total_profit/total_rev*100:.1f}%)")

    # 4. Seed SQLite & Export Parquet
    print("\n[4/5] Poblando SQLite en modo WAL y exportando columnar a Parquet...")
    repo = SQLiteRetailRepository("data/processed/retail_pricing.db")
    repo.seed_data(df_products, df_transactions, df_competitor)
    parquet_paths = repo.export_to_parquet("data/processed")
    print(f"  ✓ Base de datos SQLite guardada en data/processed/retail_pricing.db")
    for tbl, path in parquet_paths.items():
        print(f"  ✓ Parquet exportado: {path} ({os.path.getsize(path)/1024:.1f} KB)")

    # 5. Build Corporate Excel Model
    print("\n[5/5] Construyendo Modelo Financiero Corporativo en Excel con fórmulas encadenadas...")
    excel_path = CorporateExcelBuilder.build_full_workbook(
        df_products=df_products,
        df_competitors=df_competitor,
        output_path="data/excel/AURA_Pricing_Engine_Executive_Model.xlsx",
    )
    print(f"  ✓ Libro Excel corporativo creado: {excel_path} ({os.path.getsize(excel_path)/1024:.1f} KB)")

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"✅ Pipeline completado con éxito en {elapsed:.2f} segundos.")
    print("=" * 80)


if __name__ == "__main__":
    main()
