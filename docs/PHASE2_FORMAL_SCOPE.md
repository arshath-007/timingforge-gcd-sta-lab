# Phase 2 formal proof — scope and interpretation

The first formal property set compares the two GCD architectures at the transaction boundary. It does not require their `done` pulses to occur on the same cycle because the split architecture intentionally has additional processing latency.

- Width: 4 bits.
- Inputs: symbolic constants, so the proof considers every 4-bit input pair, including zero and equal operands.
- Stimulus: one reset followed by one accepted start request.
- Assertions: each implementation completes once, reports `done` with `busy` low, both complete within the 24-cycle bound, and their captured GCD results match.
- Engine: Yosys SMT2 export plus `yosys-smtbmc` and Z3 (CI default).
- Bound: 18 SMT steps.

This is a bounded sequential-equivalence property set for WIDTH=4. It is not a proof for all 32-bit inputs, not an unbounded induction proof, and not a proof of PPA equivalence. The 32-bit design remains covered by simulation regression and will need a separately justified formal bound or a stronger proof strategy.
