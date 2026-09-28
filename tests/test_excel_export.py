"""Unit tests for corporate Excel model generation and formula validation."""

import os
import openpyxl
import pandas as pd
import pytest
from src.reporting.excel_generator import CorporateExcelBuilder


def test_excel_workbook_generation_and_formula_integrity(tmp_path):
    """Validates that Excel workbook contains all required tabs, styles, and chained formulas."""
    test_file = str(tmp_path / "test_pricing_model.xlsx")

    df_products = pd.DataFrame([
        {
            "sku": f"IRN-TEST-{i:03d}",
            "name": f"Product {i}",
            "category": "Fuerza Libre",
            "sub_category": "Barras",
            "tier_segment": "Better",
            "cogs_usd": 50.0 + i,
            "base_price_usd": 100.0 + (i * 2),
            "true_elasticity": -1.5,
            "stock_on_hand": 80,
        }
        for i in range(1, 10)
    ])

    df_comp = pd.DataFrame([
        {
            "sku": "IRN-TEST-001",
            "competitor_brand": "Rogue",
            "country_id": "CL",
            "competitor_price_usd": 115.0,
        }
    ])

    saved_path = CorporateExcelBuilder.build_full_workbook(
        df_products=df_products,
        df_competitors=df_comp,
        output_path=test_file,
    )

    assert os.path.exists(saved_path)
    wb = openpyxl.load_workbook(saved_path, data_only=False)

    # 1. Validate required sheets
    expected_sheets = ["Catalogo_Productos", "Simulador_Pricing", "Resumen_Ejecutivo_PL", "Benchmark_Competitivo"]
    for s in expected_sheets:
        assert s in wb.sheetnames

    # 2. Validate formulas in Simulador_Pricing
    ws_sim = wb["Simulador_Pricing"]
    # Column F should contain VLOOKUP for COGS
    f2_val = str(ws_sim["F2"].value)
    assert f2_val.startswith("=VLOOKUP")
    assert "Catalogo_Productos" in f2_val

    # Column I should contain formula for Unit Margin
    i2_val = str(ws_sim["I2"].value)
    assert "=" in i2_val

    # Column T should contain decision formula
    t2_val = str(ws_sim["T2"].value)
    assert t2_val.startswith("=IF")
    assert "APROBADA" in t2_val

    # 3. Validate KPI formulas in Resumen_Ejecutivo_PL
    ws_exec = wb["Resumen_Ejecutivo_PL"]
    b4_val = str(ws_exec["B4"].value)
    assert b4_val.startswith("=SUM")
