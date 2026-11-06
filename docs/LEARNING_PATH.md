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

The split architecture registers the comparison decision and uses a later subtraction cycle. This was a hypothesis for reducing combinational delay, not an established advantage. The available single post-route run measured 1.02 ns register-to-register minimum period for split versus 0.95 ns for combined, while split used fewer standard-cell area units. Compare timing, area, and operation cycles; do not assume the split architecture wins timing.

## Stage 5 — Grow toward signoff methodology

After the single-clock experiment works, study generated clocks, clock groups, multicycle paths, false paths, min/max corners, propagated clocks, uncertainty, derates, on-chip variation, parasitics, SI, and timing ECOs.

## Beginner rule

A tool reporting no violation is not the same as proving the design is correctly constrained. Always inspect unconstrained endpoints and constraint coverage.

## Stage 6 — Reproducible library-backed run

Use the OpenROAD Flow Scripts environment with its Yosys and OpenROAD binaries. Run `make sta-matrix` to map both GCD architectures to the educational Nangate45 typical Liberty library and inspect the baseline and injected-constraint timing logs. Record the tool versions and platform. Do not compare measurements from different libraries or corners as if they were the same experiment.

## Stage 7 — Compare timing with operation latency

A higher reported maximum clock frequency is not automatically higher application throughput. The TimingForge testbench measures cycle count from accepted start to done for both GCD architectures. Use an unbiased uniform-random operand sample and multiply its mean cycle count by the post-route register-only minimum period only as an illustrative proxy. It is not measured silicon latency or a proven worst-case bound.
