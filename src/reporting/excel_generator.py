"""Corporate Excel financial model builder with chained formulas, dynamic lookups, and validations."""

import os
from typing import Optional
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule
import pandas as pd


class CorporateExcelBuilder:
    """Builds enterprise-grade retail pricing and revenue optimization models in Excel."""

    NAVY_HEADER = "1A365D"
    WHITE = "FFFFFF"
    LIGHT_GRAY = "F7FAFC"
    BORDER_GRAY = "CBD5E0"
    ALERT_RED_FILL = "FED7D7"
    ALERT_RED_TEXT = "9B2C2C"
    SAFE_GREEN_FILL = "C6F6D5"
    SAFE_GREEN_TEXT = "22543D"
    WARN_YELLOW_FILL = "FEFCBF"
    WARN_YELLOW_TEXT = "744210"

    @classmethod
    def build_full_workbook(
        cls,
        df_products: pd.DataFrame,
        df_competitors: Optional[pd.DataFrame] = None,
        output_path: str = "data/excel/AURA_Pricing_Engine_Executive_Model.xlsx",
    ) -> str:
        """Constructs a multi-tab corporate financial workbook with chained formulas and validations."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        wb = openpyxl.Workbook()

        # Styles
        thin_border = Border(
            left=Side(style="thin", color=cls.BORDER_GRAY),
            right=Side(style="thin", color=cls.BORDER_GRAY),
            top=Side(style="thin", color=cls.BORDER_GRAY),
            bottom=Side(style="thin", color=cls.BORDER_GRAY),
        )
        header_fill = PatternFill(start_color=cls.NAVY_HEADER, end_color=cls.NAVY_HEADER, fill_type="solid")
        header_font = Font(name="Segoe UI", size=10, bold=True, color=cls.WHITE)
        cell_font = Font(name="Segoe UI", size=10)
        bold_font = Font(name="Segoe UI", size=10, bold=True)

        # -------------------------------------------------------------
        # Tab 1: Catalogo_Productos (Data Source for Lookups)
        # -------------------------------------------------------------
        ws_catalog = wb.active
        ws_catalog.title = "Catalogo_Productos"
        ws_catalog.views.sheetView[0].showGridLines = True

        catalog_headers = ["SKU", "Nombre", "Categoria", "Subcategoria", "Tier", "COGS_USD", "Elasticidad", "Precio_Base_USD", "Stock_Actual"]
        ws_catalog.append(catalog_headers)
        for col_idx in range(1, len(catalog_headers) + 1):
            cell = ws_catalog.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for _, row in df_products.iterrows():
            ws_catalog.append([
                row["sku"],
                row["name"],
                row["category"],
                row["sub_category"],
                row["tier_segment"],
                float(row["cogs_usd"]),
                float(row.get("true_elasticity", -1.5)),
                float(row["base_price_usd"]),
                int(row["stock_on_hand"]),
            ])

        cat_rows = len(df_products) + 1
        for r in range(2, cat_rows + 1):
            ws_catalog[f"F{r}"].number_format = '$#,##0.00'
            ws_catalog[f"G{r}"].number_format = '0.00'
            ws_catalog[f"H{r}"].number_format = '$#,##0.00'
            ws_catalog[f"I{r}"].number_format = '#,##0'
            for c in range(1, len(catalog_headers) + 1):
                cell = ws_catalog.cell(row=r, column=c)
                cell.border = thin_border
                cell.font = cell_font

        # -------------------------------------------------------------
        # Tab 2: Simulador_Pricing (Chained Formulas & Decision Engine)
        # -------------------------------------------------------------
        ws_sim = wb.create_sheet(title="Simulador_Pricing")
        ws_sim.views.sheetView[0].showGridLines = True

        sim_headers = [
            "SKU", "Canal", "Moneda", "Precio Lista ($)", "% Descuento",
            "COGS ($) [VLOOKUP]", "Fee Canal (%)", "Precio Neto ($)", "Margen Unit ($)", "% Margen",
            "Vol. Base", "Elasticidad [VLOOKUP]", "Lift Equilibrio (%)", "Lift Esperado (%)",
            "Vol. Proyectado", "Revenue Proyectado ($)", "Ganancia Proyectada ($)",
            "Ganancia Base ($)", "Ganancia Incremental ($)", "Dictamen Financiero"
        ]
        ws_sim.append(sim_headers)
        for col_idx in range(1, len(sim_headers) + 1):
            cell = ws_sim.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws_sim.row_dimensions[1].height = 32

        # Add Data Validation for Channel and Country/Currency
        channel_validation = DataValidation(type="list", formula1='"D2C_SHOPIFY,MELI_FULL,B2B_GYM"', allow_blank=False)
        ws_sim.add_data_validation(channel_validation)
        channel_validation.add("B2:B200")

        currency_validation = DataValidation(type="list", formula1='"USD,CLP,MXN,ARS"', allow_blank=False)
        ws_sim.add_data_validation(currency_validation)
        currency_validation.add("C2:C200")

        # Discount validation (between 0.0 and 0.60)
        discount_validation = DataValidation(
            type="decimal",
            operator="between",
            formula1=0.0,
            formula2=0.60,
            allow_blank=False,
            errorTitle="Descuento Excesivo",
            error="El descuento comercial no puede exceder el 60.0% sin autorización de la Gerencia General."
        )
        ws_sim.add_data_validation(discount_validation)
        discount_validation.add("E2:E200")

        # Populate top 40 SKUs with formulas
        sample_skus = df_products.head(40)
        for idx, (_, prod) in enumerate(sample_skus.iterrows(), start=2):
            sku_val = prod["sku"]
            channel_val = "D2C_SHOPIFY" if idx % 2 == 0 else "MELI_FULL"
            disc_val = 0.15 if idx % 3 == 0 else (0.20 if idx % 5 == 0 else 0.10)
            base_vol = 120 if idx % 2 == 0 else 80

            # Cell values & Chained Formulas:
            # A: SKU
            # B: Canal
            # C: Moneda
            # D: Precio Lista
            # E: % Descuento
            # F: COGS via VLOOKUP: =VLOOKUP(A{row}, Catalogo_Productos!$A$2:$I${cat_rows}, 6, FALSE)
            # G: Fee Canal: =IF(B{row}="MELI_FULL", 0.14, IF(B{row}="D2C_SHOPIFY", 0.025, 0.01))
            # H: Precio Neto: =D{row}*(1-E{row})
            # I: Margen Unit ($): =H{row}-F{row}-(D{row}*G{row})
            # J: % Margen: =I{row}/H{row}
            # K: Vol. Base: base_vol
            # L: Elasticidad via VLOOKUP: =VLOOKUP(A{row}, Catalogo_Productos!$A$2:$I${cat_rows}, 7, FALSE)
            # M: Lift Equilibrio: =IF(E{row}>=J{row}, 9.99, E{row}/(J{row}-E{row}))
            # N: Lift Esperado: =ABS(L{row})*E{row}
            # O: Vol. Proyectado: =ROUND(K{row}*(1+N{row}), 0)
            # P: Revenue Proyectado: =H{row}*O{row}
            # Q: Ganancia Proyectada: =I{row}*O{row}
            # R: Ganancia Base: =(D{row}-F{row}-(D{row}*G{row}))*K{row}
            # S: Ganancia Incremental: =Q{row}-R{row}
            # T: Dictamen: =IF(S{row}>0, "APROBADA", "RECHAZADA")

            row_cells = [
                sku_val,
                channel_val,
                "USD",
                float(prod["base_price_usd"]),
                disc_val,
                f'=VLOOKUP(A{idx}, Catalogo_Productos!$A$2:$I${cat_rows}, 6, FALSE)',
                f'=IF(B{idx}="MELI_FULL", 0.14, IF(B{idx}="D2C_SHOPIFY", 0.025, 0.01))',
                f'=D{idx}*(1-E{idx})',
                f'=H{idx}-F{idx}-(D{idx}*G{idx})',
                f'=I{idx}/H{idx}',
                base_vol,
                f'=VLOOKUP(A{idx}, Catalogo_Productos!$A$2:$I${cat_rows}, 7, FALSE)',
                f'=IF(E{idx}>=J{idx}, 9.99, E{idx}/(J{idx}-E{idx}))',
                f'=ABS(L{idx})*E{idx}',
                f'=ROUND(K{idx}*(1+N{idx}), 0)',
                f'=H{idx}*O{idx}',
                f'=I{idx}*O{idx}',
                f'=(D{idx}-F{idx}-(D{idx}*G{idx}))*K{idx}',
                f'=Q{idx}-R{idx}',
                f'=IF(S{idx}>0, "APROBADA", "RECHAZADA")',
            ]
            ws_sim.append(row_cells)

            # Number formats
            ws_sim[f"D{idx}"].number_format = '$#,##0.00'
            ws_sim[f"E{idx}"].number_format = '0.0%'
            ws_sim[f"F{idx}"].number_format = '$#,##0.00'
            ws_sim[f"G{idx}"].number_format = '0.0%'
            ws_sim[f"H{idx}"].number_format = '$#,##0.00'
            ws_sim[f"I{idx}"].number_format = '$#,##0.00'
            ws_sim[f"J{idx}"].number_format = '0.0%'
            ws_sim[f"K{idx}"].number_format = '#,##0'
            ws_sim[f"L{idx}"].number_format = '0.00'
            ws_sim[f"M{idx}"].number_format = '0.0%'
            ws_sim[f"N{idx}"].number_format = '0.0%'
            ws_sim[f"O{idx}"].number_format = '#,##0'
            ws_sim[f"P{idx}"].number_format = '$#,##0.00'
            ws_sim[f"Q{idx}"].number_format = '$#,##0.00'
            ws_sim[f"R{idx}"].number_format = '$#,##0.00'
            ws_sim[f"S{idx}"].number_format = '$#,##0.00'

            for c in range(1, len(sim_headers) + 1):
                cell = ws_sim.cell(row=idx, column=c)
                cell.border = thin_border
                cell.font = cell_font

        # Conditional formatting for Decision column
        green_rule = CellIsRule(operator="equal", formula=['"APROBADA"'], stopIfTrue=True,
                                fill=PatternFill(start_color=cls.SAFE_GREEN_FILL, end_color=cls.SAFE_GREEN_FILL, fill_type="solid"),
                                font=Font(name="Segoe UI", size=10, bold=True, color=cls.SAFE_GREEN_TEXT))
        red_rule = CellIsRule(operator="equal", formula=['"RECHAZADA"'], stopIfTrue=True,
                              fill=PatternFill(start_color=cls.ALERT_RED_FILL, end_color=cls.ALERT_RED_FILL, fill_type="solid"),
                              font=Font(name="Segoe UI", size=10, bold=True, color=cls.ALERT_RED_TEXT))
        ws_sim.conditional_formatting.add("T2:T45", green_rule)
        ws_sim.conditional_formatting.add("T2:T45", red_rule)

        # -------------------------------------------------------------
        # Tab 3: Resumen_Ejecutivo_PL (KPIs and Totals)
        # -------------------------------------------------------------
        ws_exec = wb.create_sheet(title="Resumen_Ejecutivo_PL")
        ws_exec.views.sheetView[0].showGridLines = True

        ws_exec["A1"] = "PANEL DE CONTROL FINANCIERO - IMPACTO EN P&L"
        ws_exec["A1"].font = Font(name="Segoe UI", size=14, bold=True, color=cls.NAVY_HEADER)
        ws_exec.merge_cells("A1:E1")

        kpis = [
            ("Métrica Clave de Campaña", "Fórmula Encadenada / Valor", "Formato"),
            ("Revenue Proyectado de Campaña ($)", "=SUM(Simulador_Pricing!P2:P41)", "$#,##0.00"),
            ("Ganancia Bruta Proyectada ($)", "=SUM(Simulador_Pricing!Q2:Q41)", "$#,##0.00"),
            ("Ganancia Bruta Línea Base ($)", "=SUM(Simulador_Pricing!R2:R41)", "$#,##0.00"),
            ("Ganancia Incremental Neta ($)", "=B3-B4", "$#,##0.00"),
            ("Margen Bruto Ponderado Campaña (%)", "=B3/B2", "0.0%"),
            ("Promociones Aprobadas", '=COUNTIF(Simulador_Pricing!T2:T41, "APROBADA")', '#,##0'),
            ("Promociones Rechazadas (Veto Margen)", '=COUNTIF(Simulador_Pricing!T2:T41, "RECHAZADA")', '#,##0'),
            ("Tasa de Aprobación de Campaña (%)", "=B7/(B7+B8)", "0.0%"),
        ]

        for r_idx, (label, formula_or_val, fmt) in enumerate(kpis, start=3):
            cell_label = ws_exec.cell(row=r_idx, column=1, value=label)
            cell_val = ws_exec.cell(row=r_idx, column=2, value=formula_or_val)
            
            if r_idx == 3:
                cell_label.fill = header_fill
                cell_label.font = header_font
                cell_val.fill = header_fill
                cell_val.font = header_font
            else:
                cell_label.font = bold_font
                cell_val.font = bold_font
                cell_val.number_format = fmt
                cell_label.border = thin_border
                cell_val.border = thin_border

        # -------------------------------------------------------------
        # Tab 4: Benchmark_Competitivo (Price Index Analysis)
        # -------------------------------------------------------------
        if df_competitors is not None and not df_competitors.empty:
            ws_comp = wb.create_sheet(title="Benchmark_Competitivo")
            ws_comp.views.sheetView[0].showGridLines = True

            comp_headers = ["SKU", "Competidor", "País", "Precio Nuestro (USD)", "Precio Competidor (USD)", "Price Index (%)", "Posicionamiento"]
            ws_comp.append(comp_headers)
            for c_idx in range(1, len(comp_headers) + 1):
                cell = ws_comp.cell(row=1, column=c_idx)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # Merge with product base price
            merged_comp = pd.merge(df_competitors.head(100), df_products[["sku", "base_price_usd"]], on="sku", how="left")
            for c_r_idx, (_, c_row) in enumerate(merged_comp.iterrows(), start=2):
                ws_comp.append([
                    c_row["sku"],
                    c_row["competitor_brand"],
                    c_row["country_id"],
                    float(c_row["base_price_usd"]),
                    float(c_row["competitor_price_usd"]),
                    f'=(D{c_r_idx}/E{c_r_idx})*100',
                    f'=IF(F{c_r_idx}>115, "Overpriced", IF(F{c_r_idx}>=105, "Healthy Premium", IF(F{c_r_idx}>=95, "Competitive Parity", "Underpriced")))',
                ])
                ws_comp[f"D{c_r_idx}"].number_format = '$#,##0.00'
                ws_comp[f"E{c_r_idx}"].number_format = '$#,##0.00'
                ws_comp[f"F{c_r_idx}"].number_format = '0.0'
                for c in range(1, len(comp_headers) + 1):
                    cell = ws_comp.cell(row=c_r_idx, column=c)
                    cell.border = thin_border
                    cell.font = cell_font

        # Auto-adjust column widths across all worksheets
        for ws in wb.worksheets:
            for col in ws.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    val_str = str(cell.value or "")
                    if len(val_str) > max_len and not str(cell.value or "").startswith("="):
                        max_len = len(val_str)
                ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

        wb.save(output_path)
        return output_path
