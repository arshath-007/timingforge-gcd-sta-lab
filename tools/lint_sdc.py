#!/usr/bin/env python3
"""Conservative, interface-aware SDC lint for the TimingForge GCD benchmark.

This is a line-oriented subset parser, not a complete Tcl/SDC interpreter.
It checks the project's canonical interface constraints and fails closed on
ambiguous numeric budgets; it does not prove design intent or signoff quality.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import shlex

INPUTS = ("start", "rst", "a_in", "b_in")
OUTPUTS = ("gcd_out", "busy", "done")
GET_PORTS = re.compile(r"\[\s*get_ports\s+(?:\{([^}]*)\}|([^\]\s]+))\s*\]")
NUMBER = re.compile(r"^[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?$")


def _active_lines(text):
    return [line.strip() for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def _tokens(line):
    try:
        return shlex.split(line, posix=False)
    except ValueError:
        return line.split()


def _port_patterns(line):
    patterns = []
    for match in GET_PORTS.finditer(line):
        patterns.extend((match.group(1) or match.group(2)).split())
    return patterns


def _covers_port(pattern, port):
    return pattern in {port, port + "*", port + "[*]"}


def _numeric_value(line, option=None):
    tokens = _tokens(line)
    if option and option in tokens:
        index = tokens.index(option)
        if index + 1 < len(tokens) and NUMBER.fullmatch(tokens[index + 1]):
            return float(tokens[index + 1])
    # SDC permits the numeric delay/uncertainty value as the first positional
    # argument, before -clock/-max/-min/-setup/-hold.
    command = tokens[0] if tokens else ""
    for token in tokens[1:]:
        if token.startswith("-") or token.startswith("[") or token.endswith("]"):
            continue
        if NUMBER.fullmatch(token):
            return float(token)
    return None


def _clock_reference(line):
    match = re.search(r"-clock\s+\[\s*get_clocks\s+([^\]]+)\]", line)
    if match:
        return match.group(1).strip().split()[0]
    match = re.search(r"-clock\s+(\S+)", line)
    return match.group(1).strip("{}") if match else None


def _effective_delay(lines, command, port, mode, clock_names):
    matches = []
    for line in lines:
        if not line.startswith(command + " "):
            continue
        if not re.search(rf"(?:^|\s)-{mode}(?:\s|$)", line):
            continue
        clock = _clock_reference(line)
        if clock not in clock_names:
            continue
        if any(_covers_port(pattern, port) for pattern in _port_patterns(line)):
            matches.append(_numeric_value(line, f"-{mode}"))
    return matches[-1] if matches else None, len(matches)


def _effective_uncertainty(lines, mode):
    values = []
    for line in lines:
        if not line.startswith("set_clock_uncertainty "):
            continue
        if not re.search(rf"(?:^|\s)-{mode}(?:\s|$)", line):
            continue
        values.append(_numeric_value(line, f"-{mode}"))
    return values[-1] if values else None


def lint_sdc(text):
    lines = _active_lines(text)
    findings = []
    clocks = [line for line in lines if line.startswith("create_clock ")]
    clock_names = {
        match.group(1).strip("{}")
        for line in clocks
        for match in [re.search(r"-name\s+(\S+)", line)]
        if match
    }
    clock_periods = []
    valid_clock = False
    for line in clocks:
        match = re.search(r"-period\s+([-+0-9.eE]+)", line)
        port_ok = any(_covers_port(pattern, "clk") for pattern in _port_patterns(line))
        try:
            period = float(match.group(1)) if match else None
        except ValueError:
            period = None
        if period is not None:
            clock_periods.append(period)
        if period is not None and period > 0 and port_ok:
            valid_clock = True
    period = min(clock_periods) if clock_periods else None
    if not clocks:
        findings.append("TF001 ERROR: no create_clock command found")
    elif not valid_clock:
        findings.append("TF002 ERROR: create_clock must define a positive period on port 'clk'")
    if period is not None and (period < 0.01 or period > 100.0):
        findings.append(f"TF003 ERROR: clock period {period:g} ns is outside the benchmark sanity range 0.01..100 ns")

    for direction, ports, command, missing_rule, nonpositive_rule, range_rule in (
        ("input", INPUTS, "set_input_delay", "TF101", "TF103", "TF104"),
        ("output", OUTPUTS, "set_output_delay", "TF201", "TF203", "TF204"),
    ):
        for port in ports:
            for mode in ("max", "min"):
                value, count = _effective_delay(lines, command, port, mode, clock_names)
                if count == 0 or value is None:
                    findings.append(f"{missing_rule} ERROR: missing {mode} {direction} delay for port '{port}'")
                    continue
                if count > 1:
                    findings.append(f"TF106 REVIEW: multiple {mode} {direction} delay commands cover '{port}'; last command wins")
                if value <= 0:
                    findings.append(f"{nonpositive_rule} ERROR: {mode} {direction} delay for port '{port}' must be positive")
                if period is not None and value >= period:
                    findings.append(f"{range_rule} ERROR: {mode} {direction} delay for port '{port}' must be less than clock period")

    setup_uncertainty = _effective_uncertainty(lines, "setup")
    hold_uncertainty = _effective_uncertainty(lines, "hold")
    if setup_uncertainty is None or setup_uncertainty <= 0:
        findings.append("TF401 ERROR: positive setup clock uncertainty is not defined")
    if hold_uncertainty is None or hold_uncertainty <= 0:
        findings.append("TF402 ERROR: positive hold clock uncertainty is not defined")
    if period is not None:
        if setup_uncertainty is not None and setup_uncertainty >= period:
            findings.append("TF403 ERROR: setup uncertainty must be less than clock period")
        if hold_uncertainty is not None and hold_uncertainty >= period:
            findings.append("TF404 ERROR: hold uncertainty must be less than clock period")

    review_commands = {
        "set_false_path": "TF301 REVIEW: set_false_path requires design-intent review",
        "set_multicycle_path": "TF302 REVIEW: set_multicycle_path requires design-intent review",
        "set_clock_groups": "TF303 REVIEW: set_clock_groups requires design-intent review",
        "set_disable_timing": "TF304 REVIEW: set_disable_timing requires design-intent review",
        "set_case_analysis": "TF305 REVIEW: set_case_analysis requires mode/design-intent review",
        "set_max_delay": "TF306 REVIEW: set_max_delay requires design-intent review",
        "set_min_delay": "TF307 REVIEW: set_min_delay requires design-intent review",
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
