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
    return (float(match.group(1)), float(match.group(2))) if match else (None, None)


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


def parse_log(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    top = next((name for name in TOPS if path.stem.startswith("sta_" + name + "_")), None)
    if top is None:
        raise ValueError(f"Unrecognised STA log: {path.name}")
    scenario = path.stem[len("sta_" + top + "_"):]
    setup = section(text, "=== SETUP / MAX PATH DETAILS ===", "=== REGISTER-TO-REGISTER SETUP PATHS ===")
    reg2reg = section(text, "=== REGISTER-TO-REGISTER SETUP PATHS ===", "=== HOLD / MIN PATH DETAILS ===")
    unconstrained = section(text, "=== UNCONSTRAINED PATH DETAILS ===")
    start = re.search(r"^Startpoint:\s*(.+)$", setup, re.MULTILINE)
    end = re.search(r"^Endpoint:\s*(.+)$", setup, re.MULTILINE)
    rr_start = re.search(r"^Startpoint:\s*(.+)$", reg2reg, re.MULTILINE)
    rr_end = re.search(r"^Endpoint:\s*(.+)$", reg2reg, re.MULTILINE)
    warning = re.search(r"There are\s+(\d+)\s+unconstrained endpoints", text, re.IGNORECASE)
    missing_input_warnings = re.findall(r"^Warning:.*(?:no input delay|without input delay|missing input delay).*$", text, re.MULTILINE | re.IGNORECASE)
    missing_output_warnings = re.findall(r"^Warning:.*(?:no output delay|without output delay|missing output delay).*$", text, re.MULTILINE | re.IGNORECASE)
    period, fmax = clock_metrics(text)
    try:
        log_path = str(path.relative_to(ROOT))
    except ValueError:
        log_path = str(path)
    return {
        "top": top, "scenario": scenario, "log_file": log_path,
        "yosys_cell_area": cell_area(top, path),
        "clock_period_min_ns": period, "clock_fmax_mhz": fmax,
        "worst_setup_slack_ns": worst_slack(text, "max"),
        "setup_wns_ns": metric(text, "wns", "max"),
        "setup_tns_ns": metric(text, "tns", "max"),
        "worst_hold_slack_ns": worst_slack(text, "min"),
        "hold_wns_ns": metric(text, "wns", "min"),
        "hold_tns_ns": metric(text, "tns", "min"),
        "worst_setup_startpoint": start.group(1).strip() if start else None,
        "worst_setup_endpoint": end.group(1).strip() if end else None,
        "register_to_register_path_found": bool(rr_start and rr_end),
        "register_to_register_startpoint": rr_start.group(1).strip() if rr_start else None,
        "register_to_register_endpoint": rr_end.group(1).strip() if rr_end else None,
        "unconstrained_endpoints_reported": int(warning.group(1)) if warning else None,
        "missing_input_delay_warnings": missing_input_warnings,
        "missing_output_delay_warnings": missing_output_warnings,
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
        "schema_version": "0.2",
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
        "| Architecture | SDC scenario | Yosys cell area | Min period (ns) | Fmax (MHz) | Worst setup slack (ns) | Setup WNS (ns) | Worst hold slack (ns) | Reg-to-reg path | Missing input-delay warnings | Missing output-delay warnings | Unconstrained endpoints |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    fmt = lambda v: "n/a" if v is None else f"{v:.3f}"
    for row in records:
        rows.append(
            f"| {row['top']} | {row['scenario']} | {fmt(row['yosys_cell_area'])} | "
            f"{fmt(row['clock_period_min_ns'])} | {fmt(row['clock_fmax_mhz'])} | "
            f"{fmt(row['worst_setup_slack_ns'])} | {fmt(row['setup_wns_ns'])} | "
            f"{fmt(row['worst_hold_slack_ns'])} | "
            f"{'found' if row['register_to_register_path_found'] else 'none reported'} | "
            f"{len(row['missing_input_delay_warnings'])} | {len(row['missing_output_delay_warnings'])} | "
            f"{fmt(row['unconstrained_endpoints_reported'])} |"
        )
    rows.extend([
        "",
        "WNS can be zero when slack is positive; the worst-slack column retains the positive timing margin. Missing metrics require raw-log investigation.",
        "Register-to-register paths are reported separately so the false-path mutation is evaluated against the path class it targets. Pre-layout, single typical library, no SPEF; not MMMC or signoff.",
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
    return 0 if result["logs_found"] >= 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
