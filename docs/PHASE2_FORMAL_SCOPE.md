# Phase 2 formal and assertion evidence — scope and interpretation

The current release-candidate proof evidence is linked from the [v0.4.0 release notes](RELEASE_NOTES_v0.4.0.md). Historical feature-branch run IDs are intentionally omitted here so this scope document does not imply that an earlier PR run validates the current source.

The bounded formal miter checks each GCD architecture against an independent WIDTH=3 mathematical truth-table oracle, checks mutual architecture-result matching, verifies one completion per implementation, checks `done` with `busy` low, and requires completion within 12 positive clock edges. The 64-entry oracle is independently cross-checked against Python's Euclidean `math.gcd` and an Icarus simulation. The two `done` pulses are not required to occur on the same cycle because the split architecture intentionally has additional processing latency.

- Formal width: 3 bits; all 64 symbolic operand pairs are considered.
- Formal stimulus: one reset followed by one accepted start request.
- Correctness assertions: both architectures' completed results equal the independent WIDTH=3 oracle.
- Protocol assertions inside the bounded miter: each implementation completes once, reports `done` with `busy` low, and completes within the 12-cycle bound.
- Result matching: captured transaction results from both architectures match. This is oracle-mediated result matching, not a direct cycle-by-cycle state-equivalence proof.
- Engine: Yosys SMT2 export plus `yosys-smtbmc` and CVC5, invoked directly by `scripts/run_formal.sh`. There is no SymbiYosys `.sby` configuration in this flow.
- Bound: 26 SMT steps (12 positive clock edges), as recorded by the formal runner's bounded configuration.
- Negative controls: four deliberately faulty WIDTH=3 RTL variants must produce an assertion failure.

## Reproduce the bounded proof

From the repository root, use a Linux environment with Bash, GNU coreutils (including `timeout`), Python 3, Icarus Verilog (`iverilog` and `vvp`), Yosys 0.33 with `yosys-smtbmc`, and CVC5 1.1.2. The runner checks the exact Yosys and CVC5 version strings and exits if they differ.

```bash
# Install the distribution packages where available; pin/verify versions below.
sudo apt-get update
sudo apt-get install -y yosys cvc5 iverilog python3
yosys -V
cvc5 --version
command -v yosys-smtbmc
command -v timeout

# Run the complete formal suite: positive proof, four formal negative controls,
# and the WIDTH=8 exhaustive-simulation negative control.
bash scripts/run_formal.sh

# Run the separate directed protocol simulation (busy-start and reset-abort).
bash scripts/run_protocol_regression.sh
```

The checked-in GitHub Actions workflow `.github/workflows/formal-equivalence.yml` is the reference CI environment and installs the expected Yosys/CVC5 versions on `ubuntu-24.04`. The script records tool versions and solver timings under `build/formal/`; CI uploads those files together with protocol evidence as the `timingforge-formal-proof` artifact. For a locally reproduced result, retain the complete `build/formal/` directory and record `git rev-parse HEAD` alongside it. A successful local run is evidence only for that exact checked-out source revision.

## What the proof does and does not establish

The WIDTH=3 symbolic input space is exhaustive for all 64 operand pairs. Unlike a pure mutual-equivalence miter, this proof checks both implementations against a separate mathematical oracle, so a shared arithmetic defect cannot pass merely because the architectures agree. The oracle table itself is checked against `math.gcd` by a Python unit test and against an independently coded Euclidean reference in Icarus simulation.

This does **not** prove 32-bit arithmetic correctness, establish an unbounded sequential invariant, or cover arbitrary transaction sequences. The 32-bit GCD RTL is separately checked against an independent Euclidean reference in directed and seeded constrained-random simulation. Parameterized regression also runs both architectures at WIDTH=8, WIDTH=16, and WIDTH=32, with zero/equal/high-bit/stress cases and deterministic random operands. These are simulation checks, not proofs of the full 32-bit input space.

## Protocol coverage: formal versus simulation

The bounded formal miter stimulates exactly one accepted transaction. It does not formally cover a start pulse while busy, reset asserted during an iterative operation, or a subsequent transaction after completion/reset.

A new directed Icarus regression, `scripts/run_protocol_regression.sh`, exercises both architectures for:
- a second start pulse while both implementations are busy (the request must be ignored);
- reset during an iterative operation (the operation must abort and both engines return to idle);
- a fresh request after completion and after reset-abort.

These are directed simulation checks, not formal proofs. The existing Verilator concurrent SVA regression checks only:
- `done |=> !done`: `done` is a one-cycle pulse.
- `done |-> !busy`: `busy` is low when completion is sampled.

The SVA properties are dynamically assertion-checked by Verilator. They are **not** part of the Yosys/CVC5 bounded proof and do not establish unbounded formal properties.

## Negative-control inventory and N5 distinction

The formal mutant generator `tools/make_formal_mutants.py` defines exactly four formal mutants:
- N1: single-architecture subtraction fault;
- N3: shared zero-input fault;
- N4: shared common-shift fault;
- N6: truncated comparator.

N2 and N5 are not defined by that formal mutant generator. N2 has no implementation or validation evidence in this revision; it is not counted among the four formal controls. N5 is separately generated and tested by `scripts/run_exhaustive_gcd.sh`: the script forces `SHIFT_WIDTH = 2` in both WIDTH=8 designs and requires the exhaustive reference simulation to reject the mutant. N5 is therefore an exhaustive-simulation negative control, not a fifth formal negative control. The formal runner now distinguishes an actual solver-reported assertion failure from solver/tool execution errors and from a mutant that incorrectly passes.

## Parameter contract

Both RTL modules are intended for positive integer widths (WIDTH >= 1). The supported regression points are WIDTH=3 for bounded formal and WIDTH=8/16/32 for simulation. A WIDTH=0 instantiation is outside the documented interface contract and is not currently protected by a portable elaboration-time assertion; add one only with toolchain-compatible elaboration tests.

## QoR regression gate

A reviewed Nangate45 typical-corner baseline is checked into `baselines/nangate45_qor_baseline.json`. CI fails closed if platform revision, corner, Liberty hash, tool versions, golden SDC hash, architecture set, or required metrics differ. The policy allows at most 8% cell-area growth, 8% all-path minimum-period growth, 0.25 ns setup-slack loss, and 0.02 ns hold-slack loss versus that baseline.

The baseline is intentionally environment-specific. A tool/library update requires a reviewed new baseline and archived evidence; it must not be silently accepted. These thresholds are regression guardrails for this educational benchmark, not universal signoff limits.

## Clock and bound semantics

The formal harness uses a `(* gclk *)` clock initialized low and preserves native positive-edge sequential semantics. Do not apply `clk2fflogic` to this harness: lowering the clock to a global-step FF model changes the sampling relationship between the DUT's registered `done` pulse and the miter's `seen` flags. The proof remains bounded and does not establish arbitrary transaction sequences or full-width formal correctness.
