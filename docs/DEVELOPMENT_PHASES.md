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
- [x] Latest PR #10 regression and library-backed STA/QoR workflow passed on commit `8dc274761fad6d315c5c349b129f63d94c9a6f89`: [run #42225754505](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754505). Artifacts: [Nangate45 STA matrix](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754505/artifacts/13506026425) and [static benchmark](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754505/artifacts/13506240639).

### Formal proof validation and scope

The updated oracle-backed miter passed the dedicated PR #10 [formal workflow run #42225754417](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754417); the [formal artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754417/artifacts/13494245840) records the positive proof and negative controls. Yosys 0.33 plus CVC5 1.1.2 completed the positive proof at 26 SMT steps / 12 positive clock edges in 11:08. The intentionally broken subtract mutant was rejected at step 5 for operands a=5, b=3.

The proof checks both architectures against the independent 64-entry WIDTH=3 GCD oracle, checks mutual result equivalence, and verifies one accepted transaction, completion, done/busy behavior and the 12-edge bound. It is exhaustive for all 64 WIDTH=3 operand pairs only. It is not a proof of all 32-bit operands, arbitrary back-to-back transactions, or an unbounded sequential invariant. The 32-bit and WIDTH=8/16/32 tests remain simulation evidence; Verilator concurrent-SVA protocol checks are dynamic assertion evidence, not part of the Yosys/CVC5 proof.



### QoR gate boundary
The reviewed baseline and limits apply only to the pinned Nangate45 typical environment. They are regression thresholds for this educational benchmark, not universal signoff limits. QoR snapshots are retained as CI artifacts, not a persistent database/dashboard.

## Phase 3 — Physical implementation and technology breadth

### Validated baseline
- [x] Nangate45 typical physical implementation for both architectures through floorplan, placement, CTS, routing, extraction and post-route OpenSTA.
- [x] ODB/GDS/SPEF/SDC, logs, reports and SHA-256 evidence archived in the latest PR #10 [physical run #42225754311](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754311), artifact [13505672933](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754311/artifacts/13505672933).

### Implemented and validated technology-breadth experiment

- [x] ASAP7 BC/TC/WC Liberty scene setup and post-route OpenSTA MCMM analysis for both architectures.
- [x] Separate SKY130HD TT physical implementation and extracted-parasitic post-route STA for both architectures.
- [x] Pinned platform provenance, Liberty PVT/unit checks, tool/library/artifact hashes and a SHA-256 manifest.
- [x] All four physical builds, both ASAP7 three-scene MCMM analyses, both SKY130HD post-route analyses and manifest generation passed in PR #10 [technology-breadth run #42225754263](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754263). The [90-day artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754263/artifacts/13505838538) contains 412 files and the manifest. Its four design/platform combinations each include final ODB, Verilog, GDS, SPEF and SDC; all 36 manifest-listed implementation-artifact hashes were independently verified after download.

**ASAP7 measured MCMM results (minimum slack among emitted paths; report request capped at 100 paths per path group):**

| Architecture | Scene | PVT | Setup slack (ps) | Hold slack (ps) |
|---|---|---|---:|---:|
| Combined | BC | FF, 0°C, 0.77 V | 7973.601 | 8.200 |
| Combined | TC | TT, 25°C, 0.70 V | 7803.926 | 17.088 |
| Combined | WC | SS, 100°C, 0.63 V | 7504.804 | -3.225 |
| Split | BC | FF, 0°C, 0.77 V | 7948.192 | 5.724 |
| Split | TC | TT, 25°C, 0.70 V | 7780.835 | 16.630 |
| Split | WC | SS, 100°C, 0.63 V | 7490.069 | 5.691 |

The combined WC scene has a negative hold slack among its emitted hold paths; the experiment must not be described as full hold closure. OpenSTA `report_checks -group_path_count 100` requests up to 100 paths per path group, not 100 paths total. The parser reports minima among emitted slack rows only; no exhaustive signoff path inventory or full-path WNS/TNS claim is made. Each architecture's TC-extracted SPEF is reused unchanged across BC/TC/WC. There is no corner-specific RC extraction or scaling.

**SKY130HD TT post-route results:**

| Architecture | Register-to-register minimum period | Register-to-register Fmax | All-path minimum period | All-path Fmax | Worst setup slack | Worst hold slack |
|---|---:|---:|---:|---:|---:|---:|
| Combined | 4.96 ns | 201.70 MHz | 4.96 ns | 201.70 MHz | +5.042 ns | +0.066 ns |
| Split | 4.91 ns | 203.52 MHz | 5.06 ns | 197.46 MHz | +4.936 ns | +0.257 ns |

The SKY130HD experiment uses the pinned platform's verified TT, 25°C, 1.80 V model only. No SKY130HD fast/slow corners are claimed. The ASAP7 and SKY130HD results are separate platform experiments; absolute cross-library PPA ranking is not valid.



### Physical robustness and evidence audit

- [x] Run five paired placement/utilization variants and six clock-period targets for both architectures; retain raw reports and machine-readable results.
- [x] Validate all 22 physical-experiment reports with no ORFS flow failures in [workflow run #42191546348](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42191546348); the [90-day artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42191546348/artifacts/13492292148) contains 2,386 files.
- [x] Verify all 174 physical manifest entries against the PR #9 Nangate45 physical artifact and all 36 implementation-file hashes in the PR #10 technology-breadth artifact.

Five paired Nangate45 typical-corner placement variants produced a combined-GCD mean register-only period of 0.922 ns (0.89–0.96 ns) and split-GCD mean of 1.050 ns (1.01–1.18 ns). Combined had the shorter register-only period in 5/5 pairs. Mean standard-cell area was 2657.66 for combined and 2500.88 for split (about 5.9% lower for split). These five controlled variants do not establish a universal architecture winner.

The latest PR #10 physical robustness workflow [run #42225754303](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754303), [artifact #13512635145](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754303/artifacts/13512635145), completed five placement pairs and six target-period points for both architectures. The clock sweep classified both architectures as not closed at 1.0, 1.2 and 1.5 ns; both closed at 2.0 and 3.0 ns; at 2.5 ns, split closed but combined did not because a max-capacitance violation remained (54.633 vs 53.406, slack -1.227). Positive setup/hold slack alone is insufficient for closure.

**Methodology boundary:** pre-layout and ORFS physical netlists use different synthesis settings. Their period deltas are cross-flow observations, not matched-netlist routing deltas. The physical LEC subprocess is disabled. The ASAP7 MCMM experiment reuses one TC-extracted SPEF across BC/TC/WC, has a 100-path cap, and shows -3.225 ps combined-GCD WC hold slack. No full PVT/RC or signoff claim is made.

### Explicitly out of scope
- [ ] OCV/AOCV/POCV without validated variation models and methodology.
- [ ] Crosstalk/SI, power signoff, IR-drop/EM qualification, timing ECO closure, foundry DRC/LVS signoff, or manufacturing readiness.
- [ ] Netlist-to-netlist LEC across ORFS optimization stages; the optional Kepler LEC subprocess is disabled.

## v0.4.0 release gate

Do not publish v0.4.0 until all of the following are true:
1. [x] The updated oracle-backed formal workflow passes positive proof and negative controls on PR #10 (run #42225754417).
2. [x] The technology-breadth workflow completes all four physical builds, both ASAP7 three-scene MCMM analyses, both SKY130HD post-route analyses, and actual-Liberty PVT manifest validation on PR #10 (run #42225754263).
3. [ ] The PR is merged; fresh workflows on the resulting main commit pass regression, formal, Nangate45 physical, technology breadth and physical robustness.
4. [ ] README, phase tracker, measured-results page and release notes are confirmed against the final main-branch run IDs.
5. [ ] A release tag is created at the validated main commit and its evidence artifacts are attached or linked.

PR #10 commit `8dc274761fad6d315c5c349b129f63d94c9a6f89` has passed the five current PR workflows: [regression #42225754505](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754505), [formal #42225754417](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754417), [Nangate45 physical #42225754311](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754311), [technology breadth #42225754263](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754263), and [physical robustness #42225754303](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754303). The PR still requires independent technical review, merge and fresh main-branch validation before v0.4.0 can be tagged or published.



## Execution policy

A script or an uncompleted workflow is not validation. Preserve raw logs and hashes, report blocked checks plainly, and never turn an unsupported capability into a claimed result.
