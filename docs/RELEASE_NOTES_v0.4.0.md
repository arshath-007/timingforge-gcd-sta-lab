# TimingForge v0.4.0 — Release notes (candidate)

> **Status: NOT RELEASED.** This document is a release draft. Publish only after the v0.4.0 release gate in [DEVELOPMENT_PHASES.md](DEVELOPMENT_PHASES.md) is satisfied.

## Highlights

- Adds deeper GCD verification: a bounded WIDTH=3 formal miter connected to an independent exhaustive 64-entry GCD oracle, a deliberate RTL mutant negative control, Verilator protocol SVA checks, and WIDTH=8/16/32 simulation sweeps.
- Adds a fail-closed, environment-specific Nangate45 typical-corner QoR regression gate.
- Adds reproducible ASAP7 BC/TC/WC MCMM analysis scripts and a separate SKY130HD TT physical implementation/post-route STA experiment.
- Adds technology provenance, Liberty and physical-artifact SHA-256 manifests, unit checks, and explicit methodology boundaries.
- Retains the original SDC fault-injection benchmark, OpenSTA diagnostics, sensitivity experiments, and Nangate45 physical-design evidence.

## Verification and evidence

The PR #8 regression and library-backed Nangate45 STA/QoR workflow passed on source commit `388958f7228b29262793cd01b7bc9561d4db1855` in [run #42094688499](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42094688499).

The updated oracle-backed formal workflow [#42094688482](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42094688482) and technology-breadth workflow [#42094688423](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42094688423) were still in progress at the time this draft was prepared. Their results must be added only after successful completion and artifact inspection.

The Nangate45 physical baseline remains documented with its original evidence in [Phase 3 results](PHASE3_RESULTS.md). It must not be conflated with the ASAP7 or SKY130HD experiments.

## Scope and limitations

- The formal result is bounded at WIDTH=3 and does not prove all 32-bit operand pairs, arbitrary transaction sequences, or an unbounded invariant.
- Verilator concurrent-SVA checks are dynamic simulation assertions, not unbounded formal proof.
- ASAP7 BC/TC/WC MCMM uses distinct Liberty PVT timing scenes but reuses one TC-extracted SPEF unchanged; no corner-specific RC extraction/scaling is claimed.
- SKY130HD uses the pinned platform's verified TT model only; no fast/slow corners are invented.
- Absolute PPA comparisons across Nangate45, ASAP7 and SKY130HD are not apples-to-apples.
- No foundry signoff, OCV/AOCV/POCV, crosstalk/SI, power signoff, IR/EM, DRC/LVS, or manufacturing-readiness claim is made.

## Release publication checklist

- [ ] Updated oracle-backed formal workflow passes and artifacts are reviewed.
- [ ] ASAP7 MCMM + SKY130HD physical workflow passes and manifest/artifacts are reviewed.
- [ ] All required workflows pass on the final merged `main` commit.
- [ ] README, results and phase tracker are updated with final run IDs and measured values.
- [ ] Tag `v0.4.0` is created at the validated `main` commit.
- [ ] GitHub release is published with these notes and evidence links.
