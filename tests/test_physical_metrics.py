import json
import tempfile
import unittest
from pathlib import Path

from tools.physical_metrics import compare, parse_postroute_log


LOG = """=== POST-ROUTE PARASITICS LOADED ===
SPEF=final.spef
=== POST-ROUTE ALL-PATH CLOCK PERIOD ===
core_clk period_min = 3.500 fmax = 285.714
=== POST-ROUTE SETUP CLOCK SKEW ===
Clock skew report
=== POST-ROUTE HOLD CLOCK SKEW ===
Clock skew report
=== POST-ROUTE REGISTER-TO-REGISTER CLOCK PERIOD ===
core_clk period_min = 3.700 fmax = 270.270
=== POST-ROUTE ALL-PATH CLOCK PERIOD ===
core_clk period_min = 3.500 fmax = 285.714
=== POST-ROUTE SETUP SUMMARY ===
worst slack max 6.100
wns max 0.000
tns max 0.000
=== POST-ROUTE HOLD SUMMARY ===
worst slack min 0.020
wns min 0.000
tns min 0.000
=== POST-ROUTE SETUP PATHS ===
"""


class PhysicalMetricsTests(unittest.TestCase):
    def test_parse_postroute_log_requires_spef_and_timing_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "postroute.log"
            path.write_text(LOG, encoding="utf-8")
            result = parse_postroute_log(path)
            self.assertEqual(result["postroute_all_path_min_period_ns"], 3.5)
            self.assertEqual(result["postroute_worst_setup_slack_ns"], 6.1)
            self.assertEqual(result["postroute_worst_hold_slack_ns"], 0.02)
            self.assertTrue(result["clock_skew_supported"])

    def test_compare_requires_both_golden_rows_and_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            physical = root / "build" / "physical"
            for top in ("gcd_binary_combined", "gcd_binary_split"):
                (physical / top).mkdir(parents=True)
                (physical / top / "postroute_sta.log").write_text(LOG, encoding="utf-8")
            (root / "constraints").mkdir()
            (root / "constraints" / "gcd_baseline.sdc").write_text("create_clock", encoding="utf-8")
            matrix_path = root / "build" / "reports" / "sta_matrix_summary.json"
            matrix_path.parent.mkdir(parents=True)
            matrix = {
                "platform": "Nangate45 typical Liberty",
                "records": [
                    {"top": top, "scenario": "gcd_baseline",
                     "all_path_min_period_ns": 4.0,
                     "worst_setup_slack_ns": 7.0,
                     "worst_hold_slack_ns": -0.01}
                    for top in ("gcd_binary_combined", "gcd_binary_split")
                ],
            }
            matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
            result = compare(matrix_path, physical)
            self.assertEqual(len(result["designs"]), 2)
            self.assertEqual(result["designs"][0]["all_path_min_period_delta_ns"], -0.5)
            self.assertEqual(result["designs"][0]["setup_slack_delta_ns"], -0.9)
            self.assertFalse(result["signoff_claim"])


if __name__ == "__main__":
    unittest.main()
