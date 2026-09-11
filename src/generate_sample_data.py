"""Generate a reproducible synthetic CRM dataset for portfolio use."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "crm_opportunities.csv"


def generate_sample_data(rows: int = 600, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    snapshot = pd.Timestamp("2026-08-31")
    created = snapshot - pd.to_timedelta(rng.integers(10, 420, rows), unit="D")

    stage = rng.choice(
        ["Qualification", "Discovery", "Proposal", "Negotiation", "Closed Won", "Closed Lost"],
        size=rows,
        p=[0.13, 0.14, 0.12, 0.08, 0.25, 0.28],
    )
    amounts = np.round(rng.lognormal(mean=9.35, sigma=0.72, size=rows), 2)
    duration = rng.integers(25, 180, rows)
    expected_close = created + pd.to_timedelta(duration, unit="D")
    closed_mask = np.isin(stage, ["Closed Won", "Closed Lost"])
    close_date = pd.Series(pd.NaT, index=range(rows), dtype="datetime64[ns]")
    close_date.loc[closed_mask] = (
        pd.Series(created).loc[closed_mask]
        + pd.to_timedelta(rng.integers(20, 150, closed_mask.sum()), unit="D")
    ).clip(upper=snapshot)

    last_activity = []
    for i in range(rows):
        end = close_date.iloc[i] if closed_mask[i] else snapshot
        active_window = max((end - created[i]).days, 1)
        last_activity.append(created[i] + pd.Timedelta(days=int(rng.integers(0, active_window + 1))))

    loss_reasons = np.where(
        stage == "Closed Lost",
        rng.choice(
            ["Precio", "Sin prioridad", "Competencia", "Sin presupuesto", "No decision"],
            size=rows,
            p=[0.29, 0.24, 0.20, 0.17, 0.10],
        ),
        None,
    )

    df = pd.DataFrame(
        {
            "opportunity_id": [f"OPP-{i:04d}" for i in range(1, rows + 1)],
            "created_date": created,
            "expected_close_date": expected_close,
            "close_date": close_date,
            "stage": stage,
            "amount_usd": amounts,
            "sales_rep": rng.choice(["Andrea", "Camilo", "Mariana", "Sofía", "Diego"], rows),
            "industry": rng.choice(
                ["Tecnología", "Servicios", "Retail", "Seguros", "Finanzas", "Logística"], rows
            ),
            "country": rng.choice(
                ["México", "Colombia", "Perú", "Chile"], rows, p=[0.55, 0.20, 0.15, 0.10]
            ),
            "lead_source": rng.choice(
                ["Outbound", "Inbound", "Referido", "Evento", "Partner"], rows
            ),
            "last_activity_date": pd.to_datetime(last_activity),
            "loss_reason": loss_reasons,
        }
    )
    return df.sort_values("created_date").reset_index(drop=True)


if __name__ == "__main__":
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    generate_sample_data().to_csv(OUTPUT_PATH, index=False, date_format="%Y-%m-%d")
    print(f"Created {OUTPUT_PATH}")
