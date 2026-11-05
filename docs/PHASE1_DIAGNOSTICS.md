# Phase 1 diagnostics — implementation notes

## Scope

This document describes the first implementation slice for Phase 1. It is a diagnostic aid, not a signoff checklist.

## Design-rule reporting

The OpenSTA script requests three design-rule report classes independently:

- Maximum slew (transition).
- Maximum capacitance.
- Maximum fanout.

The parser records whether each report section was emitted, the number of lines explicitly marked `VIOLATED`, and the raw violation lines. If the command is unavailable in the installed build, the report is marked unsupported and its count remains null. A null count must not be interpreted as zero violations.

The command options are documented by the [OpenSTA command reference](https://opensta.readthedocs.io/en/latest/Commands/). The report is meaningful only for checks that are actually defined by the loaded Liberty/design constraints.

## SDC mutation impact

The mutation-impact report compares each known mutation with a directly observable signal:

| Mutation | Expected observation | Interpretation |
|---|---|---|
| M01 missing clock | Primary clock properties unavailable | Matched only when no valid clock period is reported |
| M02 missing input delay | Missing input-delay ports | Matched when OpenSTA reports missing input delays |
| M03 missing output delay | Missing output-delay ports | Matched when OpenSTA reports missing output delays |
| M04 broad false path | No register-to-register path in the dedicated report | Matched when the path report is empty |
| M05 near-match port | Missing input-delay ports | Matched when the incorrect collection leaves inputs uncovered |
| M06 missing hold uncertainty | Not directly observable in the current parsed evidence | Inconclusive; do not infer from hold slack alone |
| M07 non-positive period | Non-positive reported clock period | Matched only when the invalid period is explicitly observed |

Results use `matched`, `mismatched`, and `inconclusive` states. They are not aggregated into a single accuracy percentage because each mutation tests a different property and some effects are not observable in the current report parser.

## Validation boundary

A successful regression demonstrates that the scripts, parser, and unit tests execute in the CI environment. A library-backed STA pass demonstrates that the benchmark matrix runs with the configured Nangate45 platform. It does not establish production signoff, complete DRV coverage, or semantic correctness of arbitrary SDC files.

## Measured Phase 1 evidence

Both [run #257](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42046659049) and [post-merge run #258](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42047005600) passed regression and library-backed STA. The [run #258 artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42047005600/artifacts/13425391627) archives raw logs, the 16-scenario matrix, quality findings, mutation impact JSON, generated sensitivity SDCs, and sensitivity summary.

### Baseline DRV violation records

| Architecture | Max-slew violations | Max-capacitance violations | Max-fanout violation records |
|---|---:|---:|---:|
| Combined GCD | 10 | 15 | 0 |
| Split GCD | 9 | 15 | 0 |

The fanout count means no violation records were emitted by the violator-only report; it does **not** establish the total number of applicable fanout checks. The golden quality summary is REVIEW: five warnings and three informational findings. Warnings include the combined design's -0.002 ns hold slack and the reported slew/capacitance violations. The combined design's native register-only minimum-period query remains unavailable.

### Constraint sensitivity

The runner generated nine variants for each architecture, always changing one constraint family at a time from the golden SDC. Deltas below are relative to the golden baseline.

| Experiment | Values (ns) | Setup slack delta (ns) | Hold slack delta (ns) |
|---|---|---|---|
| Setup uncertainty | 0.100 / 0.150 / 0.200 | +0.050 / 0 / -0.050 | 0 / 0 / 0 |
| Hold uncertainty | 0.025 / 0.050 / 0.075 | 0 / 0 / 0 | +0.025 / 0 / -0.025 |
| Source latency (early=0; late varied) | 0 / 0.050 / 0.100 | 0 / -0.050 / -0.100 | 0 / -0.050 / -0.100 |

The measured deltas were consistent across the combined and split architectures. All-path minimum periods also changed with the constraint variants; these include port paths and are not internal register-only Fmax values. Source-latency variants are controlled ideal-clock sensitivity experiments, not CTS or propagated-clock measurements.

### Mutation impact

Across both architectures the checker reported **12 matched, 0 mismatched, and 2 inconclusive** mutation observations. M06 is inconclusive for each architecture because the current parsed reports do not directly expose whether hold uncertainty was applied. This is intentional: hold slack alone is not used as proof of constraint presence.

The sensitivity summary records the source SHA, tool versions, Nangate45 Liberty hash, baseline and variant SDC hashes, exact changed parameter, raw log path, and baseline-relative deltas.

## Validation boundary

A successful regression demonstrates that the scripts, parser, and unit tests execute in the CI environment. A library-backed STA pass demonstrates that the benchmark matrix runs with the configured Nangate45 platform. It does not establish production signoff, complete DRV coverage, or semantic correctness of arbitrary SDC files.
