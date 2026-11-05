import unittest
from tools.technology_breadth import ASAP7_SCENES, parse_scene_report


class TechnologyBreadthTests(unittest.TestCase):
    def test_asap7_pvt_scenes_are_distinct(self):
        self.assertEqual(ASAP7_SCENES["ASAP7_BC"]["process"], "FF")
        self.assertEqual(ASAP7_SCENES["ASAP7_TC"]["process"], "TT")
        self.assertEqual(ASAP7_SCENES["ASAP7_WC"]["process"], "SS")
        self.assertEqual(len({x["temperature"] for x in ASAP7_SCENES.values()}), 3)
        self.assertEqual(len({x["voltage_v"] for x in ASAP7_SCENES.values()}), 3)

    def test_parses_setup_hold_and_requires_complete_scene(self):
        log = """
TIMINGFORGE_SCENE_BEGIN ASAP7_BC
TIMINGFORGE_SETUP_BEGIN ASAP7_BC
slack (MET) 12.500
slack (VIOLATED) -3.250
TIMINGFORGE_SETUP_END ASAP7_BC
TIMINGFORGE_HOLD_BEGIN ASAP7_BC
slack (MET) 4.500
TIMINGFORGE_HOLD_END ASAP7_BC
TIMINGFORGE_DRV_BEGIN ASAP7_BC
TIMINGFORGE_DRV_END ASAP7_BC
TIMINGFORGE_SCENE_END ASAP7_BC
"""
        result = parse_scene_report(log, "ASAP7_BC")
        self.assertEqual(result["setup_reported_path_count"], 2)
        self.assertEqual(result["setup_worst_reported_slack_ps"], -3.25)
        self.assertEqual(result["hold_worst_reported_slack_ps"], 4.5)
        self.assertTrue(result["drv_report_present"])

    def test_rejects_missing_scene_or_path_inventory(self):
        with self.assertRaisesRegex(ValueError, "missing complete"):
            parse_scene_report("", "ASAP7_WC")
        log = """
TIMINGFORGE_SCENE_BEGIN ASAP7_TC
TIMINGFORGE_SETUP_BEGIN ASAP7_TC
TIMINGFORGE_SETUP_END ASAP7_TC
TIMINGFORGE_HOLD_BEGIN ASAP7_TC
TIMINGFORGE_HOLD_END ASAP7_TC
TIMINGFORGE_DRV_BEGIN ASAP7_TC
TIMINGFORGE_DRV_END ASAP7_TC
TIMINGFORGE_SCENE_END ASAP7_TC
"""
        with self.assertRaisesRegex(ValueError, "no setup path"):
            parse_scene_report(log, "ASAP7_TC")


if __name__ == "__main__":
    unittest.main()
