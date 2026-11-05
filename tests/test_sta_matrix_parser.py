import tempfile
import unittest
from pathlib import Path

from tools.parse_sta_matrix import parse_log, summarise

SAMPLE = """=== CLOCK PERIOD / FREQUENCY ===
core_clk period_min = 2.500 fmax = 400.00
=== SETUP SUMMARY ===
worst slack max 0.750
wns max 0.000
tns max 0.000
=== HOLD SUMMARY ===
worst slack min -0.025
wns min -0.025
tns min -0.125
=== SETUP / MAX PATH DETAILS ===
Startpoint: input_reg/Q
Endpoint: data_reg/D
=== REGISTER-TO-REGISTER SETUP PATHS ===
Startpoint: input_reg/Q
Endpoint: data_reg/D
=== HOLD / MIN PATH DETAILS ===
Startpoint: input_reg/Q
Endpoint: data_reg/D
=== UNCONSTRAINED PATH DETAILS ===
Startpoint: in_port
Endpoint: output_port
Warning: There are 3 unconstrained endpoints.
Warning: There are 2 input ports with no input delay.
Warning: There are 1 output ports with no output delay.
"""


class StaMatrixParserTests(unittest.TestCase):
    def test_parses_architecture_metrics_and_path_types(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sta_gcd_binary_combined_gcd_baseline.log"
            path.write_text(SAMPLE, encoding="utf-8")
            row = parse_log(path)
            self.assertEqual(row["top"], "gcd_binary_combined")
            self.assertEqual(row["scenario"], "gcd_baseline")
            self.assertEqual(row["worst_setup_slack_ns"], 0.750)
            self.assertEqual(row["setup_wns_ns"], 0.000)
            self.assertEqual(row["hold_wns_ns"], -0.025)
            self.assertEqual(row["clock_period_min_ns"], 2.500)
            self.assertEqual(row["clock_fmax_mhz"], 400.00)
            self.assertEqual(row["unconstrained_endpoints_reported"], 3)
            self.assertEqual(len(row["missing_input_delay_warnings"]), 1)
            self.assertEqual(len(row["missing_output_delay_warnings"]), 1)
            self.assertTrue(row["register_to_register_path_found"])
            self.assertEqual(row["register_to_register_startpoint"], "input_reg/Q")

    def test_false_path_scenario_can_report_no_register_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sta_gcd_binary_combined_M04_unjustified_false_path.log"
            no_reg_paths = SAMPLE.replace(
                "Startpoint: input_reg/Q\nEndpoint: data_reg/D\n=== HOLD / MIN PATH DETAILS ===",
                "No paths found.\n=== HOLD / MIN PATH DETAILS ===",
            )
            path.write_text(no_reg_paths, encoding="utf-8")
            row = parse_log(path)
            self.assertFalse(row["register_to_register_path_found"])

    def test_writes_delta_against_golden_for_same_architecture(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            baseline = SAMPLE.replace("worst slack max 0.750", "worst slack max 0.750")
            mutated = SAMPLE.replace("worst slack max 0.750", "worst slack max -0.100")
            (directory / "sta_gcd_binary_combined_gcd_baseline.log").write_text(baseline, encoding="utf-8")
            (directory / "sta_gcd_binary_combined_M04_unjustified_false_path.log").write_text(mutated, encoding="utf-8")
            result = summarise(directory)
            self.assertEqual(result["logs_found"], 2)
            target = next(x for x in result["records"] if x["scenario"] == "M04_unjustified_false_path")
            self.assertEqual(target["worst_setup_slack_delta_vs_golden_ns"], -0.850)
            self.assertTrue((directory / "sta_matrix_summary.md").is_file())
            self.assertTrue((directory / "sta_matrix_summary.json").is_file())


if __name__ == "__main__":
    unittest.main()
