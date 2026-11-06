import json
import tempfile
import unittest
from pathlib import Path

from tools.physical_experiments import _mean_range, collect


POSTROUTE_LOG = """=== POST-ROUTE PARASITIC ANNOTATION ===
Found 0 unannotated drivers.
Found 0 partially unannotated drivers.
=== TIMINGFORGE POST-ROUTE SETUP CHECK ===
=== POST-ROUTE CLOCK PROPERTIES ===
Clock Period Waveform
--------------------------------
core_clk 10.000 0.000 5.000
=== POST-ROUTE SETUP CLOCK SKEW ===
Clock skew report
=== POST-ROUTE HOLD CLOCK SKEW ===
Clock skew report
=== POST-ROUTE REGISTER-TO-REGISTER CLOCK PERIOD ===
core_clk period_min = 1.000 fmax = 1000.000
=== POST-ROUTE ALL-PATH CLOCK PERIOD ===
core_clk period_min = 2.000 fmax = 500.000
=== POST-ROUTE SETUP SUMMARY ===
worst slack max 0.100
wns max 0.000
tns max 0.000
=== POST-ROUTE SETUP PATHS ===
=== POST-ROUTE HOLD SUMMARY ===
worst slack min 0.010
wns min 0.000
tns min 0.000
=== POST-ROUTE HOLD PATHS ===
=== POST-ROUTE DRV MAX SLEW ===
=== POST-ROUTE DRV MAX CAPACITANCE ===
=== POST-ROUTE DRV MAX FANOUT ===
=== POST-ROUTE PARASITICS LOADED ===
SPEF=final.spef
"""


class PhysicalExperimentsTests(unittest.TestCase):
    def test_mean_range_summarises_variation(self):
        result = _mean_range([1.0, 2.0, 3.0])
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["mean"], 2.0)
        self.assertEqual(result["range"], 2.0)

    def test_collect_parses_run_and_reports_timing_closure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "variance" / "v1" / "gcd_binary_combined"
            results = run / "results" / "nangate45" / "gcd_binary_combined" / "base"
            logs = run / "logs" / "nangate45" / "gcd_binary_combined" / "base"
            results.mkdir(parents=True)
            logs.mkdir(parents=True)
            (results / "6_final.v").write_text("module top; endmodule\n", encoding="utf-8")
            (logs / "6_report.json").write_text(json.dumps({
                "finish__design__instance__count__stdcell": 100,
                "finish__design__instance__area__stdcell": 200.0,
                "finish__design__instance__count__class:clock_buffer": 2,
                "finish__design__instance__count__class:timing_repair_buffer": 3,
                "finish__design__instance__count__class:inverter": 4,
            }), encoding="utf-8")
            (run / "postroute_sta.log").write_text(POSTROUTE_LOG, encoding="utf-8")
            (run / "metadata.json").write_text(json.dumps({
                "experiment": "variance", "variant": "v1", "top": "gcd_binary_combined",
                "core_utilization": 35, "place_density": 0.6,
                "gpl_random_seed": 1, "grt_seed": 1,
                "clock_period_ns": None, "flow_status": "success",
            }), encoding="utf-8")
            result = collect(root)
            self.assertEqual(result["run_count"], 1)
            self.assertEqual(result["parsed_run_count"], 1)
            self.assertTrue(result["runs"][0]["timing_closure_pass"])
            self.assertEqual(result["runs"][0]["clock_buffer_count"], 2)
            self.assertEqual(result["runs"][0]["postroute_register_to_register_min_period_ns"], 1.0)


if __name__ == "__main__":
    unittest.main()
