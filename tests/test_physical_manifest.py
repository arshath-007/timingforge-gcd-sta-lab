import tempfile
import unittest
from pathlib import Path

from tools.physical_manifest import REQUIRED, TOPS, build_manifest


class PhysicalManifestTests(unittest.TestCase):
    def _make_fixture(self, project: Path) -> Path:
        physical_root = project / "build" / "physical"
        physical_root.mkdir(parents=True)
        (physical_root / "tool_versions.txt").write_text("OpenROAD: test\n", encoding="utf-8")
        constraints = project / "constraints"
        constraints.mkdir()
        (constraints / "gcd_baseline.sdc").write_text("create_clock", encoding="utf-8")
        for top in TOPS:
            work = physical_root / top
            results = work / "results" / "nangate45" / top / "base"
            results.mkdir(parents=True)
            for name in REQUIRED:
                (results / name).write_bytes(("fixture-" + name).encode())
            (work / "postroute_sta.log").write_text(
                "=== POST-ROUTE PARASITICS LOADED ===\nSPEF=fixture\n",
                encoding="utf-8",
            )
        return physical_root

    def test_manifest_requires_both_complete_physical_designs(self):
        with tempfile.TemporaryDirectory() as tmp:
            physical_root = self._make_fixture(Path(tmp))
            manifest = build_manifest(physical_root)
            self.assertEqual([item["top"] for item in manifest["designs"]], list(TOPS))
            self.assertEqual(manifest["timing_stage"], "post-route with propagated clocks and extracted SPEF")
            self.assertFalse(manifest["signoff_claim"])
            self.assertTrue(all(item["artifact_count"] >= len(REQUIRED) for item in manifest["designs"]))
            self.assertTrue(manifest["source_sdc_sha256"])

    def test_manifest_rejects_missing_spef(self):
        with tempfile.TemporaryDirectory() as tmp:
            physical_root = self._make_fixture(Path(tmp))
            spef = physical_root / TOPS[0] / "results" / "nangate45" / TOPS[0] / "base" / "6_final.spef"
            spef.unlink()
            with self.assertRaisesRegex(FileNotFoundError, "6_final.spef"):
                build_manifest(physical_root)

    def test_manifest_rejects_missing_postroute_sta_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            physical_root = self._make_fixture(Path(tmp))
            (physical_root / TOPS[1] / "postroute_sta.log").unlink()
            with self.assertRaisesRegex(FileNotFoundError, "post-route STA"):
                build_manifest(physical_root)


if __name__ == "__main__":
    unittest.main()
