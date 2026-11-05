#!/usr/bin/env python3
"""Conservative pattern-based SDC lint for the GCD benchmark interface.

This is NOT a full SDC parser and does not prove constraint correctness.
"""
import argparse
from pathlib import Path
import re

INPUTS = ("start", "rst", "a_in", "b_in")
OUTPUTS = ("gcd_out", "busy", "done")


def lint_sdc(text):
    lines = [line.strip() for line in text.splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    joined = "\\n".join(lines)
    findings = []

    if not re.search(r"^create_clock\\b", joined, re.MULTILINE):
        findings.append("TF001 ERROR: no create_clock command found")

    for port in INPUTS:
        pattern = rf"^set_input_delay\\b.*\\[get_ports\\s+\\{{?{re.escape(port)}(?:\\*|\\}})?"
        if not re.search(pattern, joined, re.MULTILINE):
            findings.append("TF101 ERROR: no input delay pattern for " + port)

    for port in OUTPUTS:
        pattern = rf"^set_output_delay\\b.*\\[get_ports\\s+\\{{?{re.escape(port)}(?:\\*|\\}})?"
        if not re.search(pattern, joined, re.MULTILINE):
            findings.append("TF201 ERROR: no output delay pattern for " + port)

    if re.search(r"^set_false_path\\b", joined, re.MULTILINE):
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
