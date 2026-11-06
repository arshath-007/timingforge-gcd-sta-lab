"""Parse post-route OpenSTA evidence and label cross-flow comparisons honestly."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from tools.physical_annotation import classify_annotation

TOPS = ("gcd_binary_combined", "gcd_binary_split")


def _number(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return float(match.group(1)) if match else None


def _section(text: str, start: str, end: str) -> str:
    parts = text.split(start, 1)
    if len(parts) != 2:
        return ""
    return parts[1].split(end, 1)[0]


def parse_postroute_log(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    if "POST-ROUTE PARASITICS LOADED" not in text or "SPEF=" not in text:
        raise ValueError(f"{path}: extracted SPEF load evidence missing")
    annotation = _section(text, "=== POST-ROUTE PARASITIC ANNOTATION ===",
                          "=== TIMINGFORGE POST-ROUTE SETUP CHECK ===")
    if not annotation.strip() or "TIMINGFORGE_PARASITIC_ANNOTATION_UNSUPPORTED" in annotation:
        raise ValueError(f"{path}: native parasitic annotation report missing")
    top = path.parent.name
    final_netlist = path.parent / "results" / "nangate45" / top / "base" / "6_final.v"
    annotation_metrics = classify_annotation(path, final_netlist)
    reg_text = _section(text, "=== POST-ROUTE REGISTER-TO-REGISTER CLOCK PERIOD ===",
                        "=== POST-ROUTE ALL-PATH CLOCK PERIOD ===")
    all_text = _section(text, "=== POST-ROUTE ALL-PATH CLOCK PERIOD ===",
                        "=== POST-ROUTE SETUP SUMMARY ===")
    reg_period = _number(r"^\s*\S+\s+period_min\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+))", reg_text)
    reg_fmax = _number(r"^\s*\S+\s+period_min\s*=\s*[-+]?(?:\d+\.?\d*|\.\d+)\s+fmax\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+))", reg_text)
    all_period = _number(r"^\s*\S+\s+period_min\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+))", all_text)
    all_fmax = _number(r"^\s*\S+\s+period_min\s*=\s*[-+]?(?:\d+\.?\d*|\.\d+)\s+fmax\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+))", all_text)
    setup = _number(r"^\s*worst slack\s+max\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    hold = _number(r"^\s*worst slack\s+min\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    setup_wns = _number(r"^\s*wns\s+max\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    setup_tns = _number(r"^\s*tns\s+max\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    hold_wns = _number(r"^\s*wns\s+min\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    hold_tns = _number(r"^\s*tns\s+min\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    setup_skew = _section(text, "=== POST-ROUTE SETUP CLOCK SKEW ===",
                          "=== POST-ROUTE HOLD CLOCK SKEW ===")
    hold_skew = _section(text, "=== POST-ROUTE HOLD CLOCK SKEW ===",
                         "=== POST-ROUTE REGISTER-TO-REGISTER CLOCK PERIOD ===")
    drv_slew = _section(text, "=== POST-ROUTE DRV MAX SLEW ===", "=== POST-ROUTE DRV MAX CAPACITANCE ===")
    drv_cap = _section(text, "=== POST-ROUTE DRV MAX CAPACITANCE ===", "=== POST-ROUTE DRV MAX FANOUT ===")
    drv_fanout = _section(text, "=== POST-ROUTE DRV MAX FANOUT ===", "=== POST-ROUTE PARASITICS LOADED ===")
    def drv_count(section: str) -> int | None:
        if not section or "TIMINGFORGE_DRV_UNSUPPORTED" in section:
            return None
        return len(re.findall(r"\(VIOLATED\)", section, re.IGNORECASE))
    if all_period is None or all_period <= 0 or setup is None or hold is None:
        raise ValueError(f"{path}: required all-path period/setup/hold metric missing")
    if reg_period is None or reg_period <= 0:
        raise ValueError(f"{path}: register-to-register minimum-period metric missing")
    if not setup_skew.strip() or not hold_skew.strip() or "TIMINGFORGE_CLOCK_SKEW_UNSUPPORTED" in setup_skew + hold_skew:
        raise ValueError(f"{path}: propagated-clock skew reports missing")
    if any(drv_count(section) is None for section in (drv_slew, drv_cap, drv_fanout)):
        raise ValueError(f"{path}: one or more post-route DRV reports are unsupported or missing")
    return {
        "postroute_register_to_register_min_period_ns": reg_period,
        "postroute_register_to_register_fmax_mhz": reg_fmax,
        "postroute_all_path_min_period_ns": all_period,
        "postroute_all_path_fmax_mhz": all_fmax,
        "postroute_worst_setup_slack_ns": setup,
        "postroute_setup_wns_ns": setup_wns,
        "postroute_setup_tns_ns": setup_tns,
        "postroute_worst_hold_slack_ns": hold,
        "postroute_hold_wns_ns": hold_wns,
        "postroute_hold_tns_ns": hold_tns,
        "setup_clock_skew_report": setup_skew.strip(),
        "hold_clock_skew_report": hold_skew.strip(),
        "clock_skew_supported": bool(setup_skew.strip() and hold_skew.strip()) and "TIMINGFORGE_CLOCK_SKEW_UNSUPPORTED" not in setup_skew + hold_skew,
        "parasitic_annotation_report": annotation.strip(),
        "postroute_reported_unannotated_driver_count": annotation_metrics["reported_unannotated_driver_count"],
        "postroute_dangling_unannotated_driver_count": annotation_metrics["dangling_unannotated_driver_count"],
        "postroute_unannotated_connected_driver_count": annotation_metrics["unannotated_connected_driver_count"],
        "postroute_partially_unannotated_driver_count": annotation_metrics["partially_unannotated_driver_count"],
        "parasitic_annotation_classification": annotation_metrics["unannotated_driver_classification"],
        "postroute_max_slew_violation_count": drv_count(drv_slew),
        "postroute_max_capacitance_violation_count": drv_count(drv_cap),
        "postroute_max_fanout_violation_count": drv_count(drv_fanout),
        "postroute_drv_supported": all(drv_count(section) is not None for section in (drv_slew, drv_cap, drv_fanout)),
        "drv_report": (drv_slew + drv_cap + drv_fanout).strip(),
        "postroute_log": str(path),
    }


def compare(prelayout_path: Path, physical_root: Path) -> dict:
    matrix = json.loads(prelayout_path.read_text(encoding="utf-8"))
    if matrix.get("platform") != "Nangate45 typical Liberty":
        raise ValueError("Pre-layout platform/corner does not match Nangate45 typical")
    repo_root = prelayout_path.resolve().parents[2]
    source_sdc = repo_root / "constraints" / "gcd_baseline.sdc"
    if not source_sdc.is_file():
        raise FileNotFoundError(f"Missing baseline SDC: {source_sdc}")
    sdc_hash = hashlib.sha256(source_sdc.read_bytes()).hexdigest()
    records = {(row.get("top"), row.get("scenario")): row for row in matrix.get("records", [])}
    results = []
    for top in TOPS:
        baseline = records.get((top, "gcd_baseline"))
        if baseline is None:
            raise ValueError(f"Pre-layout golden row missing for {top}")
        post = parse_postroute_log(physical_root / top / "postroute_sta.log")
        pre_period = baseline.get("all_path_min_period_ns")
        pre_setup = baseline.get("worst_setup_slack_ns")
        pre_hold = baseline.get("worst_hold_slack_ns")
        results.append({
            "top": top,
            "platform": "Nangate45",
            "corner": "typical",
            "source_sdc_sha256": sdc_hash,
            "prelayout_all_path_min_period_ns": pre_period,
            "postroute_all_path_min_period_ns": post["postroute_all_path_min_period_ns"],
            "all_path_min_period_delta_ns_observational_only": round(post["postroute_all_path_min_period_ns"] - pre_period, 6) if pre_period is not None else None,
            "prelayout_worst_setup_slack_ns": pre_setup,
            "postroute_worst_setup_slack_ns": post["postroute_worst_setup_slack_ns"],
            "setup_slack_delta_ns_observational_only": round(post["postroute_worst_setup_slack_ns"] - pre_setup, 6) if pre_setup is not None else None,
            "prelayout_worst_hold_slack_ns": pre_hold,
            "postroute_worst_hold_slack_ns": post["postroute_worst_hold_slack_ns"],
            "hold_slack_delta_ns_observational_only": round(post["postroute_worst_hold_slack_ns"] - pre_hold, 6) if pre_hold is not None else None,
            **post,
        })
    return {
        "schema_version": "1.1",
        "comparison": "cross-flow observation: same Nangate45 typical corner and source SDC, but pre-layout and ORFS synthesis netlists are not matched",
        "netlist_matched": False,
        "delta_interpretation": "observational_only; do not attribute differences to routing parasitics alone",
        "signoff_claim": False,
        "designs": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prelayout_matrix", type=Path)
    parser.add_argument("physical_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.prelayout_matrix, args.physical_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "designs": [row["top"] for row in result["designs"]],
        "netlist_matched": result["netlist_matched"],
        "clock_skew_supported": [row["clock_skew_supported"] for row in result["designs"]],
        "signoff_claim": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
