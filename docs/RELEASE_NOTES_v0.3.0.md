# TimingForge v0.3.0 — Phase 1 STA Reliability Diagnostics

## Overview

This release candidate completes Phase 1 of the TimingForge roadmap. It extends the v0.2.2 functional-regression maintenance candidate with design-rule reporting, constraint sensitivity experiments, and explicit mutation-impact analysis.

## Changes

- Added OpenSTA violator-only reports for maximum slew/transition, maximum capacitance, and maximum fanout.
- Added conservative quality findings for reported DRV violations. Unsupported reports remain null; no violation records are not treated as proof of complete check coverage.
- Added mutation-impact analysis with matched, mismatched, and inconclusive outcomes. No aggregate accuracy percentage is used.
- Added nine clock-constraint sensitivity variants per GCD architecture: setup uncertainty, hold uncertainty, and source-latency early/late asymmetry.
- Added reproducibility metadata: source SHA, tool versions, Nangate45 Liberty hash, baseline/variant SDC hashes, exact changed parameter, raw log paths, and baseline-relative timing deltas.
- Added unit tests for DRV parsing, quality findings, mutation-impact assessment, and sensitivity-variant generation.
- Updated the development tracker, measured diagnostics, scope, README, and interview guides.

## Verification

Both final Phase 1 validation runs passed both GitHub Actions jobs:

- [Run #257 — feature-branch validation](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42046659049)
- [Run #258 — post-merge main validation](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42047005600)
- [Run #258 STA artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42047005600/artifacts/13425391627)

Measured evidence from the two runs was consistent:

- 18 sensitivity experiments completed (nine variants × two architectures).
- Mutation impact: 12 matched, 0 mismatched, 2 inconclusive. M06 remains inconclusive for both architectures because the parsed reports do not directly expose whether hold uncertainty was applied.
- Combined GCD: 10 max-slew and 15 max-capacitance violation records.
- Split GCD: 9 max-slew and 15 max-capacitance violation records.
- No max-fanout violation records were reported; the violator-only report does not enumerate total applicable checks.
- Golden quality findings remain REVIEW. The combined design has -0.002 ns hold slack, and its native register-only minimum-period metric remains unavailable.

## Scope and limitations

The benchmark remains an educational pre-layout Nangate45 typical-corner experiment with ideal clocks and no extracted SPEF. The sensitivity runs are not CTS or propagated-clock measurements. The DRV reports do not establish complete check coverage or signoff closure. FIFO and MAC remain functional-only extensions and are not included in the GCD STA matrix.

Phase 2 formal verification/QoR analytics and Phase 3 physical implementation/multi-corner work are not included in this release.

**Previous published release:** v0.2.1  
**Superseded candidate:** v0.2.2 (prepared but not published)
