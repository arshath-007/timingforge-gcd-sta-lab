# Phase 2 formal and assertion evidence — scope and interpretation

The bounded formal miter checks mutual architecture equivalence, one completion per implementation, `done` with `busy` low, and completion within 12 positive clock edges. It does not prove either implementation against a mathematical GCD specification. A separate exhaustive 64-entry WIDTH=3 truth-table oracle is checked against an independent Euclidean reference in Icarus simulation. The two `done` pulses are not required to occur on the same cycle because the split architecture intentionally has additional processing latency.

- Formal width: 3 bits; all 64 symbolic operand pairs are considered.
- Stimulus: one reset followed by one accepted start request.
- Assertions: each implementation completes once, reports `done` with `busy` low, agrees with the other implementation, and completes within the 12-cycle bound.
- Engine: Yosys SMT2 export plus `yosys-smtbmc` and CVC5.
- Bound: 26 SMT steps (12 positive clock edges).
- Negative control: a deliberately broken subtract operation must fail the same miter.

## What the proof does and does not establish

The WIDTH=3 symbolic input space is exhaustive for 64 input pairs. It checks transaction behavior and mutual result equivalence in a compact domain. The standalone truth-table oracle is separately cross-checked for all 64 pairs by Icarus simulation. It does **not** prove 32-bit arithmetic correctness, establish an unbounded sequential invariant, or cover arbitrary back-to-back transactions.

The standalone WIDTH=3 oracle table is separately checked against an independent Euclidean reference for all 64 input pairs. The 32-bit GCD RTL is also checked against an independent Euclidean reference in directed and seeded constrained-random simulation. A new parameterized regression additionally runs both architectures at WIDTH=8, WIDTH=16, and WIDTH=32, with zero/equal/high-bit/stress cases and deterministic random operands. This is simulation evidence, not a proof of the full 32-bit input space.

## Concurrent SVA protocol checks

A separate Verilator assertion regression exercises concurrent SystemVerilog Assertions on both architectures:

- `done |=> !done`: `done` is a one-cycle pulse.
- `done |-> !busy`: `busy` is low when completion is sampled.
- Stimulus includes zero operands, high-bit operands, adjacent high-valued operands, and a nontrivial common divisor.

These properties are dynamically assertion-checked by Verilator. They are **not** part of the Yosys/CVC5 formal proof and do not establish unbounded formal properties. The formal miter itself uses the immediate-assertion subset supported by the selected Yosys frontend.

## QoR regression gate

A reviewed Nangate45 typical-corner baseline is checked into `baselines/nangate45_qor_baseline.json`. CI fails closed if platform revision, corner, Liberty hash, tool versions, golden SDC hash, architecture set, or required metrics differ. The policy allows at most 8% cell-area growth, 8% all-path minimum-period growth, 0.25 ns setup-slack loss, and 0.02 ns hold-slack loss versus that baseline.

The baseline is intentionally environment-specific. A tool/library update requires a reviewed new baseline and archived evidence; it must not be silently accepted. These thresholds are regression guardrails for this educational benchmark, not universal signoff limits.

## Clock and bound semantics

The formal harness uses a `(* gclk *)` clock initialized low and preserves native positive-edge sequential semantics. Do not apply `clk2fflogic` to this harness: lowering the clock to a global-step FF model changes the sampling relationship between the DUT's registered `done` pulse and the miter's `seen` flags. The proof remains bounded and does not establish arbitrary transaction sequences or full-width formal correctness.
