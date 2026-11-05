# TimingForge development phases

This document is the execution tracker for the proposed expansion roadmap. A checkbox is marked complete only when the implementation exists and its stated acceptance evidence is available.

## Phase 1 — Trustworthy analysis and result quality

### Completed in the current main-branch work
- [x] Correct the README roadmap so functional FIFO/MAC blocks are not described as missing.
- [x] Add directed FIFO simultaneous read/write checks at non-full occupancy and while full.
- [x] Add MAC signed-boundary and clear-priority checks.
- [x] Add conservative quality findings for golden STA rows: missing required metrics, non-positive values, unconstrained endpoints, missing I/O delays, negative hold slack, missing register paths, capped path inventories, and unavailable native register-only period.
- [x] Add unit tests for quality-check behavior.
- [x] Run the quality checker in the library-backed STA CI job and upload its JSON findings.

### Phase 1 work completed
- [x] Add heuristic critical-path class labels (input-to-register, register-to-register, register-to-output, input-to-output, or unknown) from OpenSTA startpoint/endpoint names, with unknown fallback and unit tests.
- [x] Add OpenSTA violator-only reports for max transition, max capacitance and max fanout; unsupported reports remain null and empty fanout output is not treated as complete check coverage.
- [x] Add nine clock-constraint sensitivity variants per architecture, derived from the immutable golden SDC, with explicit setup/hold slack deltas and reproducibility metadata.
- [x] Add expected-versus-observed mutation impact scoring with matched, mismatched and inconclusive states; no aggregate accuracy percentage.
- [x] Validate findings against archived raw logs from feature-branch run #257 and post-merge main run #258; both passed both CI jobs.

**Phase 1 exit criteria:** all new checks have unit tests; the full workflow produces machine-readable findings; baseline and mutation behavior is explained; no derived internal Fmax is published without an independently validated method.

**Evidence:** [run #257](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42046659049) and [post-merge run #258](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42047005600), including the [run #258 STA artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42047005600/artifacts/13425391627).

## Phase 2 — Verification depth and QoR analytics

- [ ] Add formal equivalence for the two GCD RTL architectures or a clearly scoped sequential equivalence property set, with tool/version and proof logs.
- [ ] Add SVA properties for GCD invariants and protocol behavior, with a documented simulator/formal support matrix.
- [ ] Add constrained-random tests with reproducible seeds and coverage summaries.
- [ ] Add run-to-run QoR history keyed by source SHA, tool versions, library hash, SDC hash, and scenario.
- [ ] Add suspicious-result regression gates with reviewed thresholds; do not fail builds on noisy or incomparable tool metrics.
- [ ] Add parameter/width sweeps only after the reference model, testbench, synthesis top, and timing constraints are parameter-safe.

**Phase 2 exit criteria:** proofs and tests are reproducible; failures include actionable evidence; QoR comparisons reject mismatched environments instead of producing misleading deltas.

## Phase 3 — Physical implementation and technology breadth

- [ ] Establish a reproducible floorplan and placement flow for the existing GCD designs.
- [ ] Add CTS and propagated-clock timing reports, recording clock insertion delay and skew.
- [ ] Add global/detail routing and extracted parasitics, then run post-route STA.
- [ ] Add multi-corner analysis only after identifying and verifying distinct Liberty process/voltage/temperature models.
- [ ] Add a second technology library only when its source, license, units, corner identity, and mapping compatibility are documented.
- [ ] Compare pre-layout and post-layout results without mixing corners, constraints, or tool versions.

**Phase 3 exit criteria:** raw logs, tool versions, platform files/hashes, constraints, parasitics, and reports are archived; each metric is tied to a named corner and implementation stage; limitations are explicit.

## Current release boundary

The v0.3.0 candidate includes the functional-regression maintenance from the unpublished v0.2.2 candidate plus completed Phase 1 reliability diagnostics. It does not claim that Phase 2 or Phase 3 is complete. FIFO and MAC remain functional-only extensions and are not part of the 16-run GCD STA matrix. The published GCD results remain educational pre-layout Nangate45 typical-corner results with ideal clocks and no extracted SPEF. The combined architecture's native register-only minimum-period query remains unresolved, and the golden-SDC hold slack remains -0.002 ns.

## Execution policy

Do not mark an item complete because a script exists or a CI job passed once. Require a test or report that directly exercises the behavior, retain raw evidence, and record unsupported capabilities as blocked rather than approximating them.
