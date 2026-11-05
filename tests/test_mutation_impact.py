import unittest
from tools.mutation_impact import assess, inspect_matrix

class MutationImpactTests(unittest.TestCase):
    def test_missing_input_delay_is_matched(self):
        self.assertEqual(assess({"scenario": "M02_missing_input_delay", "missing_input_delay_ports": 32})["status"], "matched")
    def test_false_path_is_matched_when_register_paths_disappear(self):
        self.assertEqual(assess({"scenario": "M04_unjustified_false_path", "register_to_register_path_found": False})["status"], "matched")
    def test_missing_hold_uncertainty_is_inconclusive_without_direct_metric(self):
        self.assertEqual(assess({"scenario": "M06_missing_hold_uncertainty", "worst_hold_slack_ns": 0.01})["status"], "inconclusive")
    def test_missing_expected_signal_is_mismatch(self):
        self.assertEqual(assess({"scenario": "M03_missing_output_delay", "missing_output_delay_ports": 0})["status"], "mismatched")
    def test_summary_keeps_inconclusive_separate(self):
        result = inspect_matrix({"records": [
            {"scenario": "M02_missing_input_delay", "missing_input_delay_ports": 1},
            {"scenario": "M06_missing_hold_uncertainty"},
        ]})
        self.assertEqual(result["counts"]["matched"], 1)
        self.assertEqual(result["counts"]["inconclusive"], 1)
        self.assertNotIn("accuracy", result)

if __name__ == "__main__":
    unittest.main()
