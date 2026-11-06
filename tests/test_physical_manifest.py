import tempfile
import unittest
from pathlib import Path

from tools.physical_manifest import PROVENANCE_FILES, REQUIRED, TOPS, build_manifest, sha256


class PhysicalManifestTests(unittest.TestCase):
    def _make_fixture(self, project: Path) -> Path:
        physical_root = project / "build" / "physical"
        physical_root.mkdir(parents=True)
        for relative in PROVENANCE_FILES:
            target = project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("fixture source " + relative + "\n", encoding="utf-8")
        lines = [
            "Git commit SHA: fixture-commit",
            "ORFS container image digest (declared by workflow): sha256:fixture",
        ]
        for relative in PROVENANCE_FILES:
            if relative.startswith("rtl/"):
                label = f"RTL SHA256 ({relative})"
            elif relative.startswith("constraints/"):
                label = "Source SDC SHA256"
            else:
                label = f"Script SHA256 ({relative})"
            lines.append(f"{label}: {sha256(project / relative)}")
        (physical_root / "tool_versions.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        for top in TOPS:
            work = physical_root / top
            results = work / "results" / "nangate45" / top / "base"
            results.mkdir(parents=True)
            for name in REQUIRED:
                (results / name).write_bytes(("fixture-" + name).encode())
            (work / "postroute_sta.log").write_text(
                "=== POST-ROUTE PARASITIC ANNOTATION ===\nFound 0 unannotated drivers.\nFound 0 partially unannotated drivers.\n"
                "=== TIMINGFORGE POST-ROUTE SETUP CHECK ===\n"
                "=== POST-ROUTE PARASITICS LOADED ===\nSPEF=fixture\n",
                encoding="utf-8",
            )
        return physical_root

    def test_manifest_records_commit_hashes_and_both_designs(self):
        with tempfile.TemporaryDirectory() as tmp:
            physical_root = self._make_fixture(Path(tmp))
            manifest = build_manifest(physical_root)
            self.assertEqual([item["top"] for item in manifest["designs"]], list(TOPS))
            self.assertEqual(manifest["repo_commit_sha"], "fixture-commit")
            self.assertEqual(manifest["schema_version"], "1.1")
            self.assertEqual(set(manifest["source_hashes"]), set(PROVENANCE_FILES))
            self.assertFalse(manifest["signoff_claim"])

    def test_manifest_rejects_missing_spef(self):
        with tempfile.TemporaryDirectory() as tmp:
            physical_root = self._make_fixture(Path(tmp))
            spef = physical_root / TOPS[0] / "results" / "nangate45" / TOPS[0] / "base" / "6_final.spef"
            spef.unlink()
            with self.assertRaisesRegex(FileNotFoundError, "6_final.spef"):
                build_manifest(physical_root)

    def test_manifest_rejects_missing_annotation_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            physical_root = self._make_fixture(Path(tmp))
            log = physical_root / TOPS[1] / "postroute_sta.log"
            log.write_text("=== POST-ROUTE PARASITICS LOADED ===\nSPEF=fixture\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "annotation report"):
                build_manifest(physical_root)


    def test_manifest_rejects_nonzero_unannotated_drivers(self):
        with tempfile.TemporaryDirectory() as tmp:
            physical_root = self._make_fixture(Path(tmp))
            log = physical_root / TOPS[0] / "postroute_sta.log"
            text = log.read_text(encoding="utf-8")
            log.write_text(text.replace("Found 0 unannotated drivers.", "Found 2 unannotated drivers."), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SPEF annotation incomplete"):
                build_manifest(physical_root)

    def test_manifest_rejects_source_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            physical_root = self._make_fixture(project)
            (project / "rtl/gcd_binary_combined.sv").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                build_manifest(physical_root)


if __name__ == "__main__":
    unittest.main()
