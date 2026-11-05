"""Fail-closed, same-environment QoR regression gate."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def _finite(value, label):
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"missing or non-finite required metric: {label}")
    return float(value)


def evaluate(reference: dict, candidate: dict, policy: dict) -> dict:
    environment_fields = (
        "platform", "platform_source_revision", "corner",
        "liberty_sha256", "tool_versions",
    )
    for field in environment_fields:
        if reference.get(field) != candidate.get(field):
            raise ValueError(f"QoR environment mismatch: {field}")
    ref_rows = {
        (row.get("top"), row.get("scenario")): row
        for row in reference.get("records", [])
        if row.get("scenario") == "gcd_baseline"
    }
    new_rows = {
        (row.get("top"), row.get("scenario")): row
        for row in candidate.get("records", [])
        if row.get("scenario") == "gcd_baseline"
    }
    if not ref_rows or set(ref_rows) != set(new_rows):
        raise ValueError("baseline architecture set differs or is empty")

    limits = policy["limits"]
    required = policy["required_metrics"]
    checks = []
    failures = []
    for key in sorted(ref_rows):
        old, new = ref_rows[key], new_rows[key]
        if old.get("sdc_sha256") != new.get("sdc_sha256"):
            raise ValueError("golden SDC hash mismatch for " + "/".join(key))
        for metric in required:
            before = _finite(old.get(metric), f"baseline {key} {metric}")
            after = _finite(new.get(metric), f"candidate {key} {metric}")
            if metric in ("cell_area", "all_path_min_period_ns"):
                if before <= 0:
                    raise ValueError(f"baseline {metric} must be positive")
                delta = (after / before - 1.0) * 100.0
                limit_key = "cell_area_growth_percent" if metric == "cell_area" else "all_path_min_period_growth_percent"
                limit = float(limits[limit_key])
                passed = delta <= limit
                check = {
                    "top": key[0], "metric": metric, "baseline": before,
                    "candidate": after, "change_percent": round(delta, 4),
                    "maximum_growth_percent": limit, "passed": passed,
                }
            else:
                delta = before - after
                limit = float(limits[metric + "_drop_ns"])
                passed = delta <= limit
                check = {
                    "top": key[0], "metric": metric, "baseline": before,
                    "candidate": after, "drop_ns": round(delta, 6),
                    "maximum_drop_ns": limit, "passed": passed,
                }
            checks.append(check)
            if not passed:
                failures.append(check)
    return {
        "schema_version": "1.0",
        "baseline_source_sha": reference.get("source_sha"),
        "candidate_source_sha": candidate.get("source_sha"),
        "environment_match": True,
        "passed": not failures,
        "checks": checks,
        "failures": failures,
        "interpretation": (
            "Same-platform, same-corner, same-tool and same-SDC regression gate; "
            "not a signoff or cross-library comparison."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(
        json.loads(args.baseline.read_text(encoding="utf-8")),
        json.loads(args.candidate.read_text(encoding="utf-8")),
        json.loads(args.policy.read_text(encoding="utf-8")),
    )
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
