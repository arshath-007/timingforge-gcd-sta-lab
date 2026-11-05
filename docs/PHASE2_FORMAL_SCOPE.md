# Phase 2 formal proof — scope and interpretation

The first formal property set compares the two GCD architectures at the transaction boundary. It does not require their `done` pulses to occur on the same cycle because the split architecture intentionally has additional processing latency.

- Width: 3 bits.
- Inputs: symbolic constants, so the proof considers every 3-bit input pair, including zero and equal operands.
- Stimulus: one reset followed by one accepted start request.
- Assertions: each implementation completes once, reports `done` with `busy` low, both complete within the 12-cycle bound, and their captured GCD results match.
- Engine: Yosys SMT2 export plus `yosys-smtbmc` and CVC5 (CI default).
- Bound: 26 SMT steps (12 positive clock edges).

## Why WIDTH=3 was selected

WIDTH=3 is the practical bounded-proof configuration retained in the current CI flow, not a mathematically sufficient width for the 32-bit design. The PR implementation history records iterations at widths 8, 6, 4 and finally 3, alongside changes to the SMT solver, proof depth and clock-modeling approach. The current repository does not preserve a complete benchmark table explaining the runtime or failure mode of every earlier configuration, so we do not claim that WIDTH=3 is the smallest possible proof or that wider proofs are impossible.

The three-bit symbolic input space contains all 64 operand pairs. Exhausting those pairs is useful for checking the transaction-level relationship between the two implementations over a compact input domain, including zero and equal operands. It does **not** prove 32-bit arithmetic correctness, rule out width-dependent datapath defects, establish an unbounded sequential invariant, or cover arbitrary back-to-back transactions. The matching high-level controller intent across parameter values is context, not a substitute for a 32-bit proof.

A further distinction: the miter checks **mutual transaction-result equivalence between the combined and split implementations**. It does not compare either implementation against an independent mathematical GCD specification. The separate 32-bit simulation testbench supplies that independent Euclidean-algorithm reference check for its finite directed/seeded corpus; it is simulation evidence, not a formal proof of the full 32-bit input space.

The 32-bit implementations are separately exercised by directed and seeded constrained-random simulation. That is complementary evidence, not equivalent to formal proof. A future stronger result should use a scalable proof strategy (for example, width-parameterized invariants or compositional datapath/control properties) and retain its own reproducible CI evidence.

This is a bounded sequential-equivalence property set for WIDTH=3. It is not a proof for all 32-bit inputs, not an unbounded induction proof, and not a proof of PPA equivalence. The 32-bit design remains covered by simulation regression and will need a separately justified formal bound or a stronger proof strategy.

## Assertion support matrix

| Tool path | Assertion form | Status |
|---|---|---|
| Yosys 0.33 `read_verilog -formal -sv` + `yosys-smtbmc` | Immediate SystemVerilog `assert` statements in the sequential miter | Executed by CI |
| Icarus Verilog RTL regression | Procedural testbench checks for transaction completion, pulse behavior, and result agreement | Executed by CI |
| Concurrent `assert property` SVA syntax | Not used in this flow; the selected open-source frontend path does not provide the required concurrent-SVA support | Explicit limitation |

The property set is deliberately written in the immediate-assertion subset supported by the pinned Yosys flow. Do not describe the current result as a concurrent-SVA proof.

## Clock and bound semantics

The formal harness uses a `(* gclk *)` clock initialized low and preserves native positive-edge sequential semantics. Do not apply `clk2fflogic` to this harness: lowering the clock to a global-step FF model changes the sampling relationship between the DUT's registered `done` pulse and the miter's `seen` flags. The 26-step SMT bound covers the harness through its explicit 12-cycle completion assertion at WIDTH=3. The proof remains bounded and does not establish equivalence for 32-bit inputs or arbitrary transaction sequences.
