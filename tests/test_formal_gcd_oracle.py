import math
import re
import unittest
from pathlib import Path


class FormalGcdOracleTests(unittest.TestCase):
    def test_formal_width_three_oracle_is_exhaustive_and_correct(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "formal" / "gcd_oracle_3bit.sv").read_text(encoding="utf-8")
        rows = re.findall(
            r"6'b([01]{6}):\\s*expected_gcd\\s*=\\s*3'd([0-7]);",
            source,
        )
        actual = {}
        for operand_bits, result in rows:
            a = int(operand_bits[:3], 2)
            b = int(operand_bits[3:], 2)
            self.assertNotIn((a, b), actual, "duplicate oracle input pair")
            actual[(a, b)] = int(result)
        expected = {
            (a, b): math.gcd(a, b)
            for a in range(8)
            for b in range(8)
        }
        self.assertEqual(len(actual), 64)
        self.assertEqual(actual, expected)

    def test_formal_miter_uses_oracle_for_both_architectures(self):
        root = Path(__file__).resolve().parents[1]
        miter = (root / "formal" / "gcd_equiv.sv").read_text(encoding="utf-8")
        script = (root / "scripts" / "run_formal.sh").read_text(encoding="utf-8")
        self.assertIn("gcd_oracle_3bit u_oracle", miter)
        self.assertIn("assert(gcd_combined == expected_gcd)", miter)
        self.assertIn("assert(gcd_split == expected_gcd)", miter)
        self.assertIn("formal/gcd_oracle_3bit.sv", script)


if __name__ == "__main__":
    unittest.main()
