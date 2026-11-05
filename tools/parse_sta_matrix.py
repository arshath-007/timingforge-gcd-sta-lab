#!/usr/bin/env python3
"""Summarise TimingForge OpenROAD-integrated OpenSTA logs and synthesis area."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "build" / "reports"
TOPS = ("gcd_binary_combined", "gcd_binary_split")
SCENARIOS = (
    "gcd_baseline", "M01_missing_clock", "M02_missing_input_delay",
    "M03_missing_output_delay", "M04_unjustified_false_path",
    "M05_near_match_wrong_port", "M06_missing_hold_uncertainty",
    "M07_nonpositive_clock_period",
)


def metric(text, name, mode):
    pattern = rf"^\s*{name}\s+{mode}\s+([-+]?(?:\d+\.?\d*|\.\d+))\s*$"
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    return float(match.group(1)) if match else None


def worst_slack(text, mode):
    pattern = rf"^\s*worst slack\s+{mode}\s+([-+]?(?:\d+\.?\d*|\.\d+))\s*$"
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    return float(match.group(1)) if match else None


def clock_metrics(text):
    match = re.search(r"^\s*\S+\s+period_min\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+))\s+fmax\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+))", text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return (None, None)
    period = float(match.group(1))
    fmax_text = match.group(2).lower()
    # OpenSTA can return 0.00 / inf when no eligible path exists.
    if period <= 0 or fmax_text in {"inf", "+inf", "infinity", "+infinity"}:
        return (None, None)
    return (period, float(fmax_text))


def section(text, heading, next_heading=None):
    start = text.find(heading)
    if start < 0:
        return ""
    start += len(heading)
    if next_heading is None:
        return text[start:]
    end = text.find(next_heading, start)
    return text[start:end] if end >= 0 else text[start:]


def cell_area(top, report_path):
    candidates = (report_path.parent.parent / f"yosys_{top}.log", ROOT / "build" / f"yosys_{top}.log")
    for candidate in candidates:
        if candidate.is_file():
            data = candidate.read_text(encoding="utf-8", errors="replace")
            matches = re.findall(r"Chip area for module .*?:\s*([-+]?(?:\d+\.?\d*|\.\d+))", data)
            if matches:
                return float(matches[-1])
    return None


def classify_critical_path(startpoint, endpoint):
    """Classify a GCD critical path from explicit port/pin endpoint names.

    Unknown naming is deliberately retained as 'unknown'; this is a heuristic
    for the documented GCD top-level interface, not a general netlist parser.
    """
    if not startpoint or not endpoint:
        return "unknown"

    def is_port(name, port):
        return bool(re.fullmatch(rf"{re.escape(port)}(?:\[[^\]]+\])?", name.strip()))

    start = re.sub(r"\s+\(.*\)$", "", startpoint.strip())
    end = re.sub(r"\s+\(.*\)$", "", endpoint.strip())
    start_input = is_port(start, "a_in") or is_port(start, "b_in") or "input port" in startpoint.lower()
    end_output = is_port(end, "gcd_out") or "output port" in endpoint.lower()
    start_reg = bool(re.search(r"/(?:Q|QN)$", start)) or "flip-flop" in startpoint.lower()
    end_reg = bool(re.search(r"/D$", end)) or "flip-flop" in endpoint.lower()

    if start_input and end_reg:
        return "input_to_register"
    if start_reg and end_reg:
        return "register_to_register"
    if start_reg and end_output:
        return "register_to_output"
    if start_input and end_output:
        return "input_to_output"
    return "unknown"


def parse_log(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    top = next((name for name in TOPS if path.stem.startswith("sta_" + name + "_")), None)
    if top is None:
        raise ValueError(f"Unrecognised STA log: {path.name}")
    scenario = path.stem[len("sta_" + top + "_"):]
    setup = section(text, "=== SETUP / MAX PATH DETAILS ===", "=== REGISTER-TO-REGISTER SETUP PATHS ===")
    if "=== RISING-EDGE REGISTER-TO-REGISTER SETUP PATHS ===" in text:
        reg2reg = section(text, "=== REGISTER-TO-REGISTER SETUP PATHS ===", "=== RISING-EDGE REGISTER-TO-REGISTER SETUP PATHS ===")
    else:
        reg2reg = section(text, "=== REGISTER-TO-REGISTER SETUP PATHS ===", "=== HOLD / MIN PATH DETAILS ===")
    rising_reg2reg = section(text, "=== RISING-EDGE REGISTER-TO-REGISTER SETUP PATHS ===", "=== CLOCK PROPERTIES ===")
    rising_slacks = [
        float(value) for value in re.findall(r"([-+]?(?:\d+\.?\d*|\.\d+))\s+slack\s+\((?:MET|VIOLATED)\)", rising_reg2reg)
    ]
    clock_section = section(text, "=== CLOCK PROPERTIES ===", "=== HOLD / MIN PATH DETAILS ===")
    clock_period_match = re.search(r"^\s*core_clk\s+([-+]?(?:\d+\.?\d*|\.\d+))\s+", clock_section, re.MULTILINE)
    clock_period = float(clock_period_match.group(1)) if clock_period_match else None
    unconstrained = section(text, "=== UNCONSTRAINED PATH DETAILS ===")
    start = re.search(r"^Startpoint:\s*(.+)$", setup, re.MULTILINE)
    end = re.search(r"^Endpoint:\s*(.+)$", setup, re.MULTILINE)
    rr_start = re.search(r"^Startpoint:\s*(.+)$", reg2reg, re.MULTILINE)
    rr_end = re.search(r"^Endpoint:\s*(.+)$", reg2reg, re.MULTILINE)
    warning = re.search(r"There are\s+(\d+)\s+unconstrained endpoints", text, re.IGNORECASE)
    input_missing = re.search(r"There are\s+(\d+)\s+input ports missing set_input_delay", text, re.IGNORECASE)
    output_missing = re.search(r"There are\s+(\d+)\s+output ports missing set_output_delay", text, re.IGNORECASE)
    rr_period, rr_fmax = clock_metrics(section(text, "=== REGISTER-TO-REGISTER CLOCK PERIOD / FREQUENCY ===", "=== ALL-PATH CLOCK PERIOD / FREQUENCY"))
    all_period, all_fmax = clock_metrics(section(text, "=== ALL-PATH CLOCK PERIOD / FREQUENCY (INCLUDING PORT PATHS) ===", "=== SETUP SUMMARY ==="))
    try:
        log_path = str(path.relative_to(ROOT))
    except ValueError:
        log_path = str(path)
    return {
        "top": top, "scenario": scenario, "log_file": log_path,
        "yosys_cell_area": cell_area(top, path),
        "register_to_register_min_period_ns": rr_period,
        "register_to_register_fmax_mhz": rr_fmax,
        "all_path_min_period_ns": all_period, "all_path_fmax_mhz": all_fmax,
        "clock_period_min_ns": all_period, "clock_fmax_mhz": all_fmax,
        "worst_setup_slack_ns": worst_slack(text, "max"),
        "setup_wns_ns": metric(text, "wns", "max"),
        "setup_tns_ns": metric(text, "tns", "max"),
        "worst_hold_slack_ns": worst_slack(text, "min"),
        "hold_wns_ns": metric(text, "wns", "min"),
        "hold_tns_ns": metric(text, "tns", "min"),
        "worst_setup_startpoint": start.group(1).strip() if start else None,
        "worst_setup_endpoint": end.group(1).strip() if end else None,
        "critical_path_class": classify_critical_path(start.group(1).strip() if start else None, end.group(1).strip() if end else None),
        "register_to_register_path_found": bool(rr_start and rr_end),
        "register_to_register_rising_paths_reported": len(rising_slacks),
        "register_to_register_rising_path_inventory_complete": len(rising_slacks) < 1000,
        "register_to_register_rising_worst_slack_ns": min(rising_slacks) if rising_slacks else None,
        "register_to_register_rising_best_slack_ns": max(rising_slacks) if rising_slacks else None,
        "clock_period_ns": clock_period,
        "register_to_register_startpoint": rr_start.group(1).strip() if rr_start else None,
        "register_to_register_endpoint": rr_end.group(1).strip() if rr_end else None,
        "unconstrained_endpoints_reported": int(warning.group(1)) if warning else (0 if "=== TIMINGFORGE SETUP CHECK ===" in text else None),
        "missing_input_delay_ports": int(input_missing.group(1)) if input_missing else 0,
        "missing_output_delay_ports": int(output_missing.group(1)) if output_missing else 0,
        "unconstrained_paths_listed": len(re.findall(r"^Startpoint:", unconstrained, re.MULTILINE)),
    }


def summarise(report_dir=REPORT_DIR):
    report_dir = Path(report_dir)
    records = [parse_log(p) for p in sorted(report_dir.glob("sta_*.log"))]
    records.sort(key=lambda row: (row["top"], row["scenario"]))
    baselines = {row["top"]: row for row in records if row["scenario"] == "gcd_baseline"}
    for row in records:
        base = baselines.get(row["top"])
        row["worst_setup_slack_delta_vs_golden_ns"] = (
            round(row["worst_setup_slack_ns"] - base["worst_setup_slack_ns"], 6)
            if base and row["worst_setup_slack_ns"] is not None and base["worst_setup_slack_ns"] is not None else None
        )
    output = {
        "schema_version": "0.3",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "analysis_engine": "OpenROAD-integrated OpenSTA",
        "platform": "Nangate45 typical Liberty",
        "parasitics": "No SPEF; pre-layout/cell-based; no extracted interconnect parasitics.",
        "logs_found": len(records), "records": records,
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "sta_matrix_summary.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# TimingForge library-backed STA matrix", "",
        "- Generated UTC: " + output["generated_at_utc"],
        "- Engine: " + output["analysis_engine"],
        "- Library: " + output["platform"],
        "- Parasitics: " + output["parasitics"],
        "- Logs parsed: " + str(len(records)), "",
        "| Architecture | SDC scenario | Cell area | Native reg-to-reg period (ns) | Native reg-to-reg Fmax (MHz) | Rising-edge reg-to-reg paths reported | Worst slack in explicit reg-to-reg report (ns) | All-path min period (ns) | All-path Fmax (MHz) | Critical path class | Worst setup slack (ns) | Worst hold slack (ns) | Reg-to-reg path | Unconstrained endpoints |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    fmt = lambda value: "n/a" if value is None else f"{value:.3f}"
    for row in records:
        rows.append(
            f"| {row['top']} | {row['scenario']} | {fmt(row['yosys_cell_area'])} | "
            f"{fmt(row['register_to_register_min_period_ns'])} | {fmt(row['register_to_register_fmax_mhz'])} | "
            f"{row['register_to_register_rising_paths_reported']} | {fmt(row['register_to_register_rising_worst_slack_ns'])} | "
            f"{fmt(row['all_path_min_period_ns'])} | {fmt(row['all_path_fmax_mhz'])} | "
            f"{row['critical_path_class']} | {fmt(row['worst_setup_slack_ns'])} | {fmt(row['worst_hold_slack_ns'])} | "
            f"{'found' if row['register_to_register_path_found'] else 'none reported'} | "
            f"{fmt(row['unconstrained_endpoints_reported'])} |"
        )
    rows.extend([
        "",
        "The native register-to-register clock-period command is reported separately from the explicit same-clock rising-edge path inventory. Do not derive an internal Fmax from the path-report slack unless its relationship to the native command has been validated for the tool and design. The explicit inventory is capped at 1000 paths per group; a count below the cap indicates the report did not hit that limit. All-path period includes port paths. Neither metric is post-route or signoff timing.",
        "WNS may be zero when slack is positive; worst slack retains the margin. Missing metrics require raw-log investigation.",
        "",
    ])
    (report_dir / "sta_matrix_summary.md").write_text("\n".join(rows), encoding="utf-8")
    print("Parsed STA logs: " + str(len(records)))
    print("Summary: " + str(report_dir / "sta_matrix_summary.md"))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    result = summarise(args.reports)
    observed = {(row["top"], row["scenario"]) for row in result["records"]}
    expected = {(top, scenario) for top in TOPS for scenario in SCENARIOS}
    missing = sorted(expected - observed)
    unexpected = sorted(observed - expected)
    if missing or unexpected or result["logs_found"] != 16:
        print("ERROR: expected exactly 16 STA logs (2 architectures x 8 scenarios)")
        if missing:
            print("Missing matrix entries: " + repr(missing))
        if unexpected:
            print("Unexpected matrix entries: " + repr(unexpected))
        return 1

    # Golden rows are the reference measurements. Missing values must fail loudly,
    # not silently become "n/a" in a supposedly complete benchmark.
    required_golden = (
        "yosys_cell_area",
        "all_path_min_period_ns",
        "all_path_fmax_mhz",
        "worst_setup_slack_ns",
        "worst_hold_slack_ns",
        "unconstrained_endpoints_reported",
    )
    failures = []
    for row in result["records"]:
        if row["scenario"] != "gcd_baseline":
            continue
        for field in required_golden:
            if row[field] is None:
                failures.append(f"{row['top']} golden metric missing: {field}")
    if failures:
        print("ERROR: incomplete golden STA evidence")
        for failure in failures:
            print(failure)
        return 1

    print("Validated complete STA matrix: 16/16 architecture/scenario combinations")
    print("Validated required golden metrics for both architectures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
