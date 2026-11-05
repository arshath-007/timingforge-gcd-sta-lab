import json
import tempfile
import unittest
from pathlib import Path

from tools.run_benchmark import run_benchmark


class BenchmarkTests(unittest.TestCase):
    def test_scorecard_detects_all_controlled_patterns(self):
        root = Path(__file__).resolve().parents[1]
        source = root / "constraints" / "gcd_baseline.sdc"
        with tempfile.TemporaryDirectory() as temp:
            report = run_benchmark(source, Path(temp))
            self.assertTrue(report["golden_baseline_passed"])
            self.assertEqual(report["fault_cases"], 7)
            self.assertEqual(report["faults_detected"], 7)
            self.assertEqual(report["detection_rate"], 1.0)
            saved = json.loads((Path(temp) / "benchmark_report.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["faults_detected"], 7)
            self.assertIn("No synthesis or STA engine", saved["scope"])


if __name__ == "__main__":
    unittest.main()
