#!/usr/bin/env python3
"""Conservative quality checks for a parsed TimingForge STA matrix.

These checks flag review conditions; they do not prove SDC correctness or signoff.
Only golden rows are judged against baseline expectations. Deliberate mutation
rows are retained as experiments and are not treated as baseline failures.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def inspect_golden_row(row: dict) -> list[dict]:
    """Return conservative findings for one golden architecture result."""
    findings = []
    top = row.get("top", "unknown")

    def add(severity: str, code: str, message: str) -> None:
        findings.append({
            "top": top,
            "scenario": row.get("scenario", "unknown"),
            "severity": severity,
            "code": code,
            "message": message,
        })

    required = (
        "yosys_cell_area",
        "all_path_min_period_ns",
        "all_path_fmax_mhz",
        "worst_setup_slack_ns",
        "worst_hold_slack_ns",
        "unconstrained_endpoints_reported",
    )
    for field in required:
        if row.get(field) is None:
            add("ERROR", "TFQ001", f"Required golden metric is missing: {field}")

    area = row.get("yosys_cell_area")
    if area is not None and area <= 0:
        add("ERROR", "TFQ002", f"Non-positive synthesis area: {area}")

    period = row.get("all_path_min_period_ns")
    fmax = row.get("all_path_fmax_mhz")
    if period is not None and period <= 0:
        add("ERROR", "TFQ003", f"Non-positive all-path minimum period: {period}")
    if fmax is not None and fmax <= 0:
        add("ERROR", "TFQ004", f"Non-positive all-path Fmax: {fmax}")

    unconstrained = row.get("unconstrained_endpoints_reported")
    if unconstrained is not None and unconstrained > 0:
        add("WARNING", "TFQ101", f"Golden SDC reports {unconstrained} unconstrained endpoints")

    missing_inputs = row.get("missing_input_delay_ports", 0)
    if missing_inputs:
        add("WARNING", "TFQ102", f"Golden SDC reports {missing_inputs} input ports without input delay")

    missing_outputs = row.get("missing_output_delay_ports", 0)
    if missing_outputs:
        add("WARNING", "TFQ103", f"Golden SDC reports {missing_outputs} output ports without output delay")

    hold_slack = row.get("worst_hold_slack_ns")
    if hold_slack is not None and hold_slack < 0:
        add("WARNING", "TFQ104", f"Golden-SDC hold slack is negative ({hold_slack} ns)")

    if row.get("register_to_register_path_found") is False:
        add("WARNING", "TFQ105", "No register-to-register setup path was found under the golden SDC")

    reported = row.get("register_to_register_rising_paths_reported")
    complete = row.get("register_to_register_rising_path_inventory_complete")
    if reported is not None and complete is False:
        add("INFO", "TFQ106", "Rising-edge register-path inventory reached its reporting cap")

    for metric, label in (
        ("max_slew", "maximum transition/slew"),
        ("max_capacitance", "maximum capacitance"),
        ("max_fanout", "maximum fanout"),
    ):
        supported = row.get(f"drv_{metric}_supported")
        violations = row.get(f"drv_{metric}_violation_count")
        if supported is False:
            add("INFO", "TFQ108", f"OpenSTA {label} report is unsupported in this build")
        elif violations is not None and violations > 0:
            add("WARNING", "TFQ110", f"OpenSTA reports {violations} {label} violation records")
        elif violations == 0:
            add("INFO", "TFQ109", f"No {label} violation records were reported; total applicable check count is not enumerated")

    if row.get("register_to_register_min_period_ns") is None:
        add("INFO", "TFQ107", "Native register-only minimum period is unavailable; no derived Fmax is inferred")

    return findings


def inspect_matrix(matrix: dict) -> dict:
    """Inspect golden rows and return machine-readable findings and summary."""
    records = matrix.get("records", [])
    golden = [row for row in records if row.get("scenario") == "gcd_baseline"]
    findings = []
    for row in golden:
        findings.extend(inspect_golden_row(row))

    counts = {
        severity: sum(item["severity"] == severity for item in findings)
        for severity in ("ERROR", "WARNING", "INFO")
    }
    return {
        "schema_version": "1.0",
        "scope": "Golden rows only; mutation rows are intentionally excluded.",
        "findings": findings,
        "counts": counts,
        "status": "REVIEW" if counts["ERROR"] or counts["WARNING"] else "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path, help="Path to sta_matrix_summary.json")
    parser.add_argument("--output", type=Path, help="Optional output JSON path")
    args = parser.parse_args()

    matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
    result = inspect_matrix(matrix)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if result["counts"]["ERROR"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
