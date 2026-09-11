"""Dashboard interactivo y personalizable para el diagnóstico comercial."""

from io import StringIO
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
INPUT_COLUMNS = [
    "opportunity_id",
    "created_date",
    "expected_close_date",
    "close_date",
    "stage",
    "amount_usd",
    "sales_rep",
    "industry",
    "country",
    "lead_source",
    "last_activity_date",
    "loss_reason",
]
LATAM_COUNTRIES = [
    "Argentina",
    "Bolivia",
    "Brasil",
    "Chile",
    "Colombia",
    "Costa Rica",
    "Ecuador",
    "El Salvador",
    "Guatemala",
    "Honduras",
    "México",
    "Nicaragua",
    "Panamá",
    "Paraguay",
    "Perú",
    "República Dominicana",
    "Uruguay",
    "Venezuela",
]
STAGES = ["Qualification", "Discovery", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
STAGE_LABELS = {
    "Qualification": "Calificación",
    "Discovery": "Descubrimiento",
    "Proposal": "Propuesta",
    "Negotiation": "Negociación",
    "Closed Won": "Ganada",
    "Closed Lost": "Perdida",
}
INDUSTRIES = ["Tecnología", "Servicios", "Retail", "Seguros", "Finanzas", "Logística", "Salud", "Educación"]
LEAD_SOURCES = ["Outbound", "Inbound", "Referido", "Evento", "Partner"]
LOSS_REASONS = ["Precio", "Sin prioridad", "Competencia", "Sin presupuesto", "No decision"]


def enrich_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Reuse the same validation pipeline after a user adds a row."""
    buffer = StringIO()
    raw_df[INPUT_COLUMNS].to_csv(buffer, index=False, date_format="%Y-%m-%d")
    buffer.seek(0)
    return load_crm_data(buffer)


def reset_workspace(df: pd.DataFrame) -> None:
    """Initialize editable session data and its catalogs."""
    st.session_state.crm_df = df
    st.session_state.executives = sorted(df["sales_rep"].dropna().unique().tolist())
    data_countries = df["country"].dropna().unique().tolist()
    st.session_state.countries = sorted(set(LATAM_COUNTRIES + data_countries))
    st.session_state.upload_signature = None


st.set_page_config(page_title="Diagnóstico Inteligente de Ventas", page_icon="📊", layout="wide")

if "crm_df" not in st.session_state:
    reset_workspace(load_crm_data(SAMPLE_DATA))

st.title("📊 Diagnóstico Inteligente de Ventas")
st.caption("Personaliza tu equipo, registra oportunidades y convierte datos del CRM en decisiones comerciales")

with st.sidebar:
    st.header("Fuente de datos")
    uploaded = st.file_uploader("Cargar CSV de oportunidades", type="csv")
    if uploaded is not None:
        signature = hash(uploaded.getvalue())
        if signature != st.session_state.upload_signature:
            try:
                uploaded_df = load_crm_data(uploaded)
                reset_workspace(uploaded_df)
                st.session_state.upload_signature = signature
                st.success("Archivo cargado correctamente.")
            except (ValueError, pd.errors.ParserError) as exc:
                st.error(f"No fue posible procesar el archivo: {exc}")

    if st.button("Restablecer datos de demostración", use_container_width=True):
        reset_workspace(load_crm_data(SAMPLE_DATA))
        st.rerun()

    st.divider()
    st.header("Personalización")
    with st.expander("Equipo comercial", expanded=True):
        new_rep = st.text_input("Nombre del nuevo ejecutivo", placeholder="Ej. Javier Casaran")
        if st.button("Agregar ejecutivo", use_container_width=True):
            cleaned_rep = new_rep.strip()
            if not cleaned_rep:
                st.warning("Escribe el nombre del ejecutivo.")
            elif cleaned_rep in st.session_state.executives:
                st.info("Ese ejecutivo ya está en la lista.")
            else:
                st.session_state.executives.append(cleaned_rep)
                st.session_state.executives.sort()
                st.success(f"Ejecutivo agregado: {cleaned_rep}")

        st.caption("Ejecutivos disponibles")
        st.write(" · ".join(st.session_state.executives))

    with st.expander("Países y mercados"):
        new_country = st.text_input("Agregar otro país", placeholder="Ej. España")
        if st.button("Agregar país", use_container_width=True):
            cleaned_country = new_country.strip()
            if not cleaned_country:
                st.warning("Escribe el nombre del país.")
            elif cleaned_country in st.session_state.countries:
                st.info("Ese país ya está en la lista.")
            else:
                st.session_state.countries.append(cleaned_country)
                st.session_state.countries.sort()
                st.success(f"País agregado: {cleaned_country}")
        st.caption(f"{len(st.session_state.countries)} países disponibles")

df = st.session_state.crm_df
dashboard_tab, opportunity_tab, data_tab = st.tabs(
    ["📈 Dashboard", "➕ Registrar oportunidad", "🗂️ Datos y descarga"]
)

with dashboard_tab:
    filter_left, filter_right = st.columns(2)
    with filter_left:
        countries = st.multiselect(
            "Filtrar por país",
            st.session_state.countries,
            placeholder="Todos los países",
        )
    with filter_right:
        reps = st.multiselect(
            "Filtrar por ejecutivo",
            st.session_state.executives,
            placeholder="Todos los ejecutivos",
        )

    filtered = df.copy()
    if countries:
        filtered = filtered[filtered["country"].isin(countries)]
    if reps:
        filtered = filtered[filtered["sales_rep"].isin(reps)]

    if filtered.empty:
        st.warning("No hay oportunidades para los filtros seleccionados.")
    else:
        kpis = calculate_kpis(filtered)
        cols = st.columns(5)
        cols[0].metric("Pipeline abierto", f"USD {kpis.open_pipeline_usd:,.0f}")
        cols[1].metric("Forecast ponderado", f"USD {kpis.weighted_pipeline_usd:,.0f}")
        cols[2].metric("Tasa de cierre", f"{kpis.win_rate:.1%}")
        cols[3].metric("Ticket promedio", f"USD {kpis.average_ticket_usd:,.0f}")
        cols[4].metric("Estancadas", f"{kpis.stalled_opportunities}")

        left, right = st.columns(2)
        stage_summary = filtered.groupby("stage", as_index=False).agg(
            opportunities=("opportunity_id", "count"), amount_usd=("amount_usd", "sum")
        )
        stage_summary["etapa"] = stage_summary["stage"].map(STAGE_LABELS)
        with left:
            st.subheader("Embudo por etapa")
            fig = px.funnel(
                stage_summary,
                y="etapa",
                x="opportunities",
                category_orders={"etapa": list(STAGE_LABELS.values())},
                labels={"etapa": "Etapa", "opportunities": "Oportunidades"},
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

with opportunity_tab:
    st.subheader("Registrar una nueva oportunidad")
    st.caption("Los ejecutivos y países creados en el panel lateral aparecerán aquí.")
    with st.form("new_opportunity_form", clear_on_submit=True):
        row1 = st.columns(3)
        opportunity_id = row1[0].text_input("ID de oportunidad", placeholder="Ej. OPP-CLIENTE-001")
        sales_rep = row1[1].selectbox("Ejecutivo", st.session_state.executives)
        country = row1[2].selectbox("País", st.session_state.countries)

        row2 = st.columns(3)
        amount = row2[0].number_input("Monto estimado (USD)", min_value=0.0, step=1000.0)
        stage = row2[1].selectbox(
            "Etapa", STAGES, format_func=lambda value: STAGE_LABELS[value]
        )
        industry = row2[2].selectbox("Industria", INDUSTRIES)

        row3 = st.columns(3)
        created_date = row3[0].date_input("Fecha de creación")
        expected_close_date = row3[1].date_input("Fecha esperada de cierre")
        last_activity_date = row3[2].date_input("Última actividad")

        row4 = st.columns(2)
        lead_source = row4[0].selectbox("Origen", LEAD_SOURCES)
        loss_reason = row4[1].selectbox(
            "Motivo de pérdida",
            [""] + LOSS_REASONS,
            disabled=stage != "Closed Lost",
        )
        submitted = st.form_submit_button("Guardar oportunidad", use_container_width=True)

    if submitted:
        clean_id = opportunity_id.strip()
        if not clean_id:
            st.error("El ID de oportunidad es obligatorio.")
        elif clean_id in df["opportunity_id"].astype(str).values:
            st.error("Ese ID de oportunidad ya existe.")
        elif expected_close_date < created_date:
            st.error("La fecha esperada de cierre no puede ser anterior a la creación.")
        elif stage == "Closed Lost" and not loss_reason:
            st.error("Selecciona un motivo para la oportunidad perdida.")
        else:
            raw_df = df[INPUT_COLUMNS].copy()
            close_date = last_activity_date if stage in ["Closed Won", "Closed Lost"] else None
            new_row = {
                "opportunity_id": clean_id,
                "created_date": created_date,
                "expected_close_date": expected_close_date,
                "close_date": close_date,
                "stage": stage,
                "amount_usd": amount,
                "sales_rep": sales_rep,
                "industry": industry,
                "country": country,
                "lead_source": lead_source,
                "last_activity_date": last_activity_date,
                "loss_reason": loss_reason or None,
            }
            st.session_state.crm_df = enrich_dataframe(
                pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True)
            )
            st.success(f"Oportunidad {clean_id} guardada. Ya aparece en el dashboard.")

with data_tab:
    st.subheader("Base de oportunidades")
    export_df = df[INPUT_COLUMNS].copy()
    st.dataframe(export_df, use_container_width=True, hide_index=True)
    csv_bytes = export_df.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8")
    st.download_button(
        "Descargar CSV actualizado",
        data=csv_bytes,
        file_name="oportunidades_actualizadas.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.info(
        "Los cambios se mantienen durante esta sesión. Descarga el CSV para conservarlos y volver a cargarlo después."
    )
