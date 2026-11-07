# TimingForge v0.4.0 — Release notes (candidate)

> **Status: NOT RELEASED.** This document is a release draft. Publish only after the v0.4.0 release gate in [DEVELOPMENT_PHASES.md](DEVELOPMENT_PHASES.md) is satisfied.

## Highlights

- Adds deeper GCD verification: a bounded WIDTH=3 formal miter connected to an independent exhaustive 64-entry GCD oracle, a deliberate RTL mutant negative control, Verilator protocol SVA checks, and WIDTH=8/16/32 simulation sweeps.
- Adds a fail-closed, environment-specific Nangate45 typical-corner QoR regression gate.
- Adds reproducible ASAP7 BC/TC/WC MCMM analysis scripts and a separate SKY130HD TT physical implementation/post-route STA experiment.
- Adds technology provenance, Liberty and physical-artifact SHA-256 manifests, unit checks, and explicit methodology boundaries.
- Retains the original SDC fault-injection benchmark, OpenSTA diagnostics, sensitivity experiments, and Nangate45 physical-design evidence.

## Verification and evidence

All five PR #10 workflows passed on source commit `8dc274761fad6d315c5c349b129f63d94c9a6f89`:

- Regression and library-backed Nangate45 STA/QoR: [run #42225754505](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754505); [STA matrix artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754505/artifacts/13506026425), [static benchmark artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754505/artifacts/13506240639).
- Updated WIDTH=3 oracle-backed formal proof and deliberate mutant rejection: [run #42225754417](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754417); [formal artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754417/artifacts/13494245840).
- Nangate45 typical physical implementation: [run #42225754311](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754311); [physical artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754311/artifacts/13505672933).
- ASAP7 BC/TC/WC MCMM and SKY130HD TT physical flow: [run #42225754263](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754263); [technology-breadth artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754263/artifacts/13505838538).

The ASAP7 combined-design WC scene reported -3.225 ps minimum hold slack among the emitted hold paths. This is retained as a warning, not hidden or described as full hold closure. OpenSTA's `-group_path_count 100` requests up to 100 paths per path group; the parser reports minima among emitted rows only, not an exhaustive path inventory. The SKY130HD TT post-route all-path minimum periods were 4.96 ns (combined) and 5.06 ns (split). Full per-scene and per-platform measurements are in [Phase 3 technology-breadth results](PHASE3_TECHNOLOGY_BREADTH_RESULTS.md).

The separate physical robustness workflow also passed on [PR #10 run #42225754303](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754303), with its [evidence artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754303/artifacts/13512635145). At the 2.500 ns target, combined GCD did not close because of a max-capacitance violation (54.633 versus a 53.406 limit; slack -1.227), while split GCD closed. These are PR-branch validation runs. The PR must still be merged and all five workflows must pass on the resulting main commit before a v0.4.0 tag/release is published.



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
- [ ] PR #10 is merged and all five required workflows pass on the resulting `main` commit.
- [ ] README, results and phase tracker are confirmed against final main-branch run IDs.
- [ ] Tag `v0.4.0` is created at the validated `main` commit.
- [ ] GitHub release is published with these notes and evidence links.
