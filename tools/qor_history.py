"""Create and compare environment-keyed QoR snapshots."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PLATFORM_REVISION = "11aa833a11488c3a540a1d8eb4caa23fd22df703"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def tool_versions(path: Path) -> dict:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip().lower()] = value.strip()
    return values

def build_snapshot(matrix_path: Path, root: Path = ROOT) -> dict:
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    liberty = root / "build/platform/nangate45/NangateOpenCellLibrary_typical.lib"
    versions = root / "build/tool_versions.txt"
    if not liberty.is_file() or not versions.is_file():
        raise FileNotFoundError("Expected Nangate45 Liberty and tool_versions.txt from the STA workflow")
    source_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True
    ).stdout.strip()
    records = []
    for row in matrix.get("records", []):
        scenario = row["scenario"]
        sdc = (root / "constraints/gcd_baseline.sdc") if scenario == "gcd_baseline" else (
            root / "build/mutants" / (scenario + ".sdc")
        )
        if not sdc.is_file():
            raise FileNotFoundError("Missing scenario SDC: " + str(sdc))
        records.append({
            "top": row["top"],
            "scenario": scenario,
            "sdc_sha256": sha256(sdc),
            "cell_area": row.get("yosys_cell_area"),
            "all_path_min_period_ns": row.get("all_path_min_period_ns"),
            "register_to_register_min_period_ns": row.get("register_to_register_min_period_ns"),
            "worst_setup_slack_ns": row.get("worst_setup_slack_ns"),
            "worst_hold_slack_ns": row.get("worst_hold_slack_ns"),
        })
    return {
        "schema_version": "1.0",
        "source_sha": source_sha,
        "platform": "Nangate45",
        "platform_source_revision": PLATFORM_REVISION,
        "corner": "typical",
        "liberty_sha256": sha256(liberty),
        "tool_versions": tool_versions(versions),
        "records": records,
    }

def compare_snapshots(reference: dict, candidate: dict) -> dict:
    for field in ("platform", "platform_source_revision", "corner", "liberty_sha256", "tool_versions"):
        if reference.get(field) != candidate.get(field):
            raise ValueError("QoR environments differ for " + field)
    ref_rows = {(r["top"], r["scenario"]): r for r in reference.get("records", [])}
    new_rows = {(r["top"], r["scenario"]): r for r in candidate.get("records", [])}
    if set(ref_rows) != set(new_rows):
        raise ValueError("QoR scenario sets differ")
    deltas = []
    metrics = ("cell_area", "all_path_min_period_ns", "register_to_register_min_period_ns",
               "worst_setup_slack_ns", "worst_hold_slack_ns")
    for key in sorted(ref_rows):
        old, new = ref_rows[key], new_rows[key]
        if old.get("sdc_sha256") != new.get("sdc_sha256"):
            raise ValueError("SDC hash differs for " + "/".join(key))
        delta = {"top": key[0], "scenario": key[1], "sdc_sha256": old["sdc_sha256"]}
        for metric in metrics:
            before, after = old.get(metric), new.get(metric)
            delta[metric + "_delta"] = (
                round(after - before, 6) if before is not None and after is not None else None
            )
        deltas.append(delta)
    return {
        "schema_version": "1.0",
        "reference_source_sha": reference.get("source_sha"),
        "candidate_source_sha": candidate.get("source_sha"),
        "environment_match": True,
        "deltas": deltas,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument("matrix", type=Path)
    snapshot.add_argument("--output", type=Path, required=True)
    compare = sub.add_parser("compare")
    compare.add_argument("reference", type=Path)
    compare.add_argument("candidate", type=Path)
    compare.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "snapshot":
        result = build_snapshot(args.matrix)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    else:
        result = compare_snapshots(
            json.loads(args.reference.read_text(encoding="utf-8")),
            json.loads(args.candidate.read_text(encoding="utf-8")),
        )
        rendered = json.dumps(result, indent=2) + "\\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
