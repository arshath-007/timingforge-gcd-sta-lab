import unittest
from tools.qor_history import compare_snapshots

def snapshot(source="a", library="lib1", sdc="sdc1", tool="yosys 1.0"):
    return {
        "source_sha": source, "platform": "Nangate45",
        "platform_source_revision": "rev1", "corner": "typical",
        "liberty_sha256": library, "tool_versions": {"yosys": tool},
        "records": [{
            "top": "gcd_binary_combined", "scenario": "gcd_baseline",
            "sdc_sha256": sdc, "cell_area": 100.0,
            "all_path_min_period_ns": 2.5,
            "register_to_register_min_period_ns": None,
            "worst_setup_slack_ns": 7.0, "worst_hold_slack_ns": -0.002,
        }],
    }

class QorHistoryTests(unittest.TestCase):
    def test_compares_snapshots_with_matching_environment_and_sdc(self):
        result = compare_snapshots(snapshot("old"), snapshot("new"))
        self.assertTrue(result["environment_match"])
        self.assertEqual(result["reference_source_sha"], "old")
        self.assertEqual(result["candidate_source_sha"], "new")
        self.assertEqual(result["deltas"][0]["cell_area_delta"], 0.0)
        self.assertTrue(result["within_tolerance"])
        self.assertEqual(result["violations"], [])


    def test_area_regression_outside_tolerance_fails_comparison(self):
        candidate = snapshot("new")
        candidate["records"][0]["cell_area"] = 101.0
        result = compare_snapshots(snapshot("old"), candidate, area_tolerance_percent=0.5)
        self.assertFalse(result["within_tolerance"])
        self.assertEqual(result["violations"][0]["metric"], "cell_area")

    def test_timing_regression_outside_tolerance_fails_comparison(self):
        candidate = snapshot("new")
        candidate["records"][0]["all_path_min_period_ns"] = 2.51
        result = compare_snapshots(snapshot("old"), candidate, timing_tolerance_ns=0.005)
        self.assertFalse(result["within_tolerance"])
        self.assertEqual(result["violations"][0]["metric"], "all_path_min_period_ns")

    def test_metric_availability_change_fails_comparison(self):
        candidate = snapshot("new")
        candidate["records"][0]["register_to_register_min_period_ns"] = 0.8
        result = compare_snapshots(snapshot("old"), candidate)
        self.assertFalse(result["within_tolerance"])
        self.assertEqual(result["violations"][0]["reason"], "metric availability changed")

    def test_rejects_library_mismatch(self):
        with self.assertRaisesRegex(ValueError, "liberty_sha256"):
            compare_snapshots(snapshot(), snapshot(library="different"))

    def test_rejects_tool_version_mismatch(self):
        with self.assertRaisesRegex(ValueError, "tool_versions"):
            compare_snapshots(snapshot(), snapshot(tool="yosys 2.0"))

    def test_rejects_sdc_mismatch(self):
        with self.assertRaisesRegex(ValueError, "SDC hash"):
            compare_snapshots(snapshot(), snapshot(sdc="different"))

    def test_rejects_scenario_set_mismatch(self):
        candidate = snapshot()
        candidate["records"] = []
        with self.assertRaisesRegex(ValueError, "scenario sets"):
            compare_snapshots(snapshot(), candidate)

if __name__ == "__main__":
    unittest.main()
