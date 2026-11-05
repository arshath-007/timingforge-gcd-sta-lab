import unittest

from tools.lint_sdc import lint_sdc
from tools.make_mutants import MUTATIONS, mutate

GOLDEN = """
create_clock -name core_clk -period 10.000 [get_ports clk]
set_clock_uncertainty -setup 0.150 [get_clocks core_clk]
set_clock_uncertainty -hold 0.050 [get_clocks core_clk]
set_input_delay -clock core_clk -max 1.200 [get_ports start]
set_input_delay -clock core_clk -min 0.100 [get_ports start]
set_input_delay -clock core_clk -max 0.500 [get_ports rst]
set_input_delay -clock core_clk -min 0.050 [get_ports rst]
set_input_delay -clock core_clk -max 1.500 [get_ports a_in*]
set_input_delay -clock core_clk -min 0.100 [get_ports a_in*]
set_input_delay -clock core_clk -max 1.500 [get_ports b_in*]
set_input_delay -clock core_clk -min 0.100 [get_ports b_in*]
set_output_delay -clock core_clk -max 1.000 [get_ports done]
set_output_delay -clock core_clk -min 0.100 [get_ports done]
set_output_delay -clock core_clk -max 1.000 [get_ports busy]
set_output_delay -clock core_clk -min 0.100 [get_ports busy]
set_output_delay -clock core_clk -max 1.500 [get_ports gcd_out*]
set_output_delay -clock core_clk -min 0.100 [get_ports gcd_out*]
"""


class SdcLintTests(unittest.TestCase):
    def test_golden_patterns_pass(self):
        self.assertTrue(any("TF000 PASS" in x for x in lint_sdc(GOLDEN)))

    def test_missing_clock_is_detected(self):
        text = mutate(GOLDEN, MUTATIONS["M01_missing_clock"])
        self.assertTrue(any("TF001 ERROR" in x for x in lint_sdc(text)))

    def test_missing_input_delay_is_detected(self):
        text = mutate(GOLDEN, MUTATIONS["M02_missing_input_delay"])
        self.assertTrue(any("TF101 ERROR" in x and "a_in" in x for x in lint_sdc(text)))

    def test_missing_output_delay_is_detected(self):
        text = mutate(GOLDEN, MUTATIONS["M03_missing_output_delay"])
        self.assertTrue(any("TF201 ERROR" in x and "gcd_out" in x for x in lint_sdc(text)))

    def test_false_path_is_reviewed_not_auto_rejected(self):
        text = mutate(GOLDEN, MUTATIONS["M04_unjustified_false_path"])
        findings = lint_sdc(text)
        self.assertTrue(any("TF301 REVIEW" in x for x in findings))
        self.assertFalse(any("TF301 REVIEW" in x and "ERROR" in x for x in findings))

    def test_near_match_port_name_does_not_count_as_a_in(self):
        text = mutate(GOLDEN, MUTATIONS["M05_near_match_wrong_port"])
        self.assertTrue(any("TF101 ERROR" in x and "a_in" in x for x in lint_sdc(text)))

    def test_missing_hold_uncertainty_is_detected(self):
        text = mutate(GOLDEN, MUTATIONS["M06_missing_hold_uncertainty"])
        self.assertTrue(any("TF402 ERROR" in x for x in lint_sdc(text)))

    def test_nonpositive_clock_period_is_detected(self):
        text = mutate(GOLDEN, MUTATIONS["M07_nonpositive_clock_period"])
        self.assertTrue(any("TF002 ERROR" in x for x in lint_sdc(text)))

    def test_both_minimum_and_maximum_delays_are_required(self):
        text = GOLDEN.replace("set_input_delay -clock core_clk -min 0.100 [get_ports a_in*]\n", "")
        self.assertTrue(any("TF101 ERROR: missing min input delay for port 'a_in'" == x for x in lint_sdc(text)))


    def test_comment_does_not_satisfy_missing_input_delay(self):
        text = GOLDEN.replace(
            "set_input_delay -clock core_clk -min 0.100 [get_ports a_in*]",
            "# set_input_delay -clock core_clk -min 0.100 [get_ports a_in*]",
        )
        self.assertTrue(any("TF101 ERROR: missing min input delay for port 'a_in'" == x for x in lint_sdc(text)))

    def test_partial_bus_pattern_does_not_cover_whole_bus(self):
        text = GOLDEN.replace("[get_ports a_in*]", "[get_ports a_in[0]]")
        self.assertTrue(any("TF101 ERROR" in x and "a_in" in x for x in lint_sdc(text)))

    def test_wrong_clock_reference_does_not_count_as_valid_delay(self):
        text = GOLDEN.replace("-clock core_clk -max 1.200", "-clock typo_clk -max 1.200")
        self.assertTrue(any("TF101 ERROR: missing max input delay for port 'start'" == x for x in lint_sdc(text)))

    def test_grouped_port_patterns_are_supported(self):
        text = GOLDEN.replace("[get_ports a_in*]", "[get_ports {a_in* b_in*}]")
        self.assertFalse(any("TF101 ERROR" in x for x in lint_sdc(text)))


if __name__ == "__main__":
    unittest.main()
