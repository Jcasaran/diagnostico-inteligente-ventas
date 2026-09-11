"""Interactive Streamlit dashboard for the sales diagnostic."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.sales_diagnostics import (
    OPEN_STAGES,
    build_recommendations,
    calculate_kpis,
    load_crm_data,
    rep_performance,
)


ROOT = Path(__file__).resolve().parent
SAMPLE_DATA = ROOT / "data" / "crm_opportunities.csv"

st.set_page_config(page_title="Diagnóstico Inteligente de Ventas", page_icon="📊", layout="wide")
st.title("📊 Diagnóstico Inteligente de Ventas")
st.caption("De una exportación del CRM a decisiones comerciales accionables")

with st.sidebar:
    st.header("Datos")
    uploaded = st.file_uploader("Carga un CSV de oportunidades", type="csv")
    source = uploaded if uploaded is not None else SAMPLE_DATA
    st.info("Se muestran datos simulados mientras no cargues un archivo.")

try:
    df = load_crm_data(source)
except (ValueError, pd.errors.ParserError) as exc:
    st.error(f"No fue posible procesar el archivo: {exc}")
    st.stop()

with st.sidebar:
    countries = st.multiselect("País", sorted(df["country"].dropna().unique()))
    reps = st.multiselect("Ejecutivo", sorted(df["sales_rep"].dropna().unique()))

filtered = df.copy()
if countries:
    filtered = filtered[filtered["country"].isin(countries)]
if reps:
    filtered = filtered[filtered["sales_rep"].isin(reps)]

if filtered.empty:
    st.warning("No hay oportunidades para los filtros seleccionados.")
    st.stop()

kpis = calculate_kpis(filtered)
cols = st.columns(5)
cols[0].metric("Pipeline abierto", f"USD {kpis.open_pipeline_usd:,.0f}")
cols[1].metric("Forecast ponderado", f"USD {kpis.weighted_pipeline_usd:,.0f}")
cols[2].metric("Tasa de cierre", f"{kpis.win_rate:.1%}")
cols[3].metric("Ticket promedio", f"USD {kpis.average_ticket_usd:,.0f}")
cols[4].metric("Estancadas", f"{kpis.stalled_opportunities}")

left, right = st.columns(2)
stage_order = [*OPEN_STAGES, "Closed Won", "Closed Lost"]
stage_summary = (
    filtered.groupby("stage", as_index=False)
    .agg(opportunities=("opportunity_id", "count"), amount_usd=("amount_usd", "sum"))
)
with left:
    st.subheader("Embudo por etapa")
    fig = px.funnel(
        stage_summary,
        y="stage",
        x="opportunities",
        category_orders={"stage": stage_order},
        labels={"stage": "Etapa", "opportunities": "Oportunidades"},
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Pipeline por industria")
    open_df = filtered[filtered["stage"].isin(OPEN_STAGES)]
    industry = open_df.groupby("industry", as_index=False)["amount_usd"].sum()
    fig = px.bar(
        industry.sort_values("amount_usd"),
        x="amount_usd",
        y="industry",
        orientation="h",
        labels={"amount_usd": "Pipeline (USD)", "industry": "Industria"},
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Desempeño por ejecutivo")
performance = rep_performance(filtered)
display = performance.copy()
display["win_rate"] = display["win_rate"].map(lambda value: f"{value:.1%}")
st.dataframe(display, use_container_width=True, hide_index=True)

st.subheader("Oportunidades estancadas")
stalled = filtered[filtered["is_stalled"]].sort_values("amount_usd", ascending=False)
st.dataframe(
    stalled[
        [
            "opportunity_id",
            "sales_rep",
            "stage",
            "amount_usd",
            "expected_close_date",
            "days_without_activity",
        ]
    ].head(25),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Recomendaciones")
for recommendation in build_recommendations(filtered, kpis):
    st.write(f"- {recommendation}")
