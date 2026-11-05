import unittest

from tools.lint_sdc import lint_sdc
from tools.make_mutants import MUTATIONS, mutate

GOLDEN = """
create_clock -name core_clk -period 10.000 [get_ports clk]
set_input_delay -clock core_clk -max 1.200 [get_ports start]
set_input_delay -clock core_clk -max 0.500 [get_ports rst]
set_input_delay -clock core_clk -max 1.500 [get_ports a_in*]
set_input_delay -clock core_clk -max 1.500 [get_ports b_in*]
set_output_delay -clock core_clk -max 1.000 [get_ports done]
set_output_delay -clock core_clk -max 1.000 [get_ports busy]
set_output_delay -clock core_clk -max 1.500 [get_ports gcd_out*]
"""


class SdcLintTests(unittest.TestCase):
    def test_golden_patterns_pass(self):
        self.assertTrue(any("TF000 PASS" in x for x in lint_sdc(GOLDEN)))

    def test_missing_clock_is_detected(self):
        text = mutate(GOLDEN, MUTATIONS["M01_missing_clock"])
        self.assertTrue(any("TF001 ERROR" in x for x in lint_sdc(text)))

    def test_missing_input_delay_is_detected(self):
        text = mutate(GOLDEN, MUTATIONS["M02_missing_input_delay"])
        self.assertTrue(any("a_in" in x and "ERROR" in x for x in lint_sdc(text)))

    def test_missing_output_delay_is_detected(self):
        text = mutate(GOLDEN, MUTATIONS["M03_missing_output_delay"])
        self.assertTrue(any("gcd_out" in x and "ERROR" in x for x in lint_sdc(text)))

    def test_false_path_is_reviewed_not_auto_rejected(self):
        text = mutate(GOLDEN, MUTATIONS["M04_unjustified_false_path"])
        self.assertTrue(any("TF301 REVIEW" in x for x in lint_sdc(text)))
        self.assertFalse(any("TF301 REVIEW" in x and "ERROR" in x for x in lint_sdc(text)))


if __name__ == "__main__":
    unittest.main()
