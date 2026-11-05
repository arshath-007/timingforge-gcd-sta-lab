"""Validate and hash TimingForge OpenROAD physical-flow evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

TOPS = ("gcd_binary_combined", "gcd_binary_split")
REQUIRED = (
    "2_floorplan.odb",
    "3_place.odb",
    "4_cts.odb",
    "5_route.odb",
    "6_final.odb",
    "6_final.gds",
    "6_final.spef",
    "6_final.sdc",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(root: Path) -> dict:
    designs = []
    for top in TOPS:
        work = root / top
        results = work / "results" / "nangate45" / top / "base"
        reports = work / "reports" / "nangate45" / top / "base"
        logs = work / "logs" / "nangate45" / top / "base"
        missing = [
            name for name in REQUIRED
            if not (results / name).is_file() or (results / name).stat().st_size == 0
        ]
        if missing:
            raise FileNotFoundError(f"{top}: missing required physical artifacts: {missing}")
        postroute = work / "postroute_sta.log"
        postroute_text = postroute.read_text(encoding="utf-8", errors="replace") if postroute.is_file() else ""
        if "POST-ROUTE PARASITICS LOADED" not in postroute_text or "SPEF=" not in postroute_text:
            raise FileNotFoundError(f"{top}: extracted-parasitic post-route STA log missing or incomplete")
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
            "postroute_sta_log": str(postroute.relative_to(root)),
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        })
    versions = root / "tool_versions.txt"
    if not versions.is_file():
        raise FileNotFoundError("build/physical/tool_versions.txt is required")
    source_sdc = root.parent.parent / "constraints" / "gcd_baseline.sdc"
    if not source_sdc.is_file():
        raise FileNotFoundError("Repository baseline SDC is missing")
    return {
        "schema_version": "1.0",
        "flow": "OpenROAD Flow Scripts",
        "platform": "Nangate45",
        "corner": "typical",
        "timing_stage": "post-route with propagated clocks and extracted SPEF",
        "source_sdc_sha256": sha256(source_sdc),
        "signoff_claim": False,
        "tool_versions_file": str(versions.relative_to(root)),
        "designs": designs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_manifest(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "designs": [item["top"] for item in result["designs"]],
        "physical_artifacts_per_design": [item["artifact_count"] for item in result["designs"]],
        "timing_stage": result["timing_stage"],
        "signoff_claim": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
