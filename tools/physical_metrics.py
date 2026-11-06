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


def _stage_metrics(log_dir: Path, top: str) -> dict:
    stages = {
        "orfs_synthesis": ("1_synth.json", "synth"),
        "global_placement": ("3_3_place_gp.json", "globalplace"),
        "clock_tree_synthesis": ("4_1_cts.json", "cts"),
        "global_route": ("5_1_grt.json", "globalroute"),
        "final": ("6_report.json", "finish"),
    }
    result = {}
    for stage, (filename, prefix) in stages.items():
        path = log_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"{top}: missing ORFS stage metrics {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        required = {
            "instance_count": f"{prefix}__design__instance__count__stdcell",
            "instance_area": f"{prefix}__design__instance__area__stdcell",
            "total_instance_count": f"{prefix}__design__instance__count",
            "total_instance_area": f"{prefix}__design__instance__area",
        }
        missing = [key for key, source in required.items() if source not in data]
        if missing:
            raise ValueError(f"{top}: {filename} missing standard-cell metrics {missing}")
        result[stage] = {
            "standard_cell_instance_count": int(data[required["instance_count"]]),
            "standard_cell_area": float(data[required["instance_area"]]),
            "total_instance_count_including_physical_cells": int(data[required["total_instance_count"]]),
            "total_instance_area": float(data[required["total_instance_area"]]),
            "source_report": filename,
        }
    return result


def _prelayout_synthesis_metrics(build_root: Path, top: str, matrix_row: dict) -> dict:
    path = build_root / f"yosys_{top}.log"
    if not path.is_file():
        raise FileNotFoundError(f"{top}: pre-layout Yosys synthesis log missing: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    # Yosys's mapped-statistics table may render area in scientific notation
    # and rounds that display value (for example, "1.68E+03"). Use the table
    # for its integer cell count and the explicit Chip area line for precision.
    number = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
    areas = re.findall(r"Chip area for module .*?:\s*(" + number + r")", text)
    rows = re.findall(
        r"^\s*(\d+)\s+" + number + r"\s+cells\s*$",
        text,
        re.MULTILINE,
    )
    area = float(areas[-1]) if areas else matrix_row.get("yosys_cell_area")
    if area is None or not rows:
        raise ValueError(f"{top}: pre-layout synthesis area/cell count missing from {path}")
    count = int(rows[-1])
    if count <= 0 or float(area) <= 0:
        raise ValueError(f"{top}: pre-layout synthesis metrics must be positive in {path}")
    return {
        "standard_cell_instance_count": count,
        "standard_cell_area": float(area),
        "source_log": str(path),
    }


def parse_presynth_log(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    setup_check = _section(text, "=== ORFS POST-SYNTHESIS SETUP CHECK ===", "=== ORFS POST-SYNTHESIS CLOCK PROPERTIES ===")
    setup_warnings = [line.strip() for line in setup_check.splitlines() if line.strip().startswith("Warning:")]
    if setup_warnings:
        raise ValueError(f"{path}: post-synthesis check_setup reported warnings: {setup_warnings[:10]}")
    if "ORFS POST-SYNTHESIS REGISTER-TO-REGISTER CLOCK PERIOD" not in text:
        raise ValueError(f"{path}: ORFS post-synthesis STA heading missing")
    reg = _section(text, "=== ORFS POST-SYNTHESIS REGISTER-TO-REGISTER CLOCK PERIOD ===",
                   "=== ORFS POST-SYNTHESIS ALL-PATH CLOCK PERIOD ===")
    all_path = _section(text, "=== ORFS POST-SYNTHESIS ALL-PATH CLOCK PERIOD ===",
                        "=== ORFS POST-SYNTHESIS SETUP SUMMARY ===")
    def period(section_text: str) -> tuple[float | None, float | None]:
        match = re.search(
            r"^\s*\S+\s+period_min\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+))"
            r"\s+fmax\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+)|inf|nan)",
            section_text,
            re.MULTILINE | re.IGNORECASE,
        )
        if not match:
            return None, None
        period_value = float(match.group(1))
        fmax_text = match.group(2).lower()
        fmax_value = float(fmax_text) if fmax_text not in {"inf", "+inf", "-inf", "nan"} else None
        # OpenROAD reports 0.00 ns / infinite Fmax when its register-only
        # minimum-period query has no usable result. Preserve that as unavailable.
        if period_value <= 0 or fmax_value is None:
            return None, None
        return period_value, fmax_value

    reg_period, reg_fmax = period(reg)
    all_period, all_fmax = period(all_path)
    setup = _number(r"^\s*worst slack\s+max\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    hold = _number(r"^\s*worst slack\s+min\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    if all_period is None or all_period <= 0 or setup is None or hold is None:
        raise ValueError(f"{path}: incomplete ORFS post-synthesis timing metrics")
    return {
        "register_to_register_min_period_ns": reg_period,
        "register_to_register_fmax_mhz": reg_fmax,
        "register_to_register_period_available": reg_period is not None,
        "register_to_register_period_note": (
            None if reg_period is not None else
            "OpenROAD reported a zero register-only period / infinite Fmax; retained as unavailable."
        ),
        "all_path_min_period_ns": all_period,
        "all_path_fmax_mhz": all_fmax,
        "worst_setup_slack_ns": setup,
        "worst_hold_slack_ns": hold,
        "log": str(path),
    }


def compare(prelayout_path: Path, physical_root: Path, repo_root: Path | None = None) -> dict:
    matrix = json.loads(prelayout_path.read_text(encoding="utf-8"))
    if matrix.get("platform") != "Nangate45 typical Liberty":
        raise ValueError("Pre-layout platform/corner does not match Nangate45 typical")
    repo_root = (repo_root or Path.cwd()).resolve()
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
        synthesis_sta = parse_presynth_log(physical_root / top / "presynth_sta.log")
        stage_metrics = _stage_metrics(
            physical_root / top / "logs" / "nangate45" / top / "base", top
        )
        prelayout_synthesis = _prelayout_synthesis_metrics(physical_root.parent, top, baseline)
        orfs_synthesis = stage_metrics["orfs_synthesis"]
        pre_period = baseline.get("all_path_min_period_ns")
        pre_setup = baseline.get("worst_setup_slack_ns")
        pre_hold = baseline.get("worst_hold_slack_ns")
        results.append({
            "top": top,
            "platform": "Nangate45",
            "corner": "typical",
            "source_sdc_sha256": sdc_hash,
            "prelayout_synthesis": prelayout_synthesis,
            "orfs_synthesis": orfs_synthesis,
            "synthesis_flow_area_delta_orfs_minus_prelayout": round(
                orfs_synthesis["standard_cell_area"] - prelayout_synthesis["standard_cell_area"], 6
            ),
            "synthesis_flow_area_delta_percent_orfs_vs_prelayout": round(
                100.0 * (orfs_synthesis["standard_cell_area"] / prelayout_synthesis["standard_cell_area"] - 1.0), 3
            ),
            "synthesis_flow_instance_count_delta_orfs_minus_prelayout": (
                orfs_synthesis["standard_cell_instance_count"] - prelayout_synthesis["standard_cell_instance_count"]
            ),
            "orfs_stage_metrics": stage_metrics,
            "orfs_post_synthesis_sta": synthesis_sta,
            "orfs_synthesis_to_postroute": {
                "same_orfs_synthesis_lineage": True,
                "exact_netlist_match": False,
                "interpretation": "post-synthesis versus final routed implementation in one ORFS flow; placement/CTS/timing repair may resize or buffer the netlist",
                "register_to_register_min_period_delta_ns": (
                    round(post["postroute_register_to_register_min_period_ns"] - synthesis_sta["register_to_register_min_period_ns"], 6)
                    if post.get("postroute_register_to_register_min_period_ns") is not None
                    and synthesis_sta.get("register_to_register_min_period_ns") is not None
                    else None
                ),
                "register_to_register_period_delta_available": (
                    post.get("postroute_register_to_register_min_period_ns") is not None
                    and synthesis_sta.get("register_to_register_min_period_ns") is not None
                ),
                "all_path_min_period_delta_ns": round(
                    post["postroute_all_path_min_period_ns"] - synthesis_sta["all_path_min_period_ns"], 6
                ),
                "worst_setup_slack_delta_ns": round(
                    post["postroute_worst_setup_slack_ns"] - synthesis_sta["worst_setup_slack_ns"], 6
                ),
                "worst_hold_slack_delta_ns": round(
                    post["postroute_worst_hold_slack_ns"] - synthesis_sta["worst_hold_slack_ns"], 6
                ),
            },
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
        "schema_version": "1.2",
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
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(),
                        help="Repository root containing constraints/gcd_baseline.sdc")
    args = parser.parse_args()
    result = compare(args.prelayout_matrix, args.physical_root, args.repo_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
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
