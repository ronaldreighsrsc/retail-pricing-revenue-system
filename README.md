# 🏷️ AURA-Pricing Engine
### Autonomous Unified Revenue Analytics & Portfolio Optimization
> **Arquitectura Empresarial de Pricing Dinámico, Elasticidad Econométrica y Revenue Management Multicanal para Retail, E-Commerce y Consumo Masivo.**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Clean Architecture](https://img.shields.io/badge/Architecture-DDD%20%2B%20Clean%20Architecture-brightgreen.svg)](https://blog.cleancoder.com/)
[![Statsmodels](https://img.shields.io/badge/Econometrics-Statsmodels%20OLS%20HC1-orange.svg)](https://www.statsmodels.org/)
[![SQLite WAL](https://img.shields.io/badge/Database-SQLite%20WAL%20%2B%20Parquet-blueviolet.svg)](https://www.sqlite.org/)
[![OpenPyXL](https://img.shields.io/badge/Excel%20Modeling-OpenPyXL%20Chained%20Formulas-green.svg)](https://openpyxl.readthedocs.io/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit%201.35%2B-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Coverage-93%25%20Pytest-success.svg)](https://docs.pytest.org/)

---

## 📌 1. Resumen Ejecutivo y Justificación Económica

En la industria de retail de bienes durables y equipamiento de entrenamiento de fuerza y fitness (inspirado en operaciones de alto volumen como **IRONSIDE Fitness, Falabella y Mercado Libre** en Chile, México y Argentina), las decisiones de fijación de precios determinan la viabilidad directa del EBITDA:

1. **El Peso Muerto del Flete (*Freight-to-Cost Ratio*):** Discos bumper, barras olímpicas y racks pesan entre 20 y 180 kg por unidad. El costo logístico de última milla representa hasta el **25% del costo de adquisición (CIF)**. Un error de fijación de precio erosiona el margen de contribución de inmediato.
2. **Superación del *Cost-Plus* Ciego:** El 80% de los retailers fija precios sumando un markup estático al costo ($P = Costo \times 1.5$). Si la demanda es inelástica, se renuncia al excedente del consumidor (*Consumer Surplus*); si es elástica, se pierde cuota frente a la competencia.
3. **Erradicación de Descuentos Deficitarios (*CyberDay / Black Friday*):** Con un margen bruto del $35\%$, un descuento del $20\%$ exige un **$133\%$ de incremento en volumen** solo para no perder dinero. AURA evalúa el **Lift de Equilibrio (*Break-Even Lift*)** antes de autorizar cualquier promoción.
4. **Liquidación Inteligente de Inventario (*Dead Stock & Markdown*):** Monitoreo continuo de días de inventario ($DIO > 180$) con una escalera descendente de rebajas escalonadas que maximiza el valor de recuperación de caja y minimiza costos de bodegaje.
5. **Armonización Multicanal:** Previene la canibalización y el arbitraje entre **Shopify D2C**, **Mercado Libre** (comisión ~14%) y **Distribuidores B2B** (gimnasios).

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 IMPACTO EN LA CUENTA DE RESULTADOS (P&L)                                │
├────────────────────────────┬─────────────────────────────┬─────────────────────────────────────────────┤
│ Palanca de Negocio         │ Variación Típica            │ Impacto en Utilidad Operativa (EBITDA)       │
├────────────────────────────┼─────────────────────────────┼─────────────────────────────────────────────┤
│ Reducción Costos Fijos     │ - 1.0%                      │ + 2.3% en EBITDA                            │
│ Aumento de Volumen Ventas  │ + 1.0%                      │ + 3.1% en EBITDA                            │
│ Reducción Costos Variables │ - 1.0%                      │ + 6.8% en EBITDA                            │
│ MEJORA DE PRICING          │ + 1.0%                      │ + 11.2% en EBITDA  <-- LA PALANCA REINA    │
└────────────────────────────┴─────────────────────────────┴─────────────────────────────────────────────┘
```

---

## 📐 2. Fundamentos Matemáticos y Econométricos

### A. Estimación de Elasticidad Precio-Demanda ($\epsilon$)
Se implementa una formulación **Log-Log (Cobb-Douglas Multivariada)** con estimación OLS y errores estándar robustos a heterocedasticidad (HC1 de White):

$$\ln(Q_{i,t}) = \alpha_i + \beta_i \ln(P_{i,t}) + \gamma_i \ln(P_{comp,t}) + \delta_i Promo_{i,t} + u_{i,t}$$

* **$\beta_i$ (Elasticidad Precio Directa):** Coeficiente $\epsilon$.
  * $\epsilon > -1.0$: **Demanda Inelástica** (oportunidad de subida de precio para expansión de margen).
  * $\epsilon < -1.0$: **Demanda Elástica** (alta sensibilidad a promociones).
* **$\gamma_i$ (Elasticidad Cruzada):** Mide grado de sustitución frente al competidor directo.

### B. Regla de Amoroso-Robinson / Lerner (Margen Óptimo)
Para condiciones de maximización de beneficio ($\max \Pi = (P - c) \cdot Q(P)$):

$$P^* = \frac{\epsilon}{1 + \epsilon} \cdot c$$

Donde $c$ es el costo marginal unitario (COGS + Flete + Comisión de plataforma).

### C. Volumen de Equilibrio Promocional (*Break-Even Volume Lift*)
Frente a una propuesta de descuento $d\%$ con margen bruto inicial $M_0 = \frac{P - c}{P}$:

$$Lift_{BE} = \frac{d}{M_0 - d}$$

Si el incremento porcentual de volumen proyectado por la elasticidad ($|\epsilon| \cdot d$) es menor que $Lift_{BE}$, **la promoción destruye valor y es vetada automáticamente**.

### D. Índice de Posicionamiento Competitivo (*Price Index - PI*)
$$PI_{i,t} = \left( \frac{P_{\text{propio}, i, t}}{P_{\text{benchmark}, i, t}} \right) \times 100$$

* $PI > 115$: **Overpriced (Alto Riesgo)** $\rightarrow$ Descuento táctico o justificación de marca.
* $105 \le PI \le 115$: **Healthy Premium** $\rightarrow$ Sostener margen, explotar servicio y garantía.
* $98 \le PI < 105$: **Competitive Parity** $\rightarrow$ Paridad de mercado.
* $PI < 95$: **Underpriced (Fuga de Margen)** $\rightarrow$ **SUBIR PRECIO** de inmediato.

---

## 🏛️ 3. Arquitectura del Sistema (Clean Architecture + DDD)

El proyecto está estructurado bajo **Domain-Driven Design (DDD)** y desacoplamiento mediante **Inversión de Dependencias (DIP)**:

```
retail-pricing-revenue-system/
│
├── data/
│   ├── raw/                               # Archivos fuente y crudos
│   ├── processed/                         # SQLite en modo WAL y Parquet columnar
│   └── excel/                             # Modelo financiero corporativo .xlsx con fórmulas
│
├── src/
│   ├── domain/                            # Entidades puras y reglas de negocio
│   │   ├── models.py                      # Dataclasses: Product, Transaction, CompetitorQuote
│   │   └── value_objects.py               # Currency, Country, Channel, MarginMetrics, PriceRange
│   │
│   ├── core/                              # Interfaces abstractas (DIP)
│   │   ├── base_repository.py             # Contrato abstracto para acceso a datos
│   │   ├── base_estimator.py              # Contrato para estimadores econométricos
│   │   └── base_optimizer.py              # Contrato para optimizadores matemáticos
│   │
│   ├── data_engine/                       # Motor de generación y persistencia de datos
│   │   ├── generator.py                   # Generador de 350 SKUs reales y 24 meses transaccionales
│   │   └── repository.py                  # Repositorio SQLite en modo WAL + exportador Parquet
│   │
│   ├── analytics/                         # Módulos matemáticos y econométricos
│   │   ├── elasticity_engine.py           # Regresiones Log-Log OLS con errores robustos HC1
│   │   ├── competitive_tracker.py         # Price Indexing y detección de arbitraje
│   │   ├── promotion_simulator.py         # Break-Even Lift y simulador de campañas CyberDay
│   │   └── markdown_optimizer.py          # Escalera de liquidación y reducción de holding cost
│   │
│   ├── reporting/                         # Automatización y modelado corporativo
│   │   ├── excel_generator.py             # Generador OpenPyXL con fórmulas encadenadas y estilos
│   │   └── sql_queries.py                 # Consultas analíticas SQL con CTEs y Window Functions
│   │
│   └── dashboard/                         # Portal de decisión ejecutiva
│       └── app.py                         # Streamlit multi-pestaña interactivo con Plotly
│
├── tests/                                 # Suite de pruebas unitarias e integración (93% coverage)
│   ├── test_competitive.py                # Validación de Price Index y arbitraje
│   ├── test_data_engine.py                # Validación de generación y CRUD de datos
│   ├── test_domain.py                     # Validación de entidades y value objects
│   ├── test_elasticity.py                 # Validación econométrica y regla de Amoroso-Robinson
│   ├── test_excel_export.py               # Validación de fórmulas encadenadas en Excel
│   ├── test_markdown.py                   # Validación de monotonía en rebajas y DIO
│   ├── test_promotions.py                 # Validación estricta de Break-Even Lift
│   └── test_sql_pipeline.py               # Validación de consultas analíticas en SQLite
│
├── scripts/
│   └── seed_data.py                       # Orquestador del pipeline de datos y generación
├── requirements.txt                       # Dependencias fijadas del proyecto
├── .gitignore                             # Exclusiones de Git
└── README.md                              # Documentación técnica ejecutiva
```

---

## 📊 4. Módulos Analíticos Principales

### 1. Motor Econométrico de Elasticidad (`elasticity_engine.py`)
* Ajusta curvas de demanda multivariadas con transformación logarítmica.
* Aísla efectos de promociones ($Promo$), precios de competidores ($P_{comp}$) y estacionalidad.
* Clasifica el catálogo en regímenes: Inelástico, Elástico o Unitario, recomendando el markup óptimo de Amoroso-Robinson.

### 2. Radar de Competitividad & Price Index (`competitive_tracker.py`)
* Audita cotizaciones en tiempo real frente a **Spartan, Rogue, SDmed y Tayga**.
* Identifica de forma proactiva **oportunidades de arbitraje**: SKUs con demanda inelástica que están por debajo del precio de mercado ($PI < 95$).

### 3. Simulador de Promociones & CyberDay (`promotion_simulator.py`)
* Evalúa la viabilidad comercial de campañas individuales o portafolios completos.
* Modela el impacto de inversión en pauta de marketing (Paid Media) en el ROI neto de la campaña.
* Dictamina de forma automatizada: `APROBADA` o `RECHAZADA (Destruye Margen)`.

### 4. Algoritmo de Liquidación Dinámica (`markdown_optimizer.py`)
* Monitorea Días de Inventario ($DIO = \frac{\text{Stock} \times 365}{\text{Venta Anual}}$) identificando *Dead Stock* ($DIO > 180$).
* Modela la aceleración de demanda ($Velocity = 1.0 + |\epsilon| \cdot d$) proyectando caja recuperada y ahorro en costo de bodegaje semanal.

### 5. Modelo Financiero en Excel Corporativo (`excel_generator.py`)
Construye automáticamente un libro interactivo `.xlsx` con **fórmulas encadenadas reales**:
* `=VLOOKUP(A2, Catalogo_Productos!$A$2:$I$351, 6, FALSE)` para vincular COGS dinámicamente.
* `=IF(B2="MELI_FULL", 0.14, IF(B2="D2C_SHOPIFY", 0.025, 0.01))` para comisiones por canal.
* `=H2 - F2 - (D2 * G2)` para margen bruto unitario en pesos.
* `=IF(E2>=J2, 9.99, E2 / (J2 - E2))` para Break-Even Lift.
* `=IF(S2 > 0, "APROBADA", "RECHAZADA")` con formato condicional semafórico.
* Validación de datos: menús desplegables para Canal y Moneda; restricción para impedir descuentos mayores al 60% sin visto bueno de Gerencia.

---

## 🖥️ 5. Dashboard Ejecutivo de Decisión Comercial (Streamlit)

El portal web interactivo está estructurado en 5 pestañas ejecutivas:

1. **📊 Resumen Ejecutivo del Portafolio:**
   * Tarjetas métricas: Revenue Acumulado ($USD$), Margen Bruto Total, Elasticidad Promedio y SKUs en Riesgo.
   * Matriz de dispersión interactiva: **Margen Bruto % vs. Elasticidad Precio** (Cuadrantes estratégicos).
   * Waterfall mensual de ingresos y márgenes a lo largo de 24 meses.
2. **🎯 Radar Competitivo & Price Index:**
   * Desglose de posicionamiento (Overpriced, Premium, Paridad, Underpriced).
   * Semáforo de Price Index por marca competidora.
   * Tabla priorizada de captura de margen para SKUs inelásticos baratos.
3. **⚡ Laboratorio de Campañas & CyberDay:**
   * Selectores interactivos de SKU, sliders de descuento y presupuesto publicitario.
   * Cálculo en tiempo real de Break-Even Lift vs Lift Esperado.
   * Curva de sensibilidad: Utilidad Neta vs % Descuento.
4. **📦 Markdown Engine (Dead Stock):**
   * Auditoría de inventario crítico ($DIO > 180$ días).
   * Escalera de rebajas con proyección de unidades vendidas, stock remanente y caja liberada.
5. **📑 Modelo Excel & Pipeline SQL:**
   * Descarga directa del archivo Excel `.xlsx` corporativo.
   * Visor de consultas analíticas SQL en tiempo real sobre SQLite.

---

## 🚀 6. Guía de Puesta en Marcha (Quickstart)

### Requisitos Previos
* Python 3.11 o 3.12 instalado.
* Git.

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/ronaldreighsrsc/retail-pricing-revenue-system.git
cd retail-pricing-revenue-system

# 2. Instalar dependencias
py -m pip install -r requirements.txt
```

### Ejecutar el Pipeline de Datos y Generar el Modelo Excel

```bash
py scripts/seed_data.py
```
*Genera el catálogo de 350 SKUs, cotizaciones competitivas, 24 meses de transacciones, inicializa SQLite en modo WAL, exporta a Parquet y compila el libro Excel corporativo.*

### Iniciar el Dashboard Ejecutivo Comercial

```bash
py -m streamlit run src/dashboard/app.py
```
*Abre la interfaz ejecutiva en su navegador en `http://localhost:8501`.*

### Ejecutar la Suite de Pruebas Unitarias

```bash
py -m pytest -v --cov=src tests/
```
*Ejecuta los 23 tests de integración con un 93% de cobertura de código.*

## 🛠️ 7. Especificaciones Técnicas y Capacidades del Sistema

* **Arquitectura:** Clean Architecture + Domain-Driven Design (DDD) con Inversión de Dependencias (DIP).
* **Stack Tecnológico:** Python 3.12, Statsmodels, Pandas, SQLite (Modo WAL), Apache Parquet, OpenPyXL, Streamlit, Plotly, Pytest (93% Cobertura).
* **Capacidades Analíticas:**
  * Motor de Revenue Management multicanal (Shopify D2C, Mercado Libre, B2B) y multipaís (Chile, México, Argentina) para catálogo de +350 SKUs.
  * Modelado econométrico multivariado en log-log con errores estándar robustos HC1 para estimación de elasticidad precio-demanda ($\epsilon$) y elasticidad cruzada.
  * Simulador de promociones de alta estacionalidad con cálculo automático de Break-Even Volume Lift ($Lift_{BE} = \frac{d}{M_0 - d}$).
  * Algoritmo de liquidación dinámica (*Markdown Schedule*) con escalera de rebajas y seguimiento de Días de Inventario ($DIO > 180$).
  * Generador automatizado de modelos financieros en Excel (.xlsx) con fórmulas encadenadas (`VLOOKUP`, `IF`, validaciones) sincronizado con Dashboard interactivo en Streamlit.

---

*Licencia: MIT • Desarrollado con Clean Architecture y rigor microeconométrico.*
