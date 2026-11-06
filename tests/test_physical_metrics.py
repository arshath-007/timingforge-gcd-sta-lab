import json
import tempfile
import unittest
from pathlib import Path

from tools.physical_metrics import compare, parse_postroute_log, parse_presynth_log


LOG = """=== POST-ROUTE PARASITIC ANNOTATION ===
Found 0 unannotated drivers.
Found 0 partially unannotated drivers.
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

PRESYNTH_LOG = """=== ORFS POST-SYNTHESIS REGISTER-TO-REGISTER CLOCK PERIOD ===
core_clk period_min = 3.900 fmax = 256.410
=== ORFS POST-SYNTHESIS ALL-PATH CLOCK PERIOD ===
core_clk period_min = 4.100 fmax = 243.902
=== ORFS POST-SYNTHESIS SETUP SUMMARY ===
worst slack max 5.900
wns max 0.000
tns max 0.000
=== ORFS POST-SYNTHESIS HOLD SUMMARY ===
worst slack min 0.010
wns min 0.000
tns min 0.000
"""


def write_stage_metrics(log_dir: Path):
    log_dir.mkdir(parents=True, exist_ok=True)
    stages = {
        "1_synth.json": "synth",
        "3_3_place_gp.json": "globalplace",
        "4_1_cts.json": "cts",
        "5_1_grt.json": "globalroute",
        "6_report.json": "finish",
    }
    for filename, prefix in stages.items():
        data = {
            f"{prefix}__design__instance__count__stdcell": 100,
            f"{prefix}__design__instance__area__stdcell": 200.0,
            f"{prefix}__design__instance__count": 100,
            f"{prefix}__design__instance__area": 200.0,
        }
        (log_dir / filename).write_text(json.dumps(data), encoding="utf-8")


class PhysicalMetricsTests(unittest.TestCase):
    def test_parser_requires_annotation_and_extracts_both_period_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "postroute.log"
            path.write_text(LOG, encoding="utf-8")
            results = path.parent / "results" / "nangate45" / path.parent.name / "base"
            results.mkdir(parents=True)
            (results / "6_final.v").write_text("module top; endmodule\n", encoding="utf-8")
            result = parse_postroute_log(path)
            self.assertEqual(result["postroute_register_to_register_min_period_ns"], 3.7)
            self.assertEqual(result["postroute_all_path_min_period_ns"], 3.5)
            self.assertEqual(result["postroute_worst_setup_slack_ns"], 6.1)
            self.assertEqual(result["postroute_worst_hold_slack_ns"], 0.02)
            self.assertTrue(result["clock_skew_supported"])
            self.assertIn("Found 0 unannotated drivers.", result["parasitic_annotation_report"])
            self.assertEqual(result["postroute_max_slew_violation_count"], 1)
            self.assertEqual(result["postroute_max_capacitance_violation_count"], 0)
            self.assertEqual(result["postroute_max_fanout_violation_count"], 0)
            self.assertTrue(result["postroute_drv_supported"])

    def test_parser_rejects_nonzero_unannotated_driver_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "postroute.log"
            path.write_text(LOG.replace("Found 0 unannotated drivers.", "Found 1 unannotated drivers."), encoding="utf-8")
            results = path.parent / "results" / "nangate45" / path.parent.name / "base"
            results.mkdir(parents=True)
            (results / "6_final.v").write_text("module top; endmodule\\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "lists 0 unannotated drivers but summary says 1"):
                parse_postroute_log(path)

    def test_parser_rejects_missing_annotation_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "postroute.log"
            path.write_text(LOG.replace("Found 0 unannotated drivers.\n", "").replace("Found 0 partially unannotated drivers.\n", ""), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "native parasitic annotation report missing"):
                parse_postroute_log(path)

    def test_parser_extracts_orfs_post_synthesis_timing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "presynth_sta.log"
            path.write_text(PRESYNTH_LOG, encoding="utf-8")
            result = parse_presynth_log(path)
            self.assertEqual(result["register_to_register_min_period_ns"], 3.9)
            self.assertEqual(result["all_path_min_period_ns"], 4.1)
            self.assertEqual(result["worst_setup_slack_ns"], 5.9)
            self.assertEqual(result["worst_hold_slack_ns"], 0.01)

    def test_compare_marks_cross_flow_deltas_observational_only_and_includes_orfs_stages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            physical = root / "build" / "physical"
            for top in ("gcd_binary_combined", "gcd_binary_split"):
                work = physical / top
                work.mkdir(parents=True)
                (work / "postroute_sta.log").write_text(LOG, encoding="utf-8")
                (work / "presynth_sta.log").write_text(PRESYNTH_LOG, encoding="utf-8")
                results = work / "results" / "nangate45" / top / "base"
                results.mkdir(parents=True)
                (results / "6_final.v").write_text("module top; endmodule\n", encoding="utf-8")
                write_stage_metrics(work / "logs" / "nangate45" / top / "base")
                (root / "build" / f"yosys_{top}.log").write_text(
                    f"=== {top} ===\n  50 100.0 cells\nChip area for module '{top}': 100.0\n",
                    encoding="utf-8",
                )
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
            result = compare(matrix_path, physical, root)
            self.assertEqual(len(result["designs"]), 2)
            self.assertEqual(result["designs"][0]["all_path_min_period_delta_ns_observational_only"], -0.5)
            self.assertFalse(result["netlist_matched"])
            self.assertEqual(result["delta_interpretation"], "observational_only; do not attribute differences to routing parasitics alone")
            self.assertFalse(result["signoff_claim"])
            combined = result["designs"][0]
            self.assertEqual(combined["prelayout_synthesis"]["standard_cell_instance_count"], 50)
            self.assertEqual(combined["orfs_synthesis"]["standard_cell_instance_count"], 100)
            self.assertEqual(combined["orfs_stage_metrics"]["clock_tree_synthesis"]["standard_cell_area"], 200.0)
            self.assertEqual(combined["orfs_post_synthesis_sta"]["register_to_register_min_period_ns"], 3.9)
            self.assertFalse(combined["orfs_synthesis_to_postroute"]["exact_netlist_match"])


if __name__ == "__main__":
    unittest.main()
