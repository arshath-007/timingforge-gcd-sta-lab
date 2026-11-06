"""Validate and hash TimingForge OpenROAD physical-flow evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from tools.physical_annotation import classify_annotation

TOPS = ("gcd_binary_combined", "gcd_binary_split")
REQUIRED = (
    "2_floorplan.odb", "3_place.odb", "4_cts.odb", "5_route.odb",
    "1_2_yosys.v", "1_2_yosys.sdc", "1_synth.json", "3_3_place_gp.json", "4_1_cts.json", "5_1_grt.json", "6_report.json",
    "6_final.odb", "6_final.gds", "6_final.v", "6_final.spef", "6_final.sdc",
)
PROVENANCE_FILES = (
    "rtl/gcd_binary_combined.sv", "rtl/gcd_binary_split.sv",
    "constraints/gcd_baseline.sdc", "scripts/run_physical.sh",
    "scripts/postroute_sta.tcl", "scripts/presynth_sta.tcl", "tools/physical_manifest.py",
    "tools/physical_metrics.py", "tools/physical_annotation.py",
    "physical/config/gcd_binary_combined.mk", "physical/config/gcd_binary_split.mk",
    ".github/workflows/physical-design.yml",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _value(text: str, label: str) -> str:
    match = re.search(r"^" + re.escape(label) + r":\s*(.+)$", text, re.MULTILINE)
    if not match:
        raise ValueError(f"tool_versions.txt is missing {label}")
    return match.group(1).strip()


def build_manifest(root: Path, repo_root: Path | None = None) -> dict:
    root = root.resolve()
    repo_root = (repo_root or root.parent.parent).resolve()
    versions_path = root / "tool_versions.txt"
    if not versions_path.is_file():
        raise FileNotFoundError("build/physical/tool_versions.txt is required")
    versions = versions_path.read_text(encoding="utf-8")
    commit_sha = _value(versions, "Git commit SHA")
    image_digest = _value(versions, "ORFS container image digest (declared by workflow)")
    source_hashes = {}
    for relative in PROVENANCE_FILES:
        source = repo_root / relative
        if not source.is_file():
            raise FileNotFoundError(f"Required provenance source missing: {relative}")
        actual = sha256(source)
        source_hashes[relative] = actual
        if relative.startswith("rtl/"):
            label = f"RTL SHA256 ({relative})"
        elif relative.startswith("constraints/"):
            label = "Source SDC SHA256"
        elif relative.startswith("physical/config/"):
            label = f"Config SHA256 ({relative})"
        elif relative.startswith(".github/"):
            label = "Workflow SHA256 (.github/workflows/physical-design.yml)"
        else:
            label = f"Script SHA256 ({relative})"
        recorded = _value(versions, label)
        if recorded != actual:
            raise ValueError(f"Provenance hash mismatch for {relative}: recorded {recorded}, actual {actual}")

    designs = []
    for top in TOPS:
        work = root / top
        results = work / "results" / "nangate45" / top / "base"
        reports = work / "reports" / "nangate45" / top / "base"
        logs = work / "logs" / "nangate45" / top / "base"
        missing = [name for name in REQUIRED if not (results / name).is_file() or (results / name).stat().st_size == 0]
        if missing:
            raise FileNotFoundError(f"{top}: missing required physical artifacts: {missing}")
        presynth = work / "presynth_sta.log"
        if not presynth.is_file():
            raise FileNotFoundError(f"{top}: ORFS post-synthesis STA log missing")
        if "ORFS POST-SYNTHESIS REGISTER-TO-REGISTER CLOCK PERIOD" not in presynth.read_text(encoding="utf-8", errors="replace"):
            raise ValueError(f"{top}: ORFS post-synthesis STA evidence incomplete")
        postroute = work / "postroute_sta.log"
        if not postroute.is_file():
            raise FileNotFoundError(f"{top}: post-route STA log missing")
        log_text = postroute.read_text(encoding="utf-8", errors="replace")
        if "POST-ROUTE PARASITICS LOADED" not in log_text or "SPEF=" not in log_text:
            raise ValueError(f"{top}: SPEF load evidence missing")
        if "=== POST-ROUTE PARASITIC ANNOTATION ===" not in log_text or "=== TIMINGFORGE POST-ROUTE SETUP CHECK ===" not in log_text:
            raise ValueError(f"{top}: native parasitic annotation report missing")
        annotation_metrics = classify_annotation(postroute, results / "6_final.v")

        artifacts = []
        for path in sorted(p for p in work.rglob("*") if p.is_file()):
            if path.name.endswith((".odb", ".gds", ".spef", ".sdc", ".def", ".v", ".rpt", ".json", ".log")):
                artifacts.append({
                    "path": str(path.relative_to(root)),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256(path),
                })
        designs.append({
            "top": top,
            "result_directory": str(results.relative_to(root)),
            "reports_directory": str(reports.relative_to(root)),
            "logs_directory": str(logs.relative_to(root)),
            "final_odb": str((results / "6_final.odb").relative_to(root)),
            "final_gds": str((results / "6_final.gds").relative_to(root)),
            "final_spef": str((results / "6_final.spef").relative_to(root)),
            "final_sdc_sha256": sha256(results / "6_final.sdc"),
            "orfs_synthesis_netlist": str((results / "1_2_yosys.v").relative_to(root)),
            "presynth_sta_log": str(presynth.relative_to(root)),
            "postroute_sta_log": str(postroute.relative_to(root)),
            "parasitic_annotation": annotation_metrics,
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        })
    return {
        "schema_version": "1.2",
        "flow": "OpenROAD Flow Scripts",
        "platform": "Nangate45",
        "corner": "typical",
        "timing_stage": "post-route with propagated clocks and extracted SPEF",
        "repo_commit_sha": commit_sha,
        "orfs_image_digest_declared_by_workflow": image_digest,
        "source_hashes": source_hashes,
        "source_sdc_sha256": source_hashes["constraints/gcd_baseline.sdc"],
        "signoff_claim": False,
        "tool_versions_file": str(versions_path.relative_to(root)),
        "designs": designs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args()
    result = build_manifest(args.root, args.repo_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "designs": [item["top"] for item in result["designs"]],
        "physical_artifacts_per_design": [item["artifact_count"] for item in result["designs"]],
        "repo_commit_sha": result["repo_commit_sha"],
        "timing_stage": result["timing_stage"],
        "signoff_claim": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
