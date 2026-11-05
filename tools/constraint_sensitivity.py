"""Generate deterministic clock-constraint sensitivity SDC variants."""
from __future__ import annotations
import re

SETUP_RE = re.compile(r"^set_clock_uncertainty -setup [0-9.]+ \\[get_clocks core_clk\\]$", re.MULTILINE)
HOLD_RE = re.compile(r"^set_clock_uncertainty -hold [0-9.]+ \\[get_clocks core_clk\\]$", re.MULTILINE)

def generate_variants(baseline: str) -> list[dict]:
    """Return setup, hold, and source-latency variants derived from immutable text."""
    if len(SETUP_RE.findall(baseline)) != 1:
        raise ValueError("Expected exactly one canonical setup uncertainty for core_clk")
    if len(HOLD_RE.findall(baseline)) != 1:
        raise ValueError("Expected exactly one canonical hold uncertainty for core_clk")
    variants = []
    for value in (0.100, 0.150, 0.200):
        rendered = SETUP_RE.sub(f"set_clock_uncertainty -setup {value:.3f} [get_clocks core_clk]", baseline)
        variants.append({"name": f"S_setup_uncertainty_{value:.3f}".replace(".", "p"),
                         "kind": "setup_uncertainty", "value_ns": value,
                         "sdc_text": rendered})
    for value in (0.025, 0.050, 0.075):
        rendered = HOLD_RE.sub(f"set_clock_uncertainty -hold {value:.3f} [get_clocks core_clk]", baseline)
        variants.append({"name": f"S_hold_uncertainty_{value:.3f}".replace(".", "p"),
                         "kind": "hold_uncertainty", "value_ns": value,
                         "sdc_text": rendered})
    for late in (0.000, 0.050, 0.100):
        rendered = baseline + (
            f"\n# Sensitivity experiment: source latency early/late asymmetry\n"
            f"set_clock_latency -source -early 0.000 [get_clocks core_clk]\n"
            f"set_clock_latency -source -late {late:.3f} [get_clocks core_clk]\n"
        )
        variants.append({"name": f"S_source_latency_late_{late:.3f}".replace(".", "p"),
                         "kind": "source_latency_early_late", "value_ns": late,
                         "early_ns": 0.000, "late_ns": late, "sdc_text": rendered})
    return variants
