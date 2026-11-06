import tempfile
import unittest
from pathlib import Path

from tools.parse_sta_matrix import parse_log, summarise

SAMPLE = """=== REGISTER-TO-REGISTER CLOCK PERIOD / FREQUENCY ===
core_clk period_min = 2.250 fmax = 444.44
=== ALL-PATH CLOCK PERIOD / FREQUENCY (INCLUDING PORT PATHS) ===
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
Warning: There are 2 input ports missing set_input_delay.
Warning: There are 1 output ports missing set_output_delay.
"""


class StaMatrixParserTests(unittest.TestCase):
    def test_parses_supported_drv_violation_counts(self):
        from tools.parse_sta_matrix import parse_drv_check
        report = """=== DRV MAX SLEW ===
Pin pin_a ^
Slack -0.020 (VIOLATED)
=== DRV MAX CAPACITANCE ===
"""
        slew = parse_drv_check(report, "=== DRV MAX SLEW ===", "=== DRV MAX CAPACITANCE ===")
        self.assertTrue(slew["supported"])
        self.assertEqual(slew["violation_count"], 1)
        cap = parse_drv_check(report, "=== DRV MAX CAPACITANCE ===", "=== DRV MAX FANOUT ===")
        self.assertTrue(cap["supported"])
        self.assertEqual(cap["violation_count"], 0)

    def test_keeps_unsupported_drv_report_as_null(self):
        from tools.parse_sta_matrix import parse_drv_check
        report = """=== DRV MAX FANOUT ===
TIMINGFORGE_DRV_UNSUPPORTED: max_fanout: command unavailable
=== UNCONSTRAINED PATH DETAILS ===
"""
        result = parse_drv_check(report, "=== DRV MAX FANOUT ===", "=== UNCONSTRAINED PATH DETAILS ===")
        self.assertFalse(result["supported"])
        self.assertIsNone(result["violation_count"])


    def test_records_check_setup_warnings(self):
        sample = SAMPLE.replace(
            "=== REGISTER-TO-REGISTER CLOCK PERIOD / FREQUENCY ===",
            "=== TIMINGFORGE SETUP CHECK ===\nWarning: There are 1 unconstrained endpoints.\n"
            "=== REGISTER-TO-REGISTER CLOCK PERIOD / FREQUENCY ===",
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sta_gcd_binary_combined_gcd_baseline.log"
            path.write_text(sample, encoding="utf-8")
            row = parse_log(path)
            self.assertEqual(row["setup_check_warning_count"], 1)
            self.assertIn("unconstrained endpoints", row["setup_check_warnings"][0])

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
            self.assertEqual(row["register_to_register_min_period_ns"], 2.250)
            self.assertEqual(row["register_to_register_fmax_mhz"], 444.44)
            self.assertEqual(row["all_path_min_period_ns"], 2.500)
            self.assertEqual(row["all_path_fmax_mhz"], 400.00)
            self.assertEqual(row["unconstrained_endpoints_reported"], 3)
            self.assertEqual(row["missing_input_delay_ports"], 2)
            self.assertEqual(row["missing_output_delay_ports"], 1)
            self.assertTrue(row["register_to_register_path_found"])
            self.assertEqual(row["register_to_register_startpoint"], "input_reg/Q")

    def test_classifies_critical_path_types_from_gcd_interface_names(self):
        from tools.parse_sta_matrix import classify_critical_path
        self.assertEqual(classify_critical_path("a_in[3]", "state_reg/D"), "input_to_register")
        self.assertEqual(classify_critical_path("state_reg/Q", "result_reg/D"), "register_to_register")
        self.assertEqual(classify_critical_path("result_reg/Q", "gcd_out[0]"), "register_to_output")
        self.assertEqual(classify_critical_path("a_in[0]", "gcd_out[0]"), "input_to_output")
        self.assertEqual(classify_critical_path("a_in[0] (input port clocked by core_clk)", "_2247_ (rising edge-triggered flip-flop clocked by core_clk)"), "input_to_register")
        self.assertEqual(classify_critical_path("_2247_ (rising edge-triggered flip-flop clocked by core_clk)", "gcd_out[0] (output port)"), "register_to_output")
        self.assertEqual(classify_critical_path("unknown_start", "unknown_end"), "unknown")

    def test_derives_single_cycle_period_from_explicit_rising_edge_paths(self):
        derived_sample = SAMPLE.replace(
            "=== HOLD / MIN PATH DETAILS ===",
            """=== RISING-EDGE REGISTER-TO-REGISTER SETUP PATHS ===
Startpoint: launch_reg/Q
Endpoint: capture_reg/D
8.414 slack (MET)
Startpoint: launch_reg2/Q
Endpoint: capture_reg2/D
8.700 slack (MET)
=== CLOCK PROPERTIES ===
Clock                   Period          Waveform
core_clk                 10.00        0.00      5.00
=== HOLD / MIN PATH DETAILS ===""",
        ).replace("core_clk period_min = 2.250 fmax = 444.44", "core_clk period_min = 0.00 fmax = inf")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sta_gcd_binary_combined_gcd_baseline.log"
            path.write_text(derived_sample, encoding="utf-8")
            row = parse_log(path)
            self.assertIsNone(row["register_to_register_min_period_ns"])
            self.assertEqual(row["register_to_register_rising_paths_reported"], 2)
            self.assertEqual(row["register_to_register_rising_worst_slack_ns"], 8.414)
            self.assertEqual(row["register_to_register_rising_path_inventory_complete"], True)
            self.assertEqual(row["register_to_register_rising_best_slack_ns"], 8.700)
            self.assertNotIn("register_to_register_derived_fmax_mhz", row)

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



    def test_m01_clock_properties_section_is_valid_when_empty(self):
        sample = SAMPLE.replace(
            "=== HOLD / MIN PATH DETAILS ===",
            "=== CLOCK PROPERTIES ===\nClock                   Period          Waveform\n----------------------------------------------------\n=== HOLD / MIN PATH DETAILS ===",
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sta_gcd_binary_combined_M01_missing_clock.log"
            path.write_text(sample, encoding="utf-8")
            row = parse_log(path)
            self.assertIsNone(row["clock_period_ns"])
            self.assertTrue(row["clock_properties_section_present"])
            self.assertTrue(row["clock_properties_section_valid"])

    def test_m01_malformed_clock_properties_section_is_invalid(self):
        sample = SAMPLE.replace(
            "=== HOLD / MIN PATH DETAILS ===",
            "=== CLOCK PROPERTIES ===\nthis is not a clock report\n=== HOLD / MIN PATH DETAILS ===",
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sta_gcd_binary_combined_M01_missing_clock.log"
            path.write_text(sample, encoding="utf-8")
            row = parse_log(path)
            self.assertIsNone(row["clock_period_ns"])
            self.assertTrue(row["clock_properties_section_present"])
            self.assertFalse(row["clock_properties_section_valid"])

    def test_mutant_path_inventory_uses_100_path_cap(self):
        paths = "\n".join("0.100 slack (MET)" for _ in range(100))
        sample = SAMPLE.replace(
            "=== HOLD / MIN PATH DETAILS ===",
            "=== RISING-EDGE REGISTER-TO-REGISTER SETUP PATHS ===\n" + paths + "\n=== HOLD / MIN PATH DETAILS ===",
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sta_gcd_binary_combined_M04_unjustified_false_path.log"
            path.write_text(sample, encoding="utf-8")
            row = parse_log(path)
            self.assertEqual(row["register_to_register_rising_paths_reported"], 100)
            self.assertEqual(row["register_to_register_rising_path_limit"], 100)
            self.assertFalse(row["register_to_register_rising_path_inventory_complete"])

    def test_no_register_path_clock_period_is_not_infinite_fmax(self):
        no_path = SAMPLE.replace("core_clk period_min = 2.250 fmax = 444.44", "core_clk period_min = 0.00 fmax = inf")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sta_gcd_binary_combined_gcd_baseline.log"
            path.write_text(no_path, encoding="utf-8")
            row = parse_log(path)
            self.assertIsNone(row["register_to_register_min_period_ns"])
            self.assertIsNone(row["register_to_register_fmax_mhz"])


if __name__ == "__main__":
    unittest.main()
