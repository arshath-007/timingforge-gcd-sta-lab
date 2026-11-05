#!/usr/bin/env python3
"""Compare expected SDC mutation effects with observed STA evidence."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

EXPECTED = {
    "M01_missing_clock": "Primary clock properties should be absent or invalid.",
    "M02_missing_input_delay": "At least one input port should be reported without input delay.",
    "M03_missing_output_delay": "At least one output port should be reported without output delay.",
    "M04_unjustified_false_path": "The dedicated register-to-register path report should contain no path.",
    "M05_near_match_wrong_port": "At least one input port should be reported without input delay.",
    "M06_missing_hold_uncertainty": "Hold-uncertainty semantics are not reliably exposed by the current parsed report.",
    "M07_nonpositive_clock_period": "The reported primary-clock period should be non-positive.",
}

def assess(row: dict) -> dict:
    scenario = row.get("scenario", "")
    if scenario == "M01_missing_clock":
        period = row.get("clock_period_ns")
        observed = period is None or period <= 0
        evidence = {"clock_period_ns": period, "unconstrained_endpoints_reported": row.get("unconstrained_endpoints_reported")}
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
        return {"scenario": scenario, "status": "inconclusive", "expected": EXPECTED[scenario],
                "observed": "No independently validated parsed metric identifies hold uncertainty presence.",
                "evidence": {"worst_hold_slack_ns": row.get("worst_hold_slack_ns")}}
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
    results = [assess(row) for row in matrix.get("records", []) if row.get("scenario") != "gcd_baseline"]
    counts = {status: sum(item["status"] == status for item in results)
              for status in ("matched", "mismatched", "inconclusive", "not_applicable")}
    return {"schema_version": "1.0",
            "method": "Per-mutation expected-versus-observed evidence; no aggregate accuracy score.",
            "results": results, "counts": counts}

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
