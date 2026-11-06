"""Fail-closed, same-environment QoR regression gate."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

TOPS = {"gcd_binary_combined", "gcd_binary_split"}
SUPPORTED_METRICS = {
    "cell_area", "all_path_min_period_ns",
    "worst_setup_slack_ns", "worst_hold_slack_ns",
}


def _finite(value, label):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"missing or non-finite required metric: {label}")
    return float(value)


def _baseline_rows(snapshot: dict, label: str) -> dict:
    rows = {}
    for row in snapshot.get("records", []):
        if row.get("scenario") != "gcd_baseline":
            continue
        key = (row.get("top"), row.get("scenario"))
        if key in rows:
            raise ValueError(f"duplicate {label} golden record: {'/'.join(str(x) for x in key)}")
        rows[key] = row
    actual_tops = {top for top, _scenario in rows}
    if actual_tops != TOPS:
        missing = sorted(TOPS - actual_tops)
        unexpected = sorted(actual_tops - TOPS)
        raise ValueError(f"{label} architecture set mismatch: missing={missing}, unexpected={unexpected}")
    return rows


def evaluate(reference: dict, candidate: dict, policy: dict) -> dict:
    environment_fields = (
        "platform", "platform_source_revision", "corner",
        "liberty_sha256", "tool_versions",
    )
    for field in environment_fields:
        if reference.get(field) != candidate.get(field):
            raise ValueError(f"QoR environment mismatch: {field}")

    ref_rows = _baseline_rows(reference, "baseline")
    new_rows = _baseline_rows(candidate, "candidate")

    limits = policy["limits"]
    required = policy["required_metrics"]
    if not required or set(required) - SUPPORTED_METRICS:
        raise ValueError(f"unsupported or empty QoR required_metrics: {required}")
    for name, value in limits.items():
        numeric = _finite(value, f"policy limit {name}")
        if numeric < 0:
            raise ValueError(f"policy limit must be non-negative: {name}")

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
                if before <= 0 or after <= 0:
                    raise ValueError(f"baseline and candidate {metric} must be positive")
                delta = (after / before - 1.0) * 100.0
                limit_keys = {
                    "cell_area": "cell_area_growth_percent",
                    "all_path_min_period_ns": "all_path_min_period_growth_percent",
                }
                limit = _finite(limits[limit_keys[metric]], f"policy {limit_keys[metric]}")
                passed = delta <= limit
                check = {
                    "top": key[0], "metric": metric, "baseline": before,
                    "candidate": after, "change_percent": round(delta, 4),
                    "maximum_growth_percent": limit, "passed": passed,
                }
            else:
                delta = before - after
                limit_key = "worst_setup_slack_drop_ns" if metric == "worst_setup_slack_ns" else "worst_hold_slack_drop_ns"
                limit = _finite(limits[limit_key], f"policy {limit_key}")
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
