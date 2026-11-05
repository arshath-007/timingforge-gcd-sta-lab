import unittest

from tools.filter_asap7_libs import filter_liberty


class FilterAsap7LibertyTests(unittest.TestCase):
    def test_removes_only_corner_inconsistent_cells_and_keeps_nested_blocks(self):
        source = """
library (test) {
  cell (XOR2x1_ASAP7_75t_R) {
    area : 1.0;
    pin (A) { direction : input; }
    pin (Y) {
      direction : output;
      timing () { related_pin : "A"; }
    }
  }
  cell (AND2x2_ASAP7_75t_R) {
    area : 1.0;
    pin (Y) { direction : output; }
  }
  cell (XNOR2x2_ASAP7_75t_R) { area : 1.0; }
  cell (HAxp5_ASAP7_75t_R) { area : 1.0; }
}
"""
        filtered, removed = filter_liberty(source)
        self.assertIn("AND2x2_ASAP7_75t_R", filtered)
        self.assertNotIn("XOR2x1_ASAP7_75t_R", filtered)
        self.assertNotIn("XNOR2x2_ASAP7_75t_R", filtered)
        self.assertNotIn("HAxp5_ASAP7_75t_R", filtered)
        self.assertEqual(
            removed,
            ["HAxp5_ASAP7_75t_R", "XNOR2x2_ASAP7_75t_R", "XOR2x1_ASAP7_75t_R"],
        )

    def test_requires_at_least_one_excluded_cell(self):
        with self.assertRaisesRegex(ValueError, "no excluded"):
            filter_liberty("library (test) { cell (AND2x2) { area : 1.0; } }")


if __name__ == "__main__":
    unittest.main()
