# TimingForge v0.4.0 — Release notes (candidate)

> **Status: VALIDATED RELEASE CANDIDATE — NOT YET PUBLISHED.** All five required workflows passed on the resulting `main` commit. The project owner waived independent review. Publish only after the `v0.4.0` tag and GitHub Release are created and verified.

## Highlights

- Adds deeper GCD verification: a bounded WIDTH=3 formal miter connected to an independent exhaustive 64-entry GCD oracle, a deliberate RTL mutant negative control, Verilator protocol SVA checks, and WIDTH=8/16/32 simulation sweeps.
- Adds a fail-closed, environment-specific Nangate45 typical-corner QoR regression gate.
- Adds reproducible ASAP7 BC/TC/WC MCMM analysis scripts and a separate SKY130HD TT physical implementation/post-route STA experiment.
- Adds technology provenance, Liberty and physical-artifact SHA-256 manifests, unit checks, and explicit methodology boundaries.
- Retains the original SDC fault-injection benchmark, OpenSTA diagnostics, sensitivity experiments, and Nangate45 physical-design evidence.

## Verification and evidence

The v0.4.0 release-candidate source commit is `d6a7247d066e668165a8b4ce0187779fc2ae8164`. PR #10 was merged to `main`, and all five required workflows passed on that exact commit:

- Regression and library-backed Nangate45 STA/QoR: [main run #42361605851](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605851); [STA matrix artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605851/artifacts/13569358610), [static benchmark artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605851/artifacts/13570052103).
- Updated WIDTH=3 oracle-backed formal proof and deliberate mutant rejection: [main run #42361605849](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605849); [formal artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605849/artifacts/13570052527).
- Nangate45 typical physical implementation: [main run #42361605868](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605868); [physical artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605868/artifacts/13570500287).
- ASAP7 BC/TC/WC MCMM and SKY130HD TT physical flow: [main run #42361605880](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605880); [technology-breadth artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605880/artifacts/13570383217).
- Five placement pairs and six clock-period robustness sweeps: [main run #42361605870](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605870); [physical-robustness artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605870/artifacts/13571333561).

The ASAP7 combined-design WC scene reported -3.225 ps minimum hold slack among the emitted hold paths. This is retained as a warning, not hidden or described as full hold closure. OpenSTA's `-group_path_count 100` requests up to 100 paths per path group; the parser reports minima among emitted rows only, not an exhaustive path inventory. The SKY130HD TT post-route all-path minimum periods were 4.96 ns (combined) and 5.06 ns (split). Full per-scene and per-platform measurements are in [Phase 3 technology-breadth results](PHASE3_TECHNOLOGY_BREADTH_RESULTS.md).

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
- [x] PR #10 is merged and all five required workflows pass on the resulting `main` commit.
- [x] README, results and phase tracker are confirmed against final main-branch run IDs in PR #12.
- [ ] Tag `v0.4.0` is created at the validated release commit.
- [ ] GitHub release is published with these notes and evidence links.
