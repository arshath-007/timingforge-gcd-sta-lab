# Learning path: from GCD RTL to timing closure

## Stage 1 — Understand the benchmark

Know the module interface, reset behaviour, start/done handshake, and binary-GCD algorithm. Run the testbench before looking at synthesis.

## Stage 2 — Read the SDC

Understand:
- create_clock: defines the clock period and source.
- set_clock_uncertainty: reserves timing margin.
- set_input_delay: models external input arrival relative to the clock.
- set_output_delay: models the external output timing budget.
- set_input_transition and set_load: model interface electrical assumptions.

These values are illustrative teaching assumptions. Never copy them into another design without deriving the real interface budget.

## Stage 3 — Understand STA reports

Learn launch/capture clocks, arrival time, required time, setup slack, hold slack, WNS, TNS, endpoint, startpoint, and unconstrained paths. Explain one path in your own words before attempting optimisation.

## Stage 4 — Compare architectures

The split architecture registers the comparison decision and uses a later subtraction cycle. It may shorten a combinational path but increases operation latency. Measure cell area, logic depth, timing, and cycles rather than assuming a winner.

## Stage 5 — Grow toward signoff methodology

After the single-clock experiment works, study generated clocks, clock groups, multicycle paths, false paths, min/max corners, propagated clocks, uncertainty, derates, on-chip variation, parasitics, SI, and timing ECOs.

## Beginner rule

A tool reporting no violation is not the same as proving the design is correctly constrained. Always inspect unconstrained endpoints and constraint coverage.
