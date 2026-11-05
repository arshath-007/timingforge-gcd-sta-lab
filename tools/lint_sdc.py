#!/usr/bin/env python3
"""Conservative, interface-aware SDC coverage lint for the GCD benchmark.

This is a small first-pass checker, NOT a complete Tcl/SDC parser and not a
proof that constraints are semantically correct or suitable for signoff.
"""
import argparse
from pathlib import Path
import re

INPUTS = ("start", "rst", "a_in", "b_in")
OUTPUTS = ("gcd_out", "busy", "done")
GET_PORTS = re.compile(r"\[\s*get_ports\s+(?:\{([^}]*)\}|([^\]\s]+))\s*\]")


def _active_lines(text):
    """Return non-empty, non-comment SDC lines (one command per line in v0.1)."""
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _port_patterns(line):
    """Extract simple get_ports patterns; deliberately avoid substring matching."""
    patterns = []
    for match in GET_PORTS.finditer(line):
        # Tcl brace collections can contain multiple whitespace-separated patterns.
        patterns.extend((match.group(1) or match.group(2)).split())
    return patterns


def _covers_port(pattern, port):
    """Accept an exact scalar name or an explicit whole-bus wildcard."""
    return pattern in {port, port + "*", port + "[*]"}


def _has_delay(lines, command, port, mode, clock_names):
    for line in lines:
        if not line.startswith(command + " "):
            continue
        clock = re.search(r"-clock\s+(\S+)", line)
        if not clock or clock.group(1) not in clock_names:
            continue
        if not re.search(rf"-{mode}\s+[-+0-9.eE]+", line):
            continue
        if any(_covers_port(pattern, port) for pattern in _port_patterns(line)):
            return True
    return False


def lint_sdc(text):
    lines = _active_lines(text)
    findings = []

    clocks = [line for line in lines if line.startswith("create_clock ")]
    valid_clock = False
    for line in clocks:
        period = re.search(r"-period\s+([-+0-9.eE]+)", line)
        clock_port = any(_covers_port(pattern, "clk") for pattern in _port_patterns(line))
        try:
            positive_period = period is not None and float(period.group(1)) > 0
        except ValueError:
            positive_period = False
        if positive_period and clock_port:
            valid_clock = True
            break

    clock_names = {
        match.group(1)
        for line in clocks
        for match in [re.search(r"-name\s+(\S+)", line)]
        if match
    }

    if not clocks:
        findings.append("TF001 ERROR: no create_clock command found")
    elif not valid_clock:
        findings.append("TF002 ERROR: create_clock must define a positive period on port 'clk'")

    for port in INPUTS:
        for mode in ("max", "min"):
            if not _has_delay(lines, "set_input_delay", port, mode, clock_names):
                findings.append(f"TF101 ERROR: missing {mode} input delay for port '{port}'")

    for port in OUTPUTS:
        for mode in ("max", "min"):
            if not _has_delay(lines, "set_output_delay", port, mode, clock_names):
                findings.append(f"TF201 ERROR: missing {mode} output delay for port '{port}'")

    def has_positive_uncertainty(mode):
        for line in lines:
            if not line.startswith("set_clock_uncertainty "):
                continue
            option = re.search(rf"-{mode}\s+([-+0-9.eE]+)", line)
            if not option:
                continue
            try:
                if float(option.group(1)) > 0:
                    return True
            except ValueError:
                pass
        return False

    if not has_positive_uncertainty("setup"):
        findings.append("TF401 ERROR: positive setup clock uncertainty is not defined")
    if not has_positive_uncertainty("hold"):
        findings.append("TF402 ERROR: positive hold clock uncertainty is not defined")

    review_commands = {
        "set_false_path": "TF301 REVIEW: set_false_path requires design-intent review",
        "set_multicycle_path": "TF302 REVIEW: set_multicycle_path requires design-intent review",
        "set_clock_groups": "TF303 REVIEW: set_clock_groups requires design-intent review",
        "set_disable_timing": "TF304 REVIEW: set_disable_timing requires design-intent review",
        "set_case_analysis": "TF305 REVIEW: set_case_analysis requires mode/design-intent review",
    }
    for command, finding in review_commands.items():
        if any(line.startswith(command + " ") for line in lines):
            findings.append(finding)
    if not findings:
        findings.append("TF000 PASS: expected clock, uncertainty, and GCD I/O delay patterns found; this is not proof of correctness")
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
