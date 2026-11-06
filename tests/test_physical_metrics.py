import json
import tempfile
import unittest
from pathlib import Path

from tools.physical_metrics import compare, parse_postroute_log


LOG = """=== POST-ROUTE PARASITIC ANNOTATION ===
Annotated parasitics report: fixture
=== TIMINGFORGE POST-ROUTE SETUP CHECK ===
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
=== POST-ROUTE SETUP CLOCK SKEW ===
Clock skew report
=== POST-ROUTE HOLD CLOCK SKEW ===
Clock skew report
=== POST-ROUTE DRV MAX SLEW ===
PinA 0.1 0.2 -0.1 (VIOLATED)
=== POST-ROUTE DRV MAX CAPACITANCE ===
=== POST-ROUTE DRV MAX FANOUT ===
=== POST-ROUTE PARASITICS LOADED ===
SPEF=final.spef
"""


class PhysicalMetricsTests(unittest.TestCase):
    def test_parser_requires_annotation_and_extracts_both_period_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "postroute.log"
            path.write_text(LOG, encoding="utf-8")
            result = parse_postroute_log(path)
            self.assertEqual(result["postroute_register_to_register_min_period_ns"], 3.7)
            self.assertEqual(result["postroute_all_path_min_period_ns"], 3.5)
            self.assertEqual(result["postroute_worst_setup_slack_ns"], 6.1)
            self.assertEqual(result["postroute_worst_hold_slack_ns"], 0.02)
            self.assertTrue(result["clock_skew_supported"])
            self.assertIn("Annotated parasitics", result["parasitic_annotation_report"])
            self.assertEqual(result["postroute_max_slew_violation_count"], 1)
            self.assertEqual(result["postroute_max_capacitance_violation_count"], 0)
            self.assertEqual(result["postroute_max_fanout_violation_count"], 0)
            self.assertTrue(result["postroute_drv_supported"])

    def test_parser_rejects_missing_annotation_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "postroute.log"
            path.write_text(LOG.replace("Annotated parasitics report: fixture", ""), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "annotation report missing"):
                parse_postroute_log(path)

    def test_compare_marks_cross_flow_deltas_observational_only(self):
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
            self.assertEqual(result["designs"][0]["all_path_min_period_delta_ns_observational_only"], -0.5)
            self.assertFalse(result["netlist_matched"])
            self.assertEqual(result["delta_interpretation"], "observational_only; do not attribute differences to routing parasitics alone")
            self.assertFalse(result["signoff_claim"])


if __name__ == "__main__":
    unittest.main()
