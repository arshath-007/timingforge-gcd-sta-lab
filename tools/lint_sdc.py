#!/usr/bin/env python3
"""Conservative pattern-based SDC lint for the GCD benchmark interface.

This is NOT a full SDC parser and does not prove constraint correctness.
"""
import argparse
from pathlib import Path

INPUTS = ("start", "rst", "a_in", "b_in")
OUTPUTS = ("gcd_out", "busy", "done")


def lint_sdc(text):
    lines = [line.strip() for line in text.splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    findings = []

    if not any(line.startswith("create_clock ") for line in lines):
        findings.append("TF001 ERROR: no create_clock command found")

    for port in INPUTS:
        covered = any(line.startswith("set_input_delay ") and port in line for line in lines)
        if not covered:
            findings.append("TF101 ERROR: no input delay pattern for " + port)

    for port in OUTPUTS:
        covered = any(line.startswith("set_output_delay ") and port in line for line in lines)
        if not covered:
            findings.append("TF201 ERROR: no output delay pattern for " + port)

    if any(line.startswith("set_false_path ") for line in lines):
        findings.append("TF301 REVIEW: set_false_path requires design-intent review")

    if not findings:
        findings.append("TF000 PASS: expected text patterns found; this is not proof of correctness")
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sdc", type=Path)
    args = parser.parse_args()
    if not args.sdc.is_file():
        parser.error("SDC file not found: " + str(args.sdc))
    findings = lint_sdc(args.sdc.read_text(encoding="utf-8"))
    for item in findings:
        print(item)
    return 1 if any("ERROR" in item for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
