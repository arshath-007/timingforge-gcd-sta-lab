import unittest

from tools.quality_checks import inspect_golden_row, inspect_matrix


class QualityCheckTests(unittest.TestCase):
    def baseline(self, **overrides):
        row = {
            "top": "gcd_binary_combined",
            "scenario": "gcd_baseline",
            "yosys_cell_area": 100.0,
            "all_path_min_period_ns": 2.5,
            "all_path_fmax_mhz": 400.0,
            "worst_setup_slack_ns": 1.0,
            "worst_hold_slack_ns": 0.1,
            "unconstrained_endpoints_reported": 0,
            "missing_input_delay_ports": 0,
            "missing_output_delay_ports": 0,
            "register_to_register_path_found": True,
            "register_to_register_min_period_ns": 1.0,
            "register_to_register_rising_paths_reported": 12,
            "register_to_register_rising_path_inventory_complete": True,
        }
        row.update(overrides)
        return row

    def test_clean_golden_row_passes(self):
        self.assertEqual(inspect_golden_row(self.baseline()), [])

    def test_negative_hold_and_unconstrained_endpoints_are_flagged(self):
        findings = inspect_golden_row(self.baseline(
            worst_hold_slack_ns=-0.002,
            unconstrained_endpoints_reported=2,
        ))
        codes = {item["code"] for item in findings}
        self.assertIn("TFQ101", codes)
        self.assertIn("TFQ104", codes)

    def test_missing_metrics_are_errors(self):
        findings = inspect_golden_row(self.baseline(all_path_fmax_mhz=None))
        self.assertIn("TFQ001", {item["code"] for item in findings})

    def test_unavailable_native_period_is_info_not_derived(self):
        findings = inspect_golden_row(self.baseline(register_to_register_min_period_ns=None))
        item = next(x for x in findings if x["code"] == "TFQ107")
        self.assertEqual(item["severity"], "INFO")

    def test_drv_violations_are_reported_as_review_findings(self):
        findings = inspect_golden_row(self.baseline(
            drv_max_slew_supported=True, drv_max_slew_check_count=10, drv_max_slew_violation_count=2,
            drv_max_capacitance_supported=True, drv_max_capacitance_check_count=10, drv_max_capacitance_violation_count=0,
        ))
        item = next(x for x in findings if x["code"] == "TFQ110")
        self.assertEqual(item["severity"], "WARNING")

    def test_no_fanout_checks_is_not_misreported_as_zero_violations(self):
        findings = inspect_golden_row(self.baseline(
            drv_max_fanout_supported=True, drv_max_fanout_check_count=0, drv_max_fanout_violation_count=0,
        ))
        item = next(x for x in findings if x["code"] == "TFQ109")
        self.assertIn("cannot be inferred", item["message"])
    def test_mutation_rows_are_not_judged_as_golden_failures(self):
        matrix = {"records": [
            self.baseline(),
            self.baseline(
                scenario="M04_unjustified_false_path",
                register_to_register_path_found=False,
                unconstrained_endpoints_reported=8,
            ),
        ]}
        result = inspect_matrix(matrix)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["counts"]["WARNING"], 0)


if __name__ == "__main__":
    unittest.main()
