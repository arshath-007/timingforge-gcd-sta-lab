import unittest
from tools.constraint_sensitivity import generate_variants

BASELINE = """create_clock -name core_clk -period 10.000 [get_ports clk]
set_clock_uncertainty -setup 0.150 [get_clocks core_clk]
set_clock_uncertainty -hold 0.050 [get_clocks core_clk]
"""

class ConstraintSensitivityTests(unittest.TestCase):
    def test_generates_three_independent_sensitivity_families(self):
        variants = generate_variants(BASELINE)
        self.assertEqual(len(variants), 9)
        self.assertEqual(sum(x["kind"] == "setup_uncertainty" for x in variants), 3)
        self.assertEqual(sum(x["kind"] == "hold_uncertainty" for x in variants), 3)
        self.assertEqual(sum(x["kind"] == "source_latency_early_late" for x in variants), 3)

    def test_does_not_mutate_input_baseline(self):
        original = BASELINE
        generate_variants(BASELINE)
        self.assertEqual(BASELINE, original)

    def test_rejects_noncanonical_or_ambiguous_baseline(self):
        with self.assertRaises(ValueError):
            generate_variants(BASELINE.replace("set_clock_uncertainty -setup", "# removed setup\nset_clock_uncertainty -setup", 1)
                              .replace("set_clock_uncertainty -setup 0.150 [get_clocks core_clk]\n", ""))

if __name__ == "__main__":
    unittest.main()
