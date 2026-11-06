import unittest
from tools.qor_gate import evaluate


def snapshot(area=100.0, period=2.0, setup=1.0, hold=0.1, tool="yosys 1.0"):
    return {
        "source_sha": "baseline",
        "platform": "Nangate45",
        "platform_source_revision": "rev1",
        "corner": "typical",
        "liberty_sha256": "lib",
        "tool_versions": {"yosys": tool},
        "records": [{
            "top": "gcd_binary_combined",
            "scenario": "gcd_baseline",
            "sdc_sha256": "sdc",
            "cell_area": area,
            "all_path_min_period_ns": period,
            "worst_setup_slack_ns": setup,
            "worst_hold_slack_ns": hold,
        }],
    }


POLICY = {
    "limits": {
        "cell_area_growth_percent": 8.0,
        "all_path_min_period_growth_percent": 8.0,
        "worst_setup_slack_drop_ns": 0.25,
        "worst_hold_slack_drop_ns": 0.02,
    },
    "required_metrics": [
        "cell_area", "all_path_min_period_ns",
        "worst_setup_slack_ns", "worst_hold_slack_ns",
    ],
}


class QorGateTests(unittest.TestCase):
    def test_accepts_candidate_inside_reviewed_margins(self):
        result = evaluate(snapshot(), snapshot(area=105, period=2.1, setup=0.9, hold=0.09), POLICY)
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["checks"]), 4)

    def test_rejects_area_regression(self):
        result = evaluate(snapshot(), snapshot(area=109), POLICY)
        self.assertFalse(result["passed"])
        self.assertEqual(result["failures"][0]["metric"], "cell_area")

    def test_rejects_setup_and_hold_degradation(self):
        result = evaluate(snapshot(), snapshot(setup=0.7, hold=0.07), POLICY)
        self.assertFalse(result["passed"])
        self.assertEqual({x["metric"] for x in result["failures"]},
                         {"worst_setup_slack_ns", "worst_hold_slack_ns"})

    def test_rejects_environment_mismatch(self):
        with self.assertRaisesRegex(ValueError, "tool_versions"):
            evaluate(snapshot(), snapshot(tool="yosys 2.0"), POLICY)

    def test_fails_closed_on_missing_metric(self):
        candidate = snapshot()
        candidate["records"][0]["worst_hold_slack_ns"] = None
        with self.assertRaisesRegex(ValueError, "non-finite"):
            evaluate(snapshot(), candidate, POLICY)

    def test_rejects_sdc_mismatch(self):
        candidate = snapshot()
        candidate["records"][0]["sdc_sha256"] = "different"
        with self.assertRaisesRegex(ValueError, "SDC hash"):
            evaluate(snapshot(), candidate, POLICY)


if __name__ == "__main__":
    unittest.main()
