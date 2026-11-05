"""Parse post-route OpenSTA logs and compare against matched pre-layout results."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

TOPS = ("gcd_binary_combined", "gcd_binary_split")


def _number(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return float(match.group(1)) if match else None


def parse_postroute_log(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    if "POST-ROUTE PARASITICS LOADED" not in text:
        raise ValueError(f"{path}: extracted parasitics marker missing")
    if "SPEF=" not in text:
        raise ValueError(f"{path}: SPEF path not recorded")
    clock = text.split("=== POST-ROUTE ALL-PATH CLOCK PERIOD ===", 1)
    if len(clock) != 2:
        raise ValueError(f"{path}: post-route clock-period section missing")
    clock_text = clock[1].split("=== POST-ROUTE SETUP SUMMARY ===", 1)[0]
    period = _number(r"^\s*\S+\s+period_min\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+))", clock_text)
    fmax = _number(r"^\s*\S+\s+period_min\s*=\s*[-+]?(?:\d+\.?\d*|\.\d+)\s+fmax\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+))", clock_text)
    setup = _number(r"^\s*worst slack\s+max\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    hold = _number(r"^\s*worst slack\s+min\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    setup_wns = _number(r"^\s*wns\s+max\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    setup_tns = _number(r"^\s*tns\s+max\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    hold_wns = _number(r"^\s*wns\s+min\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    hold_tns = _number(r"^\s*tns\s+min\s+([-+]?(?:\d+\.?\d*|\.\d+))", text)
    skew_setup = text.split("=== POST-ROUTE SETUP CLOCK SKEW ===", 1)
    skew_hold = text.split("=== POST-ROUTE HOLD CLOCK SKEW ===", 1)
    setup_skew_text = skew_setup[1].split("=== POST-ROUTE HOLD CLOCK SKEW ===", 1)[0] if len(skew_setup) > 1 else ""
    hold_skew_text = skew_hold[1].split("=== POST-ROUTE SETUP SUMMARY ===", 1)[0] if len(skew_hold) > 1 else ""
    if period is None or period <= 0 or setup is None or hold is None:
        raise ValueError(f"{path}: required post-route period/setup/hold metric missing")
    return {
        "postroute_all_path_min_period_ns": period,
        "postroute_all_path_fmax_mhz": fmax,
        "postroute_worst_setup_slack_ns": setup,
        "postroute_setup_wns_ns": setup_wns,
        "postroute_setup_tns_ns": setup_tns,
        "postroute_worst_hold_slack_ns": hold,
        "postroute_hold_wns_ns": hold_wns,
        "postroute_hold_tns_ns": hold_tns,
        "setup_clock_skew_report": setup_skew_text.strip(),
        "hold_clock_skew_report": hold_skew_text.strip(),
        "clock_skew_supported": bool(setup_skew_text.strip() and hold_skew_text.strip()) and "TIMINGFORGE_CLOCK_SKEW_UNSUPPORTED" not in setup_skew_text + hold_skew_text,
        "postroute_log": str(path),
    }


def compare(prelayout_path: Path, physical_root: Path) -> dict:
    matrix = json.loads(prelayout_path.read_text(encoding="utf-8"))
    if matrix.get("platform") != "Nangate45 typical Liberty":
        raise ValueError("Pre-layout platform/corner does not match Nangate45 typical")
    source_sdc = prelayout_path.resolve().parents[2] / "constraints" / "gcd_baseline.sdc"
    if not source_sdc.is_file():
        raise FileNotFoundError(f"Missing baseline SDC: {source_sdc}")
    sdc_hash = hashlib.sha256(source_sdc.read_bytes()).hexdigest()
    records = {(row.get("top"), row.get("scenario")): row for row in matrix.get("records", [])}
    results = []
    for top in TOPS:
        baseline = records.get((top, "gcd_baseline"))
        if baseline is None:
            raise ValueError(f"Pre-layout golden row missing for {top}")
        post = parse_postroute_log(physical_root / top / "postroute_sta.log")
        results.append({
            "top": top,
            "platform": "Nangate45",
            "corner": "typical",
            "source_sdc_sha256": sdc_hash,
            "prelayout_all_path_min_period_ns": baseline.get("all_path_min_period_ns"),
            "postroute_all_path_min_period_ns": post["postroute_all_path_min_period_ns"],
            "all_path_min_period_delta_ns": (
                round(post["postroute_all_path_min_period_ns"] - baseline["all_path_min_period_ns"], 6)
                if baseline.get("all_path_min_period_ns") is not None else None
            ),
            "prelayout_worst_setup_slack_ns": baseline.get("worst_setup_slack_ns"),
            "postroute_worst_setup_slack_ns": post["postroute_worst_setup_slack_ns"],
            "setup_slack_delta_ns": (
                round(post["postroute_worst_setup_slack_ns"] - baseline["worst_setup_slack_ns"], 6)
                if baseline.get("worst_setup_slack_ns") is not None else None
            ),
            "prelayout_worst_hold_slack_ns": baseline.get("worst_hold_slack_ns"),
            "postroute_worst_hold_slack_ns": post["postroute_worst_hold_slack_ns"],
            "hold_slack_delta_ns": (
                round(post["postroute_worst_hold_slack_ns"] - baseline["worst_hold_slack_ns"], 6)
                if baseline.get("worst_hold_slack_ns") is not None else None
            ),
            **post,
        })
    return {
        "schema_version": "1.0",
        "comparison": "same Nangate45 typical corner and source baseline SDC; pre-layout cell-based STA vs post-route propagated-clock SPEF STA",
        "signoff_claim": False,
        "designs": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prelayout_matrix", type=Path)
    parser.add_argument("physical_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.prelayout_matrix, args.physical_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "designs": [row["top"] for row in result["designs"]],
        "clock_skew_supported": [row["clock_skew_supported"] for row in result["designs"]],
        "signoff_claim": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
