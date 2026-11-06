# Phase 2 formal and assertion evidence — scope and interpretation

**Latest PR validation:** the updated oracle-backed miter passed in [formal workflow run #42098727465](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727465); download the [formal proof artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727465/artifacts/13449462598). The positive CVC5 proof passed at 26 SMT steps / 12 positive clock edges (11:08 solver time). The intentionally broken subtract mutant was rejected at step 5 for operands a=5, b=3. Main-branch validation remains part of the v0.4.0 release gate.

The bounded formal miter now checks each GCD architecture against an independent WIDTH=3 mathematical truth-table oracle, checks mutual architecture-result equivalence, verifies one completion per implementation, checks `done` with `busy` low, and requires completion within 12 positive clock edges. The 64-entry oracle is independently cross-checked against Python's Euclidean `math.gcd` and an Icarus simulation. The two `done` pulses are not required to occur on the same cycle because the split architecture intentionally has additional processing latency.

- Formal width: 3 bits; all 64 symbolic operand pairs are considered.
- Stimulus: one reset followed by one accepted start request.
- Correctness assertions: both architectures' completed results equal the independent WIDTH=3 oracle.
- Protocol assertions: each implementation completes once, reports `done` with `busy` low, and completes within the 12-cycle bound.
- Equivalence assertion: captured transaction results from both architectures match.
- Engine: Yosys SMT2 export plus `yosys-smtbmc` and CVC5.
- Bound: 26 SMT steps (12 positive clock edges).
- Negative control: a deliberately broken subtract operation must fail the same oracle-backed miter.

## What the proof does and does not establish

The WIDTH=3 symbolic input space is exhaustive for all 64 operand pairs. Unlike a pure mutual-equivalence miter, this proof checks both implementations against a separate mathematical oracle, so a shared arithmetic defect cannot pass merely because the architectures agree. The oracle table itself is checked against `math.gcd` by a Python unit test and against an independently coded Euclidean reference in Icarus simulation.

This still does **not** prove 32-bit arithmetic correctness, establish an unbounded sequential invariant, or cover arbitrary back-to-back transactions. The 32-bit GCD RTL is separately checked against an independent Euclidean reference in directed and seeded constrained-random simulation. Parameterized regression also runs both architectures at WIDTH=8, WIDTH=16, and WIDTH=32, with zero/equal/high-bit/stress cases and deterministic random operands. These are simulation checks, not proofs of the full 32-bit input space.

## Concurrent SVA protocol checks

A separate Verilator assertion regression exercises concurrent SystemVerilog Assertions on both architectures:

- `done |=> !done`: `done` is a one-cycle pulse.
- `done |-> !busy`: `busy` is low when completion is sampled.
- Stimulus includes zero operands, high-bit operands, adjacent high-valued operands, and a nontrivial common divisor.

These properties are dynamically assertion-checked by Verilator. They are **not** part of the Yosys/CVC5 bounded proof and do not establish unbounded formal properties. The formal miter uses the immediate-assertion subset supported by the selected Yosys frontend.


## Additional negative-control and exhaustive simulation evidence

The repository's full formal script retains four additional, deliberately broken WIDTH=3 RTL negative controls: a single-architecture subtraction fault, a shared zero-input fault, a shared common-shift fault, and a truncated comparator. Each must be rejected by the same oracle-backed miter. Separately, `scripts/run_exhaustive_gcd.sh` exhaustively simulates all 65,536 WIDTH=8 operand pairs against an independent Euclidean reference for both architectures. That WIDTH=8 result is exhaustive simulation, not an SMT proof or a 32-bit formal proof. The WIDTH=8/16/32 regression sweep and Verilator SVA checks remain dynamic evidence.

## QoR regression gate

A reviewed Nangate45 typical-corner baseline is checked into `baselines/nangate45_qor_baseline.json`. CI fails closed if platform revision, corner, Liberty hash, tool versions, golden SDC hash, architecture set, or required metrics differ. The policy allows at most 8% cell-area growth, 8% all-path minimum-period growth, 0.25 ns setup-slack loss, and 0.02 ns hold-slack loss versus that baseline.

The baseline is intentionally environment-specific. A tool/library update requires a reviewed new baseline and archived evidence; it must not be silently accepted. These thresholds are regression guardrails for this educational benchmark, not universal signoff limits.

## Clock and bound semantics

The formal harness uses a `(* gclk *)` clock initialized low and preserves native positive-edge sequential semantics. Do not apply `clk2fflogic` to this harness: lowering the clock to a global-step FF model changes the sampling relationship between the DUT's registered `done` pulse and the miter's `seen` flags. The proof remains bounded and does not establish arbitrary transaction sequences or full-width formal correctness.
