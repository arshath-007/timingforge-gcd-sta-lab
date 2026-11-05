# Phase 2 formal proof — scope and interpretation

The first formal property set compares the two GCD architectures at the transaction boundary. It does not require their `done` pulses to occur on the same cycle because the split architecture intentionally has additional processing latency.

- Width: 4 bits.
- Inputs: symbolic constants, so the proof considers every 4-bit input pair, including zero and equal operands.
- Stimulus: one reset followed by one accepted start request.
- Assertions: each implementation completes once, reports `done` with `busy` low, both complete within the 16-cycle bound, and their captured GCD results match.
- Engine: Yosys SMT2 export plus `yosys-smtbmc` and CVC5 (CI default).
- Bound: 34 SMT steps (16 positive clock edges).

This is a bounded sequential-equivalence property set for WIDTH=4. It is not a proof for all 32-bit inputs, not an unbounded induction proof, and not a proof of PPA equivalence. The 32-bit design remains covered by simulation regression and will need a separately justified formal bound or a stronger proof strategy.

## Assertion support matrix

| Tool path | Assertion form | Status |
|---|---|---|
| Yosys 0.33 `read_verilog -formal -sv` + `yosys-smtbmc` | Immediate SystemVerilog `assert` statements in the sequential miter | Executed by CI |
| Icarus Verilog RTL regression | Procedural testbench checks for transaction completion, pulse behavior, and result agreement | Executed by CI |
| Concurrent `assert property` SVA syntax | Not used in this flow; the selected open-source frontend path does not provide the required concurrent-SVA support | Explicit limitation |

The property set is deliberately written in the immediate-assertion subset supported by the pinned Yosys flow. Do not describe the current result as a concurrent-SVA proof.

## Clock and bound semantics

The formal harness uses a `(* gclk *)` clock initialized low and preserves native positive-edge sequential semantics. Do not apply `clk2fflogic` to this harness: lowering the clock to a global-step FF model changes the sampling relationship between the DUT's registered `done` pulse and the miter's `seen` flags. The 34-step SMT bound provides at least 16 positive clock edges, which is sufficient for the explicit 16-cycle completion assertion at WIDTH=4.
