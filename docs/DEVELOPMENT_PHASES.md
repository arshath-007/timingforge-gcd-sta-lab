# TimingForge development phases

This tracker distinguishes implemented code from completed validation. A feature is marked validated only when a successful run exercises it and its evidence artifact is retained.

## Phase 1 — Trustworthy analysis and result quality

### Completed and validated
- [x] Two synthesizable GCD architectures and self-checking functional regression.
- [x] FIFO/MAC functional extension tests (not included in the GCD STA/physical matrix).
- [x] Seven controlled SDC mutation patterns, conservative static checker, machine-readable scorecard and unit tests.
- [x] Library-backed Nangate45 typical synthesis/OpenSTA matrix for both architectures.
- [x] Quality findings, critical-path labels, DRV reports, nine clock-sensitivity variants per architecture, and expected-versus-observed mutation impact scoring.
- [x] Historical evidence validated in [run #257](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42046659049) and [post-merge run #258](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42047005600).

**Known interpretation:** mutation impact was 12 matched, 0 mismatched and 2 inconclusive (both hold-uncertainty cases). Golden quality findings were REVIEW; combined hold slack was -0.002 ns and its native register-only minimum-period query was unavailable. No overall checker accuracy percentage is claimed.

## Phase 2 — Verification depth and QoR analytics

### Implemented
- [x] Bounded WIDTH=3 transaction miter with independent completion timing and a 12-positive-edge completion bound (26 SMT steps).
- [x] Independent 64-entry WIDTH=3 GCD truth-table oracle, cross-checked against Python's Euclidean math.gcd reference.
- [x] Positive proof and deliberately broken subtract-mutant negative control are part of the formal script.
- [x] Concurrent protocol SVA (done one-cycle pulse and done -> !busy) exercised dynamically with Verilator.
- [x] Parameterized WIDTH=8/16/32 simulation sweep.
- [x] 32-bit directed and 250 seeded constrained-random tests (seed 0x54462026; 259 cases per architecture).
- [x] Environment-keyed QoR snapshots and a fail-closed Nangate45 typical-corner regression gate.
- [x] Latest regression/STA workflow on PR #8 commit 388958f passed: [run #42094688499](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42094688499). It exercised the RTL/width/SVA/Python and library-backed STA/QoR paths.

### Formal proof scope and current CI state
The independent oracle is now connected to both implementations inside the bounded formal miter. However, the dedicated formal workflow for the updated miter, [run #42094688482](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42094688482), was still reported in progress at the last repository check; its install step had not completed. Therefore the updated oracle-backed proof is implemented but **not yet recorded as CI-verified**. The earlier [run #49](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957430) validates the earlier bounded miter and negative control, not the new oracle-connected property set.

The proof is WIDTH=3 and bounded. It is not a proof of all 32-bit inputs, arbitrary back-to-back transactions, or an unbounded invariant. Verilator SVA and wider simulations are complementary dynamic evidence, not a substitute for those proofs.

### QoR gate boundary
The reviewed baseline and limits apply only to the pinned Nangate45 typical environment. They are regression thresholds for this educational benchmark, not universal signoff limits. QoR snapshots are retained as CI artifacts, not a persistent database/dashboard.

## Phase 3 — Physical implementation and technology breadth

### Validated baseline
- [x] Nangate45 typical physical implementation for both architectures through floorplan, placement, CTS, routing, extraction and post-route OpenSTA.
- [x] ODB/GDS/SPEF/SDC, logs, reports and SHA-256 evidence archived in [physical run #23](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957456), artifact [13439243211](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957456/artifacts/13439243211).

### Implemented technology-breadth experiment — validation pending
- [x] Add ASAP7 BC/TC/WC Liberty scene setup and post-route OpenSTA MCMM analysis scripts for both architectures.
- [x] Add separate SKY130HD TT RTL-to-GDS physical implementation and extracted-parasitic post-route STA for both architectures.
- [x] Pin platform provenance, record Liberty/artifact hashes, check library units, and generate a manifest.
- [ ] Complete and archive the dedicated [technology-breadth workflow](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/workflows/technology-breadth.yml). Its run [#42094688423](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42094688423) was still in progress at the last repository check, so no MCMM/second-library measured result is yet published as validated.

**ASAP7 interpretation:** BC/TC/WC use distinct Liberty timing models, but the experiment reuses the single TC-extracted SPEF unchanged for all three scenes. This isolates cell timing model differences under shared parasitics; it is not corner-specific RC extraction or complete PVT/RC signoff.

**SKY130HD interpretation:** the pinned platform provides the verified TT model used here. No fast/slow SKY130HD corners are fabricated. Cross-library absolute PPA ranking is not claimed.

### Explicitly out of scope
- [ ] OCV/AOCV/POCV without validated variation models and methodology.
- [ ] Crosstalk/SI, power signoff, IR-drop/EM qualification, timing ECO closure, foundry DRC/LVS signoff, or manufacturing readiness.
- [ ] Netlist-to-netlist LEC across ORFS optimization stages; the optional Kepler LEC subprocess is disabled.

## v0.4.0 release gate

Do not publish v0.4.0 until all of the following are true:
1. The updated oracle-backed formal workflow passes positive proof and negative control.
2. The technology-breadth workflow completes all four physical builds, both ASAP7 three-scene MCMM analyses, both SKY130HD post-route analyses, and manifest validation.
3. The final PR is merged; fresh workflows on the resulting main commit pass regression, formal, Nangate45 physical and technology breadth.
4. README, phase tracker, measured-results page, changelog and release notes refer only to evidence from those final runs.
5. A release tag is created at the validated main commit and its evidence artifacts are attached or linked.

The latest PR #8 regression and Nangate45 STA/QoR run passed on its then-current source SHA. The updated formal and technology-breadth runs were not yet complete at last check. The PR remains open; no v0.4.0 tag/release is published.

## Execution policy

A script or an uncompleted workflow is not validation. Preserve raw logs and hashes, report blocked checks plainly, and never turn an unsupported capability into a claimed result.
