import unittest

from tools.mutation_impact import assess, inspect_matrix


class MutationImpactTests(unittest.TestCase):
    def test_missing_clock_requires_well_formed_clock_properties_section(self):
        row = {
            "scenario": "M01_missing_clock",
            "clock_period_ns": None,
            "clock_properties_section_present": True,
            "clock_properties_section_valid": True,
        }
        self.assertEqual(assess(row)["status"], "matched")

    def test_missing_clock_unparseable_section_is_not_matched(self):
        row = {
            "scenario": "M01_missing_clock",
            "clock_period_ns": None,
            "clock_properties_section_present": True,
            "clock_properties_section_valid": False,
        }
        self.assertEqual(assess(row)["status"], "mismatched")

    def test_missing_input_delay_is_matched(self):
        self.assertEqual(
            assess({"scenario": "M02_missing_input_delay", "missing_input_delay_ports": 32})["status"],
            "matched",
        )

    def test_false_path_is_matched_when_register_paths_disappear(self):
        self.assertEqual(
            assess({"scenario": "M04_unjustified_false_path", "register_to_register_path_found": False})["status"],
            "matched",
        )

    def test_missing_hold_uncertainty_matches_expected_delta(self):
        baseline = {"worst_hold_slack_ns": -0.002}
        mutant = {"scenario": "M06_missing_hold_uncertainty", "worst_hold_slack_ns": 0.048}
        self.assertEqual(assess(mutant, baseline)["status"], "matched")

    def test_missing_hold_uncertainty_rejects_wrong_delta(self):
        baseline = {"worst_hold_slack_ns": -0.002}
        mutant = {"scenario": "M06_missing_hold_uncertainty", "worst_hold_slack_ns": 0.040}
        self.assertEqual(assess(mutant, baseline)["status"], "mismatched")

    def test_missing_hold_uncertainty_without_baseline_is_inconclusive(self):
        self.assertEqual(
            assess({"scenario": "M06_missing_hold_uncertainty", "worst_hold_slack_ns": 0.01})["status"],
            "inconclusive",
        )

    def test_missing_expected_signal_is_mismatch(self):
        self.assertEqual(
            assess({"scenario": "M03_missing_output_delay", "missing_output_delay_ports": 0})["status"],
            "mismatched",
        )

    def test_golden_as_mutant_is_mismatched_for_every_rule(self):
        baseline = {
            "top": "gcd_binary_combined",
            "scenario": "gcd_baseline",
            "clock_period_ns": 10.0,
            "worst_hold_slack_ns": -0.002,
        }
        rows = [
            {"scenario": "M01_missing_clock", "clock_period_ns": 10.0,
             "clock_properties_section_present": True, "clock_properties_section_valid": True},
            {"scenario": "M02_missing_input_delay", "missing_input_delay_ports": 0},
            {"scenario": "M03_missing_output_delay", "missing_output_delay_ports": 0},
            {"scenario": "M04_unjustified_false_path", "register_to_register_path_found": True},
            {"scenario": "M05_near_match_wrong_port", "missing_input_delay_ports": 0},
            {"scenario": "M06_missing_hold_uncertainty", "worst_hold_slack_ns": -0.002},
            {"scenario": "M07_nonpositive_clock_period", "clock_period_ns": 10.0},
        ]
        matrix = {"records": [baseline] + [{"top": "gcd_binary_combined", **row} for row in rows]}
        result = inspect_matrix(matrix)
        self.assertEqual(result["counts"]["mismatched"], 7)
        self.assertEqual(result["counts"]["matched"], 0)

    def test_summary_keeps_inconclusive_separate(self):
        result = inspect_matrix({"records": [
            {"top": "combined", "scenario": "gcd_baseline", "worst_hold_slack_ns": 0.0},
            {"top": "combined", "scenario": "M02_missing_input_delay", "missing_input_delay_ports": 1},
            {"top": "combined", "scenario": "M06_missing_hold_uncertainty"},
        ]})
        self.assertEqual(result["counts"]["matched"], 1)
        self.assertEqual(result["counts"]["inconclusive"], 1)
        self.assertNotIn("accuracy", result)


if __name__ == "__main__":
    unittest.main()
