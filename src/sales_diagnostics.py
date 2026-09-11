"""Reusable metrics and validation for a B2B CRM export."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
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
}

OPEN_STAGES = ["Qualification", "Discovery", "Proposal", "Negotiation"]
STAGE_PROBABILITY = {
    "Qualification": 0.10,
    "Discovery": 0.30,
    "Proposal": 0.55,
    "Negotiation": 0.80,
    "Closed Won": 1.00,
    "Closed Lost": 0.00,
}


@dataclass(frozen=True)
class SalesKPIs:
    total_opportunities: int
    open_pipeline_usd: float
    weighted_pipeline_usd: float
    win_rate: float
    average_ticket_usd: float
    average_sales_cycle_days: float
    stalled_opportunities: int


def load_crm_data(path_or_buffer: str | Path) -> pd.DataFrame:
    """Load, validate, and enrich a CRM opportunities dataset."""
    df = pd.read_csv(path_or_buffer)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    df = df.copy()
    date_columns = [
        "created_date",
        "expected_close_date",
        "close_date",
        "last_activity_date",
    ]
    for column in date_columns:
        df[column] = pd.to_datetime(df[column], errors="coerce")

    df["amount_usd"] = pd.to_numeric(df["amount_usd"], errors="coerce")
    if df["opportunity_id"].duplicated().any():
        raise ValueError("opportunity_id must be unique")
    if df["amount_usd"].isna().any() or (df["amount_usd"] < 0).any():
        raise ValueError("amount_usd must contain valid non-negative numbers")
    invalid_stages = set(df["stage"].dropna()).difference(STAGE_PROBABILITY)
    if invalid_stages:
        raise ValueError(f"Unknown stages: {', '.join(sorted(invalid_stages))}")

    snapshot_date = max(
        df["created_date"].max(),
        df["last_activity_date"].max(),
        df["close_date"].max(),
    )
    is_open = df["stage"].isin(OPEN_STAGES)
    df["days_without_activity"] = (snapshot_date - df["last_activity_date"]).dt.days
    df["is_stalled"] = is_open & (df["days_without_activity"] > 30)
    df["stage_probability"] = df["stage"].map(STAGE_PROBABILITY)
    df["weighted_amount_usd"] = df["amount_usd"] * df["stage_probability"]
    df["sales_cycle_days"] = (df["close_date"] - df["created_date"]).dt.days
    return df


def calculate_kpis(df: pd.DataFrame) -> SalesKPIs:
    """Calculate executive KPIs from an enriched dataset."""
    open_mask = df["stage"].isin(OPEN_STAGES)
    won = df[df["stage"] == "Closed Won"]
    closed = df[df["stage"].isin(["Closed Won", "Closed Lost"])]
    return SalesKPIs(
        total_opportunities=int(len(df)),
        open_pipeline_usd=float(df.loc[open_mask, "amount_usd"].sum()),
        weighted_pipeline_usd=float(df.loc[open_mask, "weighted_amount_usd"].sum()),
        win_rate=float(len(won) / len(closed)) if len(closed) else 0.0,
        average_ticket_usd=float(won["amount_usd"].mean()) if len(won) else 0.0,
        average_sales_cycle_days=float(won["sales_cycle_days"].mean()) if len(won) else 0.0,
        stalled_opportunities=int(df["is_stalled"].sum()),
    )


def rep_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Return opportunity, revenue, and conversion metrics by representative."""
    rows = []
    for rep, group in df.groupby("sales_rep"):
        won = group[group["stage"] == "Closed Won"]
        closed = group[group["stage"].isin(["Closed Won", "Closed Lost"])]
        rows.append(
            {
                "sales_rep": rep,
                "opportunities": len(group),
                "won_revenue_usd": won["amount_usd"].sum(),
                "win_rate": len(won) / len(closed) if len(closed) else 0.0,
                "open_pipeline_usd": group.loc[
                    group["stage"].isin(OPEN_STAGES), "amount_usd"
                ].sum(),
            }
        )
    return pd.DataFrame(rows).sort_values("won_revenue_usd", ascending=False)


def build_recommendations(df: pd.DataFrame, kpis: SalesKPIs) -> list[str]:
    """Generate transparent, rule-based commercial recommendations."""
    recommendations: list[str] = []
    open_count = int(df["stage"].isin(OPEN_STAGES).sum())
    stalled_share = kpis.stalled_opportunities / open_count if open_count else 0
    if stalled_share >= 0.20:
        recommendations.append(
            f"Revisar el pipeline: {stalled_share:.0%} de las oportunidades abiertas "
            "lleva más de 30 días sin actividad."
        )
    if kpis.win_rate < 0.25:
        recommendations.append(
            "Fortalecer la calificación inicial y el discovery: la tasa de cierre está por debajo de 25%."
        )
    top_loss = (
        df.loc[df["stage"] == "Closed Lost", "loss_reason"].dropna().value_counts()
    )
    if not top_loss.empty:
        recommendations.append(
            f"Atacar el principal motivo de pérdida, “{top_loss.index[0]}”, con una acción específica de habilitación comercial."
        )
    if kpis.weighted_pipeline_usd < 0.4 * kpis.open_pipeline_usd:
        recommendations.append(
            "Aumentar oportunidades en Proposal y Negotiation: gran parte del pipeline aún tiene baja probabilidad."
        )
    return recommendations or ["Mantener seguimiento semanal y validar las probabilidades por etapa."]
