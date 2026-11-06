# TimingForge development phases

This document is the execution tracker for the proposed expansion roadmap. A checkbox is marked complete only when the implementation exists and its stated acceptance evidence is available.

## Phase 1 — Trustworthy analysis and result quality

### Completed
- [x] Correct the README roadmap so functional FIFO/MAC blocks are not described as missing.
- [x] Add directed FIFO simultaneous read/write checks at non-full occupancy and while full.
- [x] Add MAC signed-boundary and clear-priority checks.
- [x] Add conservative quality findings for golden STA rows: missing required metrics, non-positive values, unconstrained endpoints, missing I/O delays, negative hold slack, missing register paths, capped path inventories, and unavailable native register-only period.
- [x] Add unit tests for quality-check behavior and run the checker in CI.
- [x] Add heuristic critical-path class labels from OpenSTA startpoint/endpoint names, with unknown fallback and unit tests.
- [x] Add OpenSTA violator-only reports for max transition, max capacitance and max fanout; unsupported reports remain null and empty fanout output is not treated as complete check coverage.
- [x] Add nine clock-constraint sensitivity variants per architecture, derived from the immutable golden SDC, with explicit setup/hold slack deltas and reproducibility metadata.
- [x] Add expected-versus-observed mutation impact scoring with matched, mismatched and inconclusive states; no aggregate accuracy percentage.
- [x] Validate findings against archived raw logs from feature-branch run #257 and post-merge main run #258; both passed both CI jobs.

**Phase 1 exit criteria:** all new checks have unit tests; the full workflow produces machine-readable findings; baseline and mutation behavior is explained; no derived internal Fmax is published without an independently validated method.

**Evidence:** [run #257](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42046659049) and [run #258](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42047005600), both at commit `30b7a7bcf862762627935813a31330efa85a1eff`; [run #258 STA artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42047005600/artifacts/13425391627).

## Phase 2 — Verification depth and QoR analytics

### Implemented and CI-verified
- [x] Add a bounded sequential transaction-equivalence property set for both GCD architectures, with tool/version and proof logs.
- [x] Add a documented immediate-assertion support matrix and explicit limitation for concurrent `assert property` SVA syntax.
- [x] Add 32-bit constrained-random tests with reproducible seed and coverage summaries (250 random cases plus directed cases).
- [x] Add environment-keyed QoR snapshots and a comparator that rejects mismatched platform, corner, tool versions, Liberty hash, scenario set, and SDC hashes.
- [x] Verify the formal positive proof and a deliberately broken RTL negative control.

### Deliberately deferred
- [ ] Add reviewed fail-closed thresholds for suspicious QoR findings; current quality findings are reported for engineering review rather than converted into broad CI failure gates.
- [ ] Add parameter/width sweeps after the reference model, testbench, synthesis top, and timing constraints are parameter-safe.
- [ ] Add concurrent SVA properties when a supported frontend/tool path is selected.

**Formal scope:** WIDTH=3, symbolic input pairs, one reset/start transaction, completion by 12 positive clock edges (26 SMT steps), Yosys 0.33 and CVC5 1.1.2. This is not a 32-bit or unbounded proof. The 32-bit designs are separately covered by simulation. QoR snapshots are GitHub Actions artifacts, not a persistent database/dashboard.

**Phase 2 evidence:**
- [Formal equivalence run #49](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957430) and its [proof artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957430/artifacts/13439043462).
- [Regression and library-backed STA run #336](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957502), including [static benchmark artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957502/artifacts/13439247462).
- 32-bit simulation checked 259 cases on both architectures (250 seeded random plus directed cases), seed `0x54462026`; 49 Python tests passed.

## Phase 3 — Physical implementation and technology breadth

### Implemented and experimentally validated
- [x] Establish a reproducible floorplan and placement flow for both GCD designs.
- [x] Add CTS, propagated-clock timing reports, and clock-skew reports.
- [x] Add global/detail routing and extracted parasitics, then run post-route STA.
- [ ] Establish a netlist-matched pre-layout/post-route comparison; current synthesis flows differ, so published deltas are cross-flow observations only.
- [x] Archive raw logs, tool versions, platform/constraint hashes, parasitics, reports, final databases, GDS and SHA-256 manifests.

### Remaining technology-breadth work
- [ ] Add multi-corner analysis only after identifying and verifying distinct Liberty process/voltage/temperature models.
- [ ] Add a second technology library only when its source, license, units, corner identity, and mapping compatibility are documented.
- [ ] Add variation-aware experiments (OCV/AOCV/POCV) only with appropriate validated models and methodology.

**Historical Phase 3 evidence:** [OpenROAD physical-design run #23](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957456) passed on PR #6 merge SHA `4686342491aeabc5746fecd36f7e33b2d90c8b5b`, not a standalone main-branch commit. The [90-day physical evidence artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957456/artifacts/13439243211) includes final ODB/GDS/SPEF/SDC, stage logs/reports, post-route STA, comparison JSON and SHA-256 manifest. See [measured Phase 3 results](PHASE3_RESULTS.md).

**Phase 3 boundary:** one educational Nangate45 typical-corner experiment, not foundry signoff, multi-corner closure, DRC/LVS signoff, IR-drop/EM closure, or manufacturing readiness. The optional ORFS Kepler-based internal netlist LEC is disabled; the separate bounded RTL proof does not replace netlist-to-netlist LEC across physical optimization stages.

## Current release boundary

The v0.4.0 candidate currently includes Phase 1 diagnostics, bounded Phase 2 verification/QoR implementation, and an experimentally validated single-corner Phase 3 physical flow. Phase 3 evidence provenance, netlist matching, netlist-level equivalence, timing-closure sweeps and variance studies remain under audit. Multi-corner analysis, a second library, reviewed fail-closed QoR thresholds, parameter sweeps, and stronger formal coverage remain future work. FIFO and MAC are functional-only extensions and are not part of the GCD STA/physical matrix. No signoff claim is made.

## Execution policy

Do not mark an item complete because a script exists or a CI job passed once. Require a test or report that directly exercises the behavior, retain raw evidence, and record unsupported capabilities as blocked rather than approximating them.
