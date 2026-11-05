#!/usr/bin/env python3
"""Run the static SDC fault-injection benchmark and write JSON/Markdown reports."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import platform

from tools.lint_sdc import lint_sdc
from tools.make_mutants import MUTATIONS, mutate

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "constraints" / "gcd_baseline.sdc"
OUTPUT = ROOT / "build"

EXPECTED_FINDINGS = {
    "M01_missing_clock": "TF001 ERROR",
    "M02_missing_input_delay": "TF101 ERROR",
    "M03_missing_output_delay": "TF201 ERROR",
    "M04_unjustified_false_path": "TF301 REVIEW",
    "M05_near_match_wrong_port": "TF101 ERROR",
    "M06_missing_hold_uncertainty": "TF402 ERROR",
    "M07_nonpositive_clock_period": "TF002 ERROR",
}


def has_code(findings, code):
    return any(item.startswith(code) for item in findings)


def run_benchmark(source=SOURCE, output=OUTPUT):
    source = Path(source)
    output = Path(output)
    golden = source.read_text(encoding="utf-8")
    golden_findings = lint_sdc(golden)
    scenarios = [
        {
            "id": "GOLDEN",
            "description": "Golden reference SDC; timing results and any violations are documented separately",
            "expected_finding": "TF000 PASS",
            "findings": golden_findings,
            "detected": has_code(golden_findings, "TF000 PASS"),
        }
    ]

    for name, spec in MUTATIONS.items():
        findings = lint_sdc(mutate(golden, spec))
        code = EXPECTED_FINDINGS[name]
        scenarios.append({
            "id": name,
            "description": spec["description"],
            "expected_finding": code,
            "findings": findings,
            "detected": has_code(findings, code),
        })

    fault_cases = scenarios[1:]
    detected = sum(1 for item in fault_cases if item["detected"])
    report = {
        "schema_version": "0.2",
        "benchmark": "TimingForge static SDC fault-injection benchmark",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python_version": platform.python_version(),
        "source_file": str(source.relative_to(ROOT) if source.is_relative_to(ROOT) else source),
        "source_sha256": hashlib.sha256(golden.encode("utf-8")).hexdigest(),
        "scope": "Static pattern/coverage checks only. No synthesis or STA engine was run by this benchmark command.",
        "golden_baseline_passed": scenarios[0]["detected"],
        "fault_cases": len(fault_cases),
        "faults_detected": detected,
        "detection_rate": detected / len(fault_cases) if fault_cases else 0.0,
        "scenarios": scenarios,
    }

    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "benchmark_report.json"
    markdown_path = output / "benchmark_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    rows = [
        "# TimingForge benchmark report",
        "",
        "- Generated UTC: " + report["generated_at_utc"],
        "- Golden baseline passed: " + str(report["golden_baseline_passed"]),
        "- Controlled fault patterns detected: " + str(detected) + "/" + str(len(fault_cases)),
        "- Detection rate: " + format(report["detection_rate"] * 100, ".1f") + "%",
        "- Scope: " + report["scope"],
        "",
        "| Scenario | Expected finding | Detected | Observed findings |",
        "|---|---|---:|---|",
    ]
    for item in scenarios:
        rows.append("| " + item["id"] + " | " + item["expected_finding"] + " | " +
                    ("yes" if item["detected"] else "NO") + " | " +
                    "; ".join(item["findings"]) + " |")
    rows.extend([
        "",
        "This score measures only the controlled patterns implemented in this prototype. It is not a measure of general SDC correctness, does not prove that a timing exception is invalid, and is not STA signoff.",
        "",
    ])
    markdown_path.write_text("\n".join(rows), encoding="utf-8")
    print("Golden baseline passed: " + str(report["golden_baseline_passed"]))
    print("Controlled static fault patterns detected: " + str(detected) + "/" + str(len(fault_cases)))
    print("JSON report: " + str(json_path))
    print("Markdown report: " + str(markdown_path))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=OUTPUT)
    args = parser.parse_args()
    report = run_benchmark(args.source, args.out)
    return 0 if report["golden_baseline_passed"] and report["faults_detected"] == report["fault_cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
