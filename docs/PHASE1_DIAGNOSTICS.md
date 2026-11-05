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

Clock uncertainty/latency sensitivity experiments remain a separate Phase 1 task until a dedicated runner records exact changed values, baseline comparisons, source/tool/library identity, and raw logs.
