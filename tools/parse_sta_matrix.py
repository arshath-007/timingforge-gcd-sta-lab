#!/usr/bin/env python3
"""Summarise TimingForge OpenSTA/OpenROAD-integrated timing logs."""
from pathlib import Path
import json
import re
import argparse
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "build" / "reports"
TOPS = ("gcd_binary_combined", "gcd_binary_split")


def _metric(text, name, mode):
    pattern = rf"^\s*{name}\s+{mode}\s+([-+]?(?:\d+\.?\d*|\.\d+))\s*$"
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    return float(match.group(1)) if match else None


def _section(text, heading, next_heading=None):
    start = text.find(heading)
    if start < 0:
        return ""
    start += len(heading)
    if next_heading:
        end = text.find(next_heading, start)
        return text[start:end] if end >= 0 else text[start:]
    return text[start:]


def parse_log(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    stem = path.stem
    top = None
    scenario = None
    for candidate in TOPS:
        prefix = "sta_" + candidate + "_"
        if stem.startswith(prefix):
            top = candidate
            scenario = stem[len(prefix):]
            break
    if top is None:
        raise ValueError(f"Unrecognised STA log filename: {path.name}")

    setup_section = _section(text, "=== SETUP / MAX PATH DETAILS ===", "=== HOLD / MIN PATH DETAILS ===")
    unconstrained_section = _section(text, "=== UNCONSTRAINED PATH DETAILS ===")
    setup_start = re.search(r"^Startpoint:\s*(.+)$", setup_section, re.MULTILINE)
    setup_end = re.search(r"^Endpoint:\s*(.+)$", setup_section, re.MULTILINE)
    unconstrained_count = len(re.findall(r"^Startpoint:", unconstrained_section, re.MULTILINE))
    return {
        "top": top,
        "scenario": scenario,
        "log_file": str(path.relative_to(ROOT)),
        "setup_wns": _metric(text, "wns", "max"),
        "setup_tns": _metric(text, "tns", "max"),
        "hold_wns": _metric(text, "wns", "min"),
        "hold_tns": _metric(text, "tns", "min"),
        "worst_setup_startpoint": setup_start.group(1).strip() if setup_start else None,
        "worst_setup_endpoint": setup_end.group(1).strip() if setup_end else None,
        "unconstrained_path_count_reported": unconstrained_count,
        "timing_report_present": setup_start is not None,
    }


def summarise(report_dir=REPORT_DIR):
    paths = sorted(Path(report_dir).glob("sta_*.log"))
    records = [parse_log(path) for path in paths]
    records.sort(key=lambda row: (row["top"], row["scenario"]))
    by_key = {(row["top"], row["scenario"]): row for row in records}

    for row in records:
        baseline = by_key.get((row["top"], "gcd_baseline"))
        row["setup_wns_delta_vs_golden"] = (
            round(row["setup_wns"] - baseline["setup_wns"], 6)
            if baseline and row["setup_wns"] is not None and baseline["setup_wns"] is not None
            else None
        )

    output = {
        "schema_version": "0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "analysis_engine": "OpenROAD-integrated OpenSTA (or standalone OpenSTA when configured)",
        "platform": "Nangate45 typical Liberty",
        "parasitics": "No SPEF supplied; report is pre-layout/cell-based and does not include extracted interconnect parasitics.",
        "logs_found": len(records),
        "records": records,
    }

    out = Path(report_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "sta_matrix_summary.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    rows = [
        "# TimingForge library-backed STA matrix",
        "",
        "- Generated UTC: " + output["generated_at_utc"],
        "- Engine: " + output["analysis_engine"],
        "- Library: " + output["platform"],
        "- Parasitics: " + output["parasitics"],
        "- Log files parsed: " + str(len(records)),
        "",
        "| RTL architecture | SDC scenario | Setup WNS | Setup TNS | Hold WNS | Hold TNS | Setup WNS Δ vs golden | Unconstrained paths reported |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    fmt = lambda value: "n/a" if value is None else f"{value:.3f}"
    for row in records:
        rows.append(
            f"| {row['top']} | {row['scenario']} | {fmt(row['setup_wns'])} | {fmt(row['setup_tns'])} | "
            f"{fmt(row['hold_wns'])} | {fmt(row['hold_tns'])} | {fmt(row['setup_wns_delta_vs_golden'])} | "
            f"{row['unconstrained_path_count_reported']} |"
        )
    rows.extend([
        "",
        "A missing metric is shown as n/a and must be investigated in its raw log. A zero WNS means no negative slack was reported; it does not mean every constraint is correct.",
        "The experiment is pre-layout and uses a single typical Liberty file. It is not MMMC, extracted-parasitic analysis, or production signoff.",
        "",
    ])
    (out / "sta_matrix_summary.md").write_text("\n".join(rows), encoding="utf-8")
    print("Parsed STA logs: " + str(len(records)))
    print("Summary: " + str(out / "sta_matrix_summary.md"))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    result = summarise(args.reports)
    return 0 if result["logs_found"] >= 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
