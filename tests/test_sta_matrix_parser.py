import tempfile
import unittest
from pathlib import Path

from tools.parse_sta_matrix import parse_log, summarise

SAMPLE = """=== SETUP / MAX PATH DETAILS ===
Startpoint: u_reg/Q
Endpoint: v_reg/D
=== HOLD / MIN PATH DETAILS ===
Startpoint: u_reg/Q
Endpoint: v_reg/D
=== UNCONSTRAINED PATH DETAILS ===
Startpoint: in_port
Endpoint: output_port
wns max -0.025
tns max -0.125
wns min 0.010
tns min 0.000
"""


class StaMatrixParserTests(unittest.TestCase):
    def test_parses_architecture_metrics_and_unconstrained_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sta_gcd_binary_combined_gcd_baseline.log"
            path.write_text(SAMPLE, encoding="utf-8")
            row = parse_log(path)
            self.assertEqual(row["top"], "gcd_binary_combined")
            self.assertEqual(row["scenario"], "gcd_baseline")
            self.assertEqual(row["setup_wns"], -0.025)
            self.assertEqual(row["setup_tns"], -0.125)
            self.assertEqual(row["hold_wns"], 0.010)
            self.assertEqual(row["unconstrained_path_count_reported"], 1)
            self.assertEqual(row["worst_setup_startpoint"], "u_reg/Q")
            self.assertEqual(row["worst_setup_endpoint"], "v_reg/D")

    def test_writes_delta_against_golden_for_same_architecture(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "sta_gcd_binary_combined_gcd_baseline.log").write_text(SAMPLE, encoding="utf-8")
            mutated = SAMPLE.replace("wns max -0.025", "wns max -0.100")
            (directory / "sta_gcd_binary_combined_M04_unjustified_false_path.log").write_text(mutated, encoding="utf-8")
            result = summarise(directory)
            self.assertEqual(result["logs_found"], 2)
            target = next(x for x in result["records"] if x["scenario"] == "M04_unjustified_false_path")
            self.assertEqual(target["setup_wns_delta_vs_golden"], -0.075)
            self.assertTrue((directory / "sta_matrix_summary.md").is_file())
            self.assertTrue((directory / "sta_matrix_summary.json").is_file())


if __name__ == "__main__":
    unittest.main()
