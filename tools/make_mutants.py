#!/usr/bin/env python3
"""Generate named, controlled SDC mutations from the GCD golden baseline."""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "constraints" / "gcd_baseline.sdc"
OUTPUT = ROOT / "build" / "mutants"

MUTATIONS = {
    "M01_missing_clock": {
        "remove_prefix": ["create_clock"],
        "remove_contains": [],
        "append": [],
        "description": "Remove the primary clock definition",
    },
    "M02_missing_input_delay": {
        "remove_prefix": ["set_input_delay"],
        "remove_contains": ["a_in"],
        "append": [],
        "description": "Remove the input arrival budget for a_in",
    },
    "M03_missing_output_delay": {
        "remove_prefix": ["set_output_delay"],
        "remove_contains": ["gcd_out"],
        "append": [],
        "description": "Remove the output required-time budget for gcd_out",
    },
    "M04_unjustified_false_path": {
        "remove_prefix": [],
        "remove_contains": [],
        "append": [
            "# MUTATION ONLY: broad exception for a controlled negative test",
            "set_false_path -from [all_inputs]",
        ],
        "description": "Add a broad false-path exception for review",
    },
}


def mutate(text, spec):
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        remove = any(stripped.startswith(prefix) for prefix in spec["remove_prefix"])
        remove = remove and any(token in stripped for token in spec["remove_contains"]) if spec["remove_contains"] else remove
        if not remove:
            kept.append(line)
    return "\n".join(kept + spec["append"]) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error("Golden SDC not found: " + str(args.source))
    args.out.mkdir(parents=True, exist_ok=True)
    source = args.source.read_text(encoding="utf-8")
    for name, spec in MUTATIONS.items():
        target = args.out / (name + ".sdc")
        target.write_text(mutate(source, spec), encoding="utf-8")
        print(name + ": " + spec["description"] + " -> " + str(target))


if __name__ == "__main__":
    main()
