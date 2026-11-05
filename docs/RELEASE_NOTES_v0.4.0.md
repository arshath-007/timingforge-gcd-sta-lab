# TimingForge v0.4.0 — Release notes (candidate)

> **Status: NOT RELEASED.** This document is a release draft. Publish only after the v0.4.0 release gate in [DEVELOPMENT_PHASES.md](DEVELOPMENT_PHASES.md) is satisfied.

## Highlights

- Adds deeper GCD verification: a bounded WIDTH=3 formal miter connected to an independent exhaustive 64-entry GCD oracle, a deliberate RTL mutant negative control, Verilator protocol SVA checks, and WIDTH=8/16/32 simulation sweeps.
- Adds a fail-closed, environment-specific Nangate45 typical-corner QoR regression gate.
- Adds reproducible ASAP7 BC/TC/WC MCMM analysis scripts and a separate SKY130HD TT physical implementation/post-route STA experiment.
- Adds technology provenance, Liberty and physical-artifact SHA-256 manifests, unit checks, and explicit methodology boundaries.
- Retains the original SDC fault-injection benchmark, OpenSTA diagnostics, sensitivity experiments, and Nangate45 physical-design evidence.

## Verification and evidence

All four required PR #8 workflows passed on source commit 6f5a9c1b9c73261005445a6fd941242e6dde54cb:

- Regression and library-backed Nangate45 STA/QoR: [run #42098727056](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727056); [STA matrix artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727056/artifacts/13449670505), [static benchmark artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727056/artifacts/13449555421).
- Updated WIDTH=3 oracle-backed formal proof and deliberate mutant rejection: [run #42098727465](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727465); [formal artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727465/artifacts/13449462598).
- Nangate45 typical physical implementation: [run #42098727330](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727330); [physical artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727330/artifacts/13450410051).
- ASAP7 BC/TC/WC MCMM and SKY130HD TT physical flow: [run #42098727158](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727158); [technology-breadth artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727158/artifacts/13449087689).

The ASAP7 combined-design WC scene reported -3.225 ps minimum hold slack among its 100 emitted hold paths. This is retained as a warning, not hidden or described as full hold closure. The SKY130HD TT post-route all-path minimum periods were 4.96 ns (combined) and 5.06 ns (split). Full per-scene and per-platform measurements are in [Phase 3 technology-breadth results](PHASE3_TECHNOLOGY_BREADTH_RESULTS.md).

These are PR-branch validation runs. The PR must still be merged and all four workflows must pass on the resulting main commit before a v0.4.0 tag/release is published.



## Scope and limitations

- The formal result is bounded at WIDTH=3 and does not prove all 32-bit operand pairs, arbitrary transaction sequences, or an unbounded invariant.
- Verilator concurrent-SVA checks are dynamic simulation assertions, not unbounded formal proof.
- ASAP7 BC/TC/WC MCMM uses distinct Liberty PVT timing scenes but reuses one TC-extracted SPEF unchanged; no corner-specific RC extraction/scaling is claimed.
- SKY130HD uses the pinned platform's verified TT model only; no fast/slow corners are invented.
- Absolute PPA comparisons across Nangate45, ASAP7 and SKY130HD are not apples-to-apples.
- No foundry signoff, OCV/AOCV/POCV, crosstalk/SI, power signoff, IR/EM, DRC/LVS, or manufacturing-readiness claim is made.

## Release publication checklist

- [x] Updated oracle-backed formal workflow passes and the proof artifact is reviewed.
- [x] ASAP7 MCMM + SKY130HD physical workflow passes and its manifest/artifacts are reviewed.
- [ ] PR #8 is merged and all required workflows pass on the resulting `main` commit.
- [ ] README, results and phase tracker are confirmed against final main-branch run IDs.
- [ ] Tag `v0.4.0` is created at the validated `main` commit.
- [ ] GitHub release is published with these notes and evidence links.
