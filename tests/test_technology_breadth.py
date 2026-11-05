import unittest
from tools.technology_breadth import (ASAP7_SCENES, ASAP7_LIB_VERSIONS, parse_scene_report, parse_units, parse_sky130_postroute_metrics)


class TechnologyBreadthTests(unittest.TestCase):
    def test_asap7_pvt_scenes_are_distinct(self):
        self.assertEqual(ASAP7_SCENES["ASAP7_BC"]["process"], "FF")
        self.assertEqual(ASAP7_SCENES["ASAP7_TC"]["process"], "TT")
        self.assertEqual(ASAP7_SCENES["ASAP7_WC"]["process"], "SS")
        self.assertEqual(len({x["temperature"] for x in ASAP7_SCENES.values()}), 3)
        self.assertEqual(len({x["voltage_v"] for x in ASAP7_SCENES.values()}), 3)


    def test_asap7_uses_exact_pinned_nldm_revisions(self):
        self.assertEqual(ASAP7_LIB_VERSIONS, {
            "AO": "211120", "INVBUF": "220122", "OA": "211120",
            "SIMPLE": "211120", "SEQ": "220123",
        })

    def test_platform_liberty_units_are_explicit(self):
        self.assertEqual(
            parse_units("""time 1ps\ncapacitance 1fF\n""", "ps", "fF"),
            {"time": "ps", "capacitance": "ff"},
        )
        self.assertEqual(
            parse_units("""time 1ns\ncapacitance 1pF\n""", "ns", "pF"),
            {"time": "ns", "capacitance": "pf"},
        )
        with self.assertRaisesRegex(ValueError, "units mismatch"):
            parse_units("""time 1ns\ncapacitance 1pF\n""", "ps", "fF")

    def test_parses_sky130_postroute_metrics(self):
        log = """
=== POST-ROUTE REGISTER-TO-REGISTER CLOCK PERIOD ===
core_clk period_min = 1.25 fmax = 800.00
=== POST-ROUTE ALL-PATH CLOCK PERIOD ===
core_clk period_min = 2.50 fmax = 400.00
=== POST-ROUTE SETUP SUMMARY ===
worst slack max 3.500
wns max 0.000
tns max 0.000
=== POST-ROUTE HOLD SUMMARY ===
worst slack min 0.025
wns min 0.000
tns min 0.000
"""
        result = parse_sky130_postroute_metrics(log)
        self.assertEqual(result["register_to_register"]["minimum_period_ns"], 1.25)
        self.assertEqual(result["all_path"]["fmax_mhz"], 400.0)
        self.assertEqual(result["setup"]["worst_slack_ns"], 3.5)
        self.assertEqual(result["hold"]["worst_slack_ns"], 0.025)

    def test_parses_setup_hold_and_requires_complete_scene(self):
        log = """
TIMINGFORGE_SCENE_BEGIN ASAP7_BC
TIMINGFORGE_SETUP_BEGIN ASAP7_BC
slack (MET) 12.500
-3.250 slack (VIOLATED)
12.250 slack (MET)
TIMINGFORGE_SETUP_END ASAP7_BC
TIMINGFORGE_HOLD_BEGIN ASAP7_BC
4.500 slack (MET)
TIMINGFORGE_HOLD_END ASAP7_BC
TIMINGFORGE_DRV_BEGIN ASAP7_BC
TIMINGFORGE_DRV_END ASAP7_BC
TIMINGFORGE_SCENE_END ASAP7_BC
"""
        result = parse_scene_report(log, "ASAP7_BC")
        self.assertEqual(result["setup_reported_path_count"], 3)
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
