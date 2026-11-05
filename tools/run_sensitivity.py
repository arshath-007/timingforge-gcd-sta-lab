"""Run controlled clock-constraint sensitivity experiments on both GCD netlists."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess

from tools.constraint_sensitivity import generate_variants
from tools.parse_sta_matrix import parse_log

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "constraints" / "gcd_baseline.sdc"
LIBERTY = ROOT / "build/platform/nangate45/NangateOpenCellLibrary_typical.lib"
TECH_LEF = ROOT / "build/platform/nangate45/NangateOpenCellLibrary.tech.lef"
SC_LEF = ROOT / "build/platform/nangate45/NangateOpenCellLibrary.macro.mod.lef"
TOPS = ("gcd_binary_combined", "gcd_binary_split")

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def command_version(command: list[str]) -> str:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
    return (result.stdout or result.stderr).strip().splitlines()[0]

def main() -> int:
    baseline_text = BASELINE.read_text(encoding="utf-8")
    variants = generate_variants(baseline_text)
    out_dir = ROOT / "build/sensitivity/sdc"
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline_hash = sha256(BASELINE)
    liberty_hash = sha256(LIBERTY)
    tool_versions = {"yosys": command_version(["yosys", "-V"]),
                     "openroad": command_version([os.environ.get("STA", "openroad"), "-version"])}
    source_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                                capture_output=True, check=True).stdout.strip()
    records = []
    for variant in variants:
        sdc = out_dir / (variant["name"] + ".sdc")
        sdc.write_text(variant["sdc_text"], encoding="utf-8")
        for top in TOPS:
            log_name = f"sta_{top}_{variant['name']}.log"
            env = os.environ.copy()
            env.update({"TOP": top, "NETLIST": str(ROOT / f"build/{top}.v"),
                        "SDC": str(sdc), "LIBERTY": str(LIBERTY),
                        "TECH_LEF": str(TECH_LEF), "SC_LEF": str(SC_LEF),
                        "STA": os.environ.get("STA", "openroad")})
            subprocess.run(["bash", "scripts/run_sta.sh"], cwd=ROOT, env=env, check=True)
            parsed = parse_log(ROOT / "build/reports" / log_name)
            baseline_log = ROOT / "build/reports" / f"sta_{top}_gcd_baseline.log"
            base = parse_log(baseline_log)
            records.append({
                "top": top, "scenario": variant["name"], "kind": variant["kind"],
                "value_ns": variant["value_ns"],
                "early_ns": variant.get("early_ns"), "late_ns": variant.get("late_ns"),
                "baseline_sdc_sha256": baseline_hash, "variant_sdc_sha256": sha256(sdc),
                "liberty_sha256": liberty_hash, "source_sha": source_sha,
                "tool_versions": tool_versions, "log_file": f"build/reports/{log_name}",
                "worst_setup_slack_ns": parsed["worst_setup_slack_ns"],
                "worst_hold_slack_ns": parsed["worst_hold_slack_ns"],
                "all_path_min_period_ns": parsed["all_path_min_period_ns"],
                "register_to_register_min_period_ns": parsed["register_to_register_min_period_ns"],
                "setup_slack_delta_vs_baseline_ns": (
                    round(parsed["worst_setup_slack_ns"] - base["worst_setup_slack_ns"], 6)
                    if parsed["worst_setup_slack_ns"] is not None and base["worst_setup_slack_ns"] is not None else None),
                "hold_slack_delta_vs_baseline_ns": (
                    round(parsed["worst_hold_slack_ns"] - base["worst_hold_slack_ns"], 6)
                    if parsed["worst_hold_slack_ns"] is not None and base["worst_hold_slack_ns"] is not None else None),
            })
    summary = {"schema_version": "1.0", "source_sha": source_sha,
               "baseline_sdc_sha256": baseline_hash, "liberty_sha256": liberty_hash,
               "tool_versions": tool_versions,
               "method": "One constraint parameter varied at a time from the immutable golden SDC; baseline and variant use the same mapped netlist, Liberty, engine and analysis script.",
               "parasitics": "Pre-layout; no SPEF; ideal clock network with explicit source-latency sensitivity variants.",
               "records": records}
    target = ROOT / "build/sensitivity/sensitivity_summary.json"
    target.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target} ({len(records)} experiments)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
