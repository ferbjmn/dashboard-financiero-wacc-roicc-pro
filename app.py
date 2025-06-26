import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
import time
from datetime import datetime, timedelta

# Parámetros WACC
Rf = 0.0435
Rm = 0.085
Tc = 0.21

def calcular_wacc(info, balance_sheet):
    try:
        beta = info.get("beta")
        price = info.get("currentPrice")
        shares = info.get("sharesOutstanding")
        market_cap = price * shares if price and shares else None
        lt_debt = balance_sheet.loc["Long Term Debt", :].iloc[0] if "Long Term Debt" in balance_sheet.index else 0
        st_debt = balance_sheet.loc["Short Long Term Debt", :].iloc[0] if "Short Long Term Debt" in balance_sheet.index else 0
        total_debt = lt_debt + st_debt
        Re = Rf + beta * (Rm - Rf) if beta is not None else None
        Rd = 0.055 if total_debt > 0 else 0
        E = market_cap
        D = total_debt

        if None in [Re, E, D] or E + D == 0:
            return None, total_debt

        wacc = (E / (E + D)) * Re + (D / (E + D)) * Rd * (1 - Tc)
        return wacc, total_debt
    except:
        return None, None

def calcular_crecimiento_historico(financials, metric):
    try:
        if metric not in financials.index:
            return None
        datos = financials.loc[metric].dropna().iloc[:4]
        if len(datos) < 2:
            return None
        primer_valor = datos.iloc[-1]
        ultimo_valor = datos.iloc[0]
        años = len(datos) - 1
        if primer_valor == 0:
            return None
        cagr = (ultimo_valor / primer_valor) ** (1 / años) - 1
        return cagr
    except:
        return None

def get_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        bs = stock.balance_sheet
        fin = stock.financials
        cf = stock.cashflow

        price = info.get("currentPrice")
        name = info.get("longName")
        sector = info.get("sector")
        country = info.get("country")
        industry = info.get("industry")
        pe = info.get("trailingPE")
        pb = info.get("priceToBook")
        dividend = info.get("dividendRate")
        dividend_yield = info.get("dividendYield")
        payout = info.get("payoutRatio")
        roa = info.get("returnOnAssets")
        roe = info.get("returnOnEquity")
        current_ratio = info.get("currentRatio")
        ltde = info.get("longTermDebtEquity")
        de = info.get("debtToEquity")
        op_margin = info.get("operatingMargins")
        profit_margin = info.get("netMargins")

        fcf = cf.loc["Total Cash From Operating Activities"].iloc[0] if "Total Cash From Operating Activities" in cf.index else None
        shares = info.get("sharesOutstanding")
        pfcf = price / (fcf / shares) if fcf and shares else None

        ebit = fin.loc["EBIT"].iloc[0] if "EBIT" in fin.index else None
        equity = bs.loc["Total Stockholder Equity"].iloc[0] if "Total Stockholder Equity" in bs.index else None

        wacc, total_debt = calcular_wacc(info, bs)
        capital_invertido = total_debt + equity if total_debt and equity else None
        roic = ebit / capital_invertido if ebit and capital_invertido else None
        eva = roic - wacc if roic and wacc else None

        revenue_growth = calcular_crecimiento_historico(fin, "Total Revenue")
        eps_growth = calcular_crecimiento_historico(fin, "Net Income")
        fcf_growth = calcular_crecimiento_historico(cf, "Free Cash Flow") or calcular_crecimiento_historico(cf, "Total Cash From Operating Activities")

        quick_ratio = info.get("quickRatio")
        cash_ratio = info.get("cashRatio")
        operating_cash_flow = cf.loc["Total Cash From Operating Activities"].iloc[0] if "Total Cash From Operating Activities" in cf.index else None
        current_liabilities = bs.loc["Total Current Liabilities"].iloc[0] if "Total Current Liabilities" in bs.index else None
        cash_flow_ratio = operating_cash_flow / current_liabilities if operating_cash_flow and current_liabilities else None

        return {
            "Ticker": ticker,
            "Nombre": name,
            "Sector": sector,
            "País": country,
            "Industria": industry,
            "Precio": price,
            "P/E": pe,
            "P/B": pb,
            "P/FCF": pfcf,
            "Dividend Year": dividend,
            "Dividend Yield %": dividend_yield,
            "Payout Ratio": payout,
            "ROA": roa,
            "ROE": roe,
            "Current Ratio": current_ratio,
            "LtDebt/Eq": ltde,
            "Debt/Eq": de,
            "Oper Margin": op_margin,
            "Profit Margin": profit_margin,
            "WACC": wacc,
            "ROIC": roic,
            "EVA": eva,
            "Deuda Total": total_debt,
            "Patrimonio Neto": equity,
            "Revenue Growth": revenue_growth,
            "EPS Growth": eps_growth,
            "FCF Growth": fcf_growth,
            "Quick Ratio": quick_ratio,
            "Cash Ratio": cash_ratio,
            "Cash Flow Ratio": cash_flow_ratio,
            "Operating Cash Flow": operating_cash_flow,
            "Current Liabilities": current_liabilities,
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Configuración inicial
if "resultados" not in st.session_state:
    st.session_state["resultados"] = {}

st.set_page_config(page_title="Dashboard Financiero", layout="wide")
st.title("📊 Dashboard de Análisis Financiero")

# Input de tickers
st.markdown("## 📋 Sección 1: Ratios Financieros Generales")
tickers_input = st.text_area("🔎 Ingresa hasta 50 tickers separados por coma", "AAPL,MSFT,GOOGL,TSLA,AMZN")
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()][:50]

if st.button("🔍 Analizar"):
    nuevos = [t for t in tickers if t not in st.session_state["resultados"]]
    for i, t in enumerate(nuevos):
        st.write(f"⏳ Procesando {t} ({i+1}/{len(nuevos)})...")
        st.session_state["resultados"][t] = get_data(t)
        time.sleep(1.5)

# Mostrar DataFrame general
if st.session_state["resultados"]:
    datos = list(st.session_state["resultados"].values())
    df = pd.DataFrame(datos).drop(columns=["Deuda Total", "Patrimonio Neto", "Error"], errors="ignore")
    st.dataframe(df, use_container_width=True)

# Sección 2: Solvencia
st.markdown("## 💳 Sección 2: Análisis de Solvencia de Deuda")
for detalle in st.session_state["resultados"].values():
    if "Error" in detalle:
        continue
    nombre = detalle.get("Nombre", detalle["Ticker"])
    deuda = detalle.get("Deuda Total", 0)
    patrimonio = detalle.get("Patrimonio Neto", 0)
    if deuda is None or patrimonio is None:
        conclusion = "❓ Datos insuficientes para determinar la solvencia."
    elif patrimonio >= deuda:
        conclusion = f"✅ *Solvente*: el patrimonio neto (${patrimonio:,.0f}) supera la deuda total (${deuda:,.0f})."
    else:
        conclusion = f"❌ *No solvente*: la deuda total (${deuda:,.0f}) supera el patrimonio neto (${patrimonio:,.0f})."

    st.markdown(f"### 📌 {nombre}")
    df_plot = pd.DataFrame({"Categoría": ["Deuda Total", "Patrimonio Neto"], "Valor (USD)": [deuda, patrimonio]})
    fig, ax = plt.subplots()
    ax.bar(df_plot["Categoría"], df_plot["Valor (USD)"], width=0.4)
    ax.set_ylabel("USD")
    ax.set_title("Comparativa: Deuda vs Patrimonio")
    st.pyplot(fig)
    plt.close(fig)
    st.dataframe(df_plot.set_index("Categoría"))
    st.markdown(f"*Conclusión:* {conclusion}")
    st.markdown("---")

# Sección 3: ROIC vs WACC
st.markdown("## 💡 Sección 3: Análisis de Creación de Valor (ROIC vs WACC)")
for detalle in st.session_state["resultados"].values():
    if "Error" in detalle:
        continue
    nombre = detalle.get("Nombre", detalle["Ticker"])
    roic = detalle.get("ROIC")
    wacc = detalle.get("WACC")
    if roic is None or wacc is None:
        conclusion = "❓ Datos insuficientes para calcular ROIC o WACC."
    elif roic > wacc:
        conclusion = f"✅ *Crea valor*: ROIC ({roic:.2%}) > WACC ({wacc:.2%})"
    elif roic == wacc:
        conclusion = f"⚠️ *Margen neutro*: ROIC ({roic:.2%}) = WACC ({wacc:.2%})"
    else:
        conclusion = f"❌ *Destruye valor*: ROIC ({roic:.2%}) < WACC ({wacc:.2%})"

    st.markdown(f"### 📌 {nombre}")
    df_val = pd.DataFrame({"Ratio": ["ROIC", "WACC"], "Valor (%)": [roic * 100 if roic else 0, wacc * 100 if wacc else 0]})
    fig, ax = plt.subplots()
    ax.bar(df_val["Ratio"], df_val["Valor (%)"], color=["green" if roic and roic > wacc else "red", "gray"])
    ax.set_ylabel("%")
    ax.set_title("ROIC vs WACC")
    st.pyplot(fig)
    plt.close(fig)
    st.markdown(f"*Conclusión:* {conclusion}")
    st.markdown("---")

# Sección 5: Crecimiento
st.markdown("## 📈 Sección 5: Análisis de Crecimiento")
for detalle in st.session_state["resultados"].values():
    if "Error" in detalle:
        continue
    nombre = detalle.get("Nombre", detalle["Ticker"])
    revenue_growth = detalle.get("Revenue Growth")
    eps_growth = detalle.get("EPS Growth")
    fcf_growth = detalle.get("FCF Growth")

    st.markdown(f"### 📌 {nombre}")
    fig, ax = plt.subplots()
    metrics = ["Ingresos", "EPS", "FCF"]
    growth_rates = [revenue_growth, eps_growth, fcf_growth]
    growth_pct = [g * 100 if g else 0 for g in growth_rates]
    colors = ["green" if g > 0 else "red" for g in growth_pct]

    bars = ax.bar(metrics, growth_pct, color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("CAGR (%)")
    ax.set_title("Tasas de Crecimiento Histórico")
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("*Análisis de Crecimiento:*")
    if None in [revenue_growth, eps_growth, fcf_growth]:
        st.write("❓ Datos insuficientes para un análisis completo de crecimiento.")
    else:
        if revenue_growth > 0 and eps_growth > 0 and fcf_growth > 0:
            st.write("✅ *Crecimiento consistente*: Todas las métricas muestran crecimiento positivo.")
        else:
            st.write("⚠️ *Crecimiento inconsistente*: Algunas métricas son negativas.")

        if fcf_growth > eps_growth > revenue_growth:
            st.write("💰 *Alta calidad de crecimiento*: FCF > EPS > Ingresos.")
        elif eps_growth > revenue_growth:
            st.write("📊 *Crecimiento eficiente*: EPS > Ingresos.")
        else:
            st.write("📉 *Crecimiento débil*: Ingresos crecen más que EPS.")

    st.markdown("---")

# Sección 6: Liquidez Avanzada
st.markdown("## 💰 Sección 6: Análisis de Liquidez Avanzada")
for detalle in st.session_state["resultados"].values():
    if "Error" in detalle:
        continue
    nombre = detalle.get("Nombre", detalle["Ticker"])
    current_ratio = detalle.get("Current Ratio")
    quick_ratio = detalle.get("Quick Ratio")
    cash_ratio = detalle.get("Cash Ratio")
    cash_flow_ratio = detalle.get("Cash Flow Ratio")
    operating_cash_flow = detalle.get("Operating Cash Flow")
    current_liabilities = detalle.get("Current Liabilities")

    st.markdown(f"### 📌 {nombre}")
    metrics = ["Current", "Quick", "Cash", "Cash Flow"]
    ratios = [current_ratio, quick_ratio, cash_ratio, cash_flow_ratio]
    values = [r if r else 0 for r in ratios]
    colors = ["green" if r and r > 1 else "orange" if r and r > 0.5 else "red" for r in values]

    fig, ax = plt.subplots()
    bars = ax.bar(metrics, values, color=colors)
    ax.set_ylabel("Ratio")
    ax.set_title("Ratios de Liquidez")
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("*Evaluación de Liquidez:*")
    if None in ratios:
        st.write("❓ Datos insuficientes para evaluación completa.")
    else:
        if all([current_ratio > 1.5, quick_ratio > 1, cash_ratio > 0.5, cash_flow_ratio > 0.4]):
            st.write("🛡️ *Excelente liquidez*")
        elif any([current_ratio < 1, quick_ratio < 0.5, cash_ratio < 0.2, cash_flow_ratio < 0.2]):
            st.write("⚠️ *Liquidez preocupante*")
        else:
            st.write("🔄 *Liquidez aceptable*")

        if operating_cash_flow and current_liabilities:
            st.write(f"- Flujo de caja operativo: ${operating_cash_flow:,.0f} ≈ {(operating_cash_flow/current_liabilities):.1f}x pasivos corrientes")

    st.markdown("---")
