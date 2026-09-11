"""Run the sales diagnostic and export a short executive summary."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

try:
    from src.sales_diagnostics import build_recommendations, calculate_kpis, load_crm_data
except ModuleNotFoundError:
    from sales_diagnostics import build_recommendations, calculate_kpis, load_crm_data


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "crm_opportunities.csv"
OUTPUT_DIR = ROOT / "outputs"


def main() -> None:
    df = load_crm_data(DATA_PATH)
    kpis = calculate_kpis(df)
    recommendations = build_recommendations(df, kpis)
    OUTPUT_DIR.mkdir(exist_ok=True)

    (OUTPUT_DIR / "kpis.json").write_text(
        json.dumps(asdict(kpis), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    summary = [
        "# Resumen ejecutivo",
        "",
        f"- Oportunidades analizadas: **{kpis.total_opportunities:,}**",
        f"- Pipeline abierto: **USD {kpis.open_pipeline_usd:,.0f}**",
        f"- Pipeline ponderado: **USD {kpis.weighted_pipeline_usd:,.0f}**",
        f"- Tasa de cierre: **{kpis.win_rate:.1%}**",
        f"- Ticket promedio ganado: **USD {kpis.average_ticket_usd:,.0f}**",
        f"- Ciclo comercial promedio: **{kpis.average_sales_cycle_days:.0f} días**",
        f"- Oportunidades estancadas: **{kpis.stalled_opportunities}**",
        "",
        "## Recomendaciones",
        "",
        *[f"- {item}" for item in recommendations],
    ]
    (OUTPUT_DIR / "executive_summary.md").write_text("\n".join(summary), encoding="utf-8")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
