import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.sales_diagnostics import calculate_kpis, load_crm_data


class SalesDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_metrics_for_closed_opportunities(self):
        data = pd.DataFrame(
            {
                "opportunity_id": ["A", "B", "C"],
                "created_date": ["2026-01-01"] * 3,
                "expected_close_date": ["2026-03-01"] * 3,
                "close_date": ["2026-02-01", "2026-02-15", None],
                "stage": ["Closed Won", "Closed Lost", "Proposal"],
                "amount_usd": [1000, 2000, 4000],
                "sales_rep": ["Ana"] * 3,
                "industry": ["Tech"] * 3,
                "country": ["México"] * 3,
                "lead_source": ["Outbound"] * 3,
                "last_activity_date": ["2026-02-01", "2026-02-15", "2026-01-05"],
                "loss_reason": [None, "Precio", None],
            }
        )
        path = Path(self.temp_dir.name) / "crm.csv"
        data.to_csv(path, index=False)
        kpis = calculate_kpis(load_crm_data(path))

        self.assertEqual(kpis.total_opportunities, 3)
        self.assertEqual(kpis.open_pipeline_usd, 4000)
        self.assertEqual(kpis.weighted_pipeline_usd, 2200)
        self.assertEqual(kpis.win_rate, 0.5)
        self.assertEqual(kpis.average_ticket_usd, 1000)
        self.assertEqual(kpis.stalled_opportunities, 1)

    def test_rejects_duplicate_ids(self):
        data = pd.DataFrame(
            {
                "opportunity_id": ["A", "A"],
                "created_date": ["2026-01-01"] * 2,
                "expected_close_date": ["2026-03-01"] * 2,
                "close_date": [None] * 2,
                "stage": ["Discovery"] * 2,
                "amount_usd": [1000, 2000],
                "sales_rep": ["Ana"] * 2,
                "industry": ["Tech"] * 2,
                "country": ["México"] * 2,
                "lead_source": ["Outbound"] * 2,
                "last_activity_date": ["2026-01-15"] * 2,
                "loss_reason": [None] * 2,
            }
        )
        path = Path(self.temp_dir.name) / "duplicates.csv"
        data.to_csv(path, index=False)
        with self.assertRaisesRegex(ValueError, "unique"):
            load_crm_data(path)


if __name__ == "__main__":
    unittest.main()
