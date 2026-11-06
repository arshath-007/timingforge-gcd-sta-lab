"""Summarise physical implementation variation and clock-period closure experiments."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from tools.physical_metrics import parse_postroute_log

TOPS = ("gcd_binary_combined", "gcd_binary_split")


def _report_metrics(run_dir: Path, top: str) -> dict:
    report = run_dir / top / "logs" / "nangate45" / top / "base" / "6_report.json"
    if not report.is_file():
        raise FileNotFoundError(f"missing final ORFS report: {report}")
    data = json.loads(report.read_text(encoding="utf-8"))
    prefix = "finish__design__instance__"
    required = {
        "standard_cell_instance_count": prefix + "count__stdcell",
        "standard_cell_area": prefix + "area__stdcell",
        "clock_buffer_count": prefix + "count__class:clock_buffer",
        "timing_repair_buffer_count": prefix + "count__class:timing_repair_buffer",
        "inverter_count": prefix + "count__class:inverter",
    }
    missing = [name for name, key in required.items() if key not in data]
    if missing:
        raise ValueError(f"{top}: final ORFS report missing fields {missing}")
    return {name: (float(data[key]) if name == "standard_cell_area" else int(data[key]))
            for name, key in required.items()}


def _mean_range(values: list[float]) -> dict:
    return {
        "count": len(values),
        "mean": round(statistics.mean(values), 6) if values else None,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "range": round(max(values) - min(values), 6) if values else None,
        "population_stddev": round(statistics.pstdev(values), 6) if len(values) > 1 else 0.0 if values else None,
    }


def collect(root: Path) -> dict:
    runs = []
    for metadata_path in sorted(root.glob("**/metadata.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        top = metadata["top"]
        run_dir = metadata_path.parent
        if metadata.get("flow_status") != "success":
            runs.append({**metadata, "evidence_status": "flow_failed"})
            continue
        try:
            post = parse_postroute_log(run_dir / "postroute_sta.log")
            physical = _report_metrics(run_dir.parent, top)
        except Exception as exc:
            runs.append({**metadata, "evidence_status": "postroute_evidence_failed", "error": str(exc)})
            continue
        setup = post.get("postroute_worst_setup_slack_ns")
        hold = post.get("postroute_worst_hold_slack_ns")
        drv = [
            post.get("postroute_max_slew_violation_count"),
            post.get("postroute_max_capacitance_violation_count"),
            post.get("postroute_max_fanout_violation_count"),
        ]
        closure = (
            setup is not None and setup >= 0
            and hold is not None and hold >= 0
            and all(value == 0 for value in drv)
            and post.get("postroute_unannotated_connected_driver_count") == 0
        )
        runs.append({
            **metadata,
            "evidence_status": "parsed",
            **physical,
            "postroute_register_to_register_min_period_ns": post.get("postroute_register_to_register_min_period_ns"),
            "postroute_all_path_min_period_ns": post.get("postroute_all_path_min_period_ns"),
            "postroute_worst_setup_slack_ns": setup,
            "postroute_setup_wns_ns": post.get("postroute_setup_wns_ns"),
            "postroute_setup_tns_ns": post.get("postroute_setup_tns_ns"),
            "postroute_worst_hold_slack_ns": hold,
            "postroute_hold_wns_ns": post.get("postroute_hold_wns_ns"),
            "postroute_hold_tns_ns": post.get("postroute_hold_tns_ns"),
            "postroute_max_slew_violation_count": drv[0],
            "postroute_max_capacitance_violation_count": drv[1],
            "postroute_max_fanout_violation_count": drv[2],
            "parasitic_annotation": post.get("parasitic_annotation_classification"),
            "timing_closure_pass": closure,
        })

    variance = [row for row in runs if row.get("experiment") == "variance" and row.get("evidence_status") == "parsed"]
    by_top = {}
    for top in TOPS:
        rows = [row for row in variance if row["top"] == top]
        by_top[top] = {
            "register_to_register_period_ns": _mean_range([r["postroute_register_to_register_min_period_ns"] for r in rows if r.get("postroute_register_to_register_min_period_ns") is not None]),
            "all_path_period_ns": _mean_range([r["postroute_all_path_min_period_ns"] for r in rows if r.get("postroute_all_path_min_period_ns") is not None]),
            "standard_cell_area": _mean_range([r["standard_cell_area"] for r in rows]),
            "standard_cell_instance_count": _mean_range([r["standard_cell_instance_count"] for r in rows]),
            "clock_buffer_count": _mean_range([r["clock_buffer_count"] for r in rows]),
            "timing_repair_buffer_count": _mean_range([r["timing_repair_buffer_count"] for r in rows]),
        }
    variance_pairs = []
    labels = sorted({row["variant"] for row in variance})
    for label in labels:
        pair = {row["top"]: row for row in variance if row["variant"] == label}
        if set(pair) != set(TOPS):
            continue
        c = pair["gcd_binary_combined"]
        s = pair["gcd_binary_split"]
        cp = c.get("postroute_register_to_register_min_period_ns")
        sp = s.get("postroute_register_to_register_min_period_ns")
        variance_pairs.append({
            "variant": label,
            "core_utilization": c.get("core_utilization"),
            "place_density": c.get("place_density"),
            "gpl_random_seed": c.get("gpl_random_seed"),
            "combined_register_period_ns": cp,
            "split_register_period_ns": sp,
            "faster_register_period_architecture": (
                "combined" if cp is not None and sp is not None and cp < sp
                else "split" if cp is not None and sp is not None and sp < cp
                else "tie_or_unavailable"
            ),
            "combined_area": c.get("standard_cell_area"),
            "split_area": s.get("standard_cell_area"),
        })

    clock = [row for row in runs if row.get("experiment") == "clock_sweep"]
    clock_sweep = []
    for period in sorted({row.get("clock_period_ns") for row in clock if row.get("clock_period_ns") is not None}):
        group = [row for row in clock if row.get("clock_period_ns") == period]
        clock_sweep.append({
            "clock_period_ns": period,
            "designs": [{
                "top": row["top"],
                "flow_status": row.get("flow_status"),
                "evidence_status": row.get("evidence_status"),
                "setup_wns_ns": row.get("postroute_setup_wns_ns"),
                "setup_tns_ns": row.get("postroute_setup_tns_ns"),
                "hold_wns_ns": row.get("postroute_hold_wns_ns"),
                "hold_tns_ns": row.get("postroute_hold_tns_ns"),
                "standard_cell_area": row.get("standard_cell_area"),
                "standard_cell_instance_count": row.get("standard_cell_instance_count"),
                "clock_buffer_count": row.get("clock_buffer_count"),
                "timing_repair_buffer_count": row.get("timing_repair_buffer_count"),
                "timing_closure_pass": row.get("timing_closure_pass"),
            } for row in sorted(group, key=lambda x: x["top"])],
        })

    wins = {name: sum(row["faster_register_period_architecture"] == name for row in variance_pairs)
            for name in ("combined", "split")}
    return {
        "schema_version": "1.0",
        "scope": "Nangate45 typical-corner ORFS physical variation and clock-period sweep; not signoff",
        "run_count": len(runs),
        "parsed_run_count": sum(row.get("evidence_status") == "parsed" for row in runs),
        "failed_run_count": sum(row.get("evidence_status") != "parsed" for row in runs),
        "variance_run_count": sum(row.get("experiment") == "variance" for row in runs),
        "variance_parsed_run_count": sum(row.get("experiment") == "variance" and row.get("evidence_status") == "parsed" for row in runs),
        "clock_sweep_run_count": sum(row.get("experiment") == "clock_sweep" for row in runs),
        "variance_summary_by_architecture": by_top,
        "variance_pairwise_register_period_wins": wins,
        "variance_pairwise_results": variance_pairs,
        "clock_period_sweep": clock_sweep,
        "runs": runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = collect(args.root)
    rendered = json.dumps(result, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"runs={result['run_count']} parsed={result['parsed_run_count']} failed={result['failed_run_count']}")
    print(f"variance period wins: {result['variance_pairwise_register_period_wins']}")
    return 0 if (
        result["run_count"] == 22
        and result["variance_run_count"] == 10
        and result["variance_parsed_run_count"] == 10
        and result["clock_sweep_run_count"] == 12
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
