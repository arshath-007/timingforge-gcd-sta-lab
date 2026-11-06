#!/usr/bin/env python3
"""Compare expected SDC mutation effects with observed STA evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

M06_EXPECTED_HOLD_DELTA_NS = 0.050
M06_TOLERANCE_NS = 0.001

EXPECTED = {
    "M01_missing_clock": "A well-formed clock-properties section is present and contains no usable core_clk period.",
    "M02_missing_input_delay": "At least one input port should be reported without input delay.",
    "M03_missing_output_delay": "At least one output port should be reported without output delay.",
    "M04_unjustified_false_path": "The dedicated register-to-register path report should contain no path.",
    "M05_near_match_wrong_port": "At least one input port should be reported without input delay.",
    "M06_missing_hold_uncertainty": "Worst hold slack should improve by the removed 0.050 ns hold uncertainty.",
    "M07_nonpositive_clock_period": "The reported primary-clock period should be non-positive.",
}


def assess(row: dict, baseline: dict | None = None) -> dict:
    scenario = row.get("scenario", "")
    if scenario == "M01_missing_clock":
        period = row.get("clock_period_ns")
        report_valid = (
            row.get("clock_properties_section_present") is True
            and row.get("clock_properties_section_valid") is True
        )
        observed = report_valid and period is None
        evidence = {
            "clock_period_ns": period,
            "clock_properties_section_present": row.get("clock_properties_section_present"),
            "clock_properties_section_valid": row.get("clock_properties_section_valid"),
            "unconstrained_endpoints_reported": row.get("unconstrained_endpoints_reported"),
        }
    elif scenario in {"M02_missing_input_delay", "M05_near_match_wrong_port"}:
        observed = (row.get("missing_input_delay_ports") or 0) > 0
        evidence = {"missing_input_delay_ports": row.get("missing_input_delay_ports")}
    elif scenario == "M03_missing_output_delay":
        observed = (row.get("missing_output_delay_ports") or 0) > 0
        evidence = {"missing_output_delay_ports": row.get("missing_output_delay_ports")}
    elif scenario == "M04_unjustified_false_path":
        observed = row.get("register_to_register_path_found") is False
        evidence = {"register_to_register_path_found": row.get("register_to_register_path_found")}
    elif scenario == "M06_missing_hold_uncertainty":
        if baseline is None or row.get("worst_hold_slack_ns") is None or baseline.get("worst_hold_slack_ns") is None:
            return {
                "scenario": scenario,
                "status": "inconclusive",
                "expected": EXPECTED[scenario],
                "observed": "A matching golden baseline and both hold-slack values are required.",
                "evidence": {"mutant_hold_slack_ns": row.get("worst_hold_slack_ns"),
                             "baseline_hold_slack_ns": baseline.get("worst_hold_slack_ns") if baseline else None},
            }
        delta = row["worst_hold_slack_ns"] - baseline["worst_hold_slack_ns"]
        observed = abs(delta - M06_EXPECTED_HOLD_DELTA_NS) <= M06_TOLERANCE_NS
        evidence = {
            "baseline_hold_slack_ns": baseline["worst_hold_slack_ns"],
            "mutant_hold_slack_ns": row["worst_hold_slack_ns"],
            "hold_slack_delta_ns": round(delta, 6),
            "expected_delta_ns": M06_EXPECTED_HOLD_DELTA_NS,
            "tolerance_ns": M06_TOLERANCE_NS,
        }
    elif scenario == "M07_nonpositive_clock_period":
        period = row.get("clock_period_ns")
        observed = period is not None and period <= 0
        evidence = {"clock_period_ns": period, "all_path_min_period_ns": row.get("all_path_min_period_ns")}
    else:
        return {"scenario": scenario, "status": "not_applicable", "expected": None,
                "observed": "No expectation defined.", "evidence": {}}
    return {"scenario": scenario, "status": "matched" if observed else "mismatched",
            "expected": EXPECTED[scenario],
            "observed": "Expected signal observed." if observed else "Expected signal not observed.",
            "evidence": evidence}


def inspect_matrix(matrix: dict) -> dict:
    records = matrix.get("records", [])
    baselines = {row.get("top"): row for row in records if row.get("scenario") == "gcd_baseline"}
    results = [
        assess(row, baselines.get(row.get("top")))
        for row in records if row.get("scenario") != "gcd_baseline"
    ]
    counts = {status: sum(item["status"] == status for item in results)
              for status in ("matched", "mismatched", "inconclusive", "not_applicable")}
    return {
        "schema_version": "1.1",
        "method": "Per-mutation expected-versus-observed evidence; no aggregate accuracy score.",
        "m06_expected_hold_delta_ns": M06_EXPECTED_HOLD_DELTA_NS,
        "m06_tolerance_ns": M06_TOLERANCE_NS,
        "results": results,
        "counts": counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = inspect_matrix(json.loads(args.matrix.read_text(encoding="utf-8")))
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if result["counts"]["mismatched"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
