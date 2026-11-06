# TimingForge Portfolio Summary and Project Demonstration

## Portfolio summary

**TimingForge — Constraint-Aware Static Timing Analysis Benchmark**

Built a reproducible RTL-to-STA learning benchmark using SystemVerilog, Yosys, OpenROAD-integrated OpenSTA and the Nangate45 educational platform. Compared two 32-bit binary-GCD architectures, introduced seven controlled SDC fault patterns, automated a 16-run timing matrix, added DRV violation reporting, scored mutation impact, and ran 18 clock-constraint sensitivity experiments.

### Skills demonstrated

- Static timing analysis: setup, hold, slack, WNS/TNS and path inspection
- SDC constraints: clocks, uncertainty, input/output delays and timing exceptions
- RTL architecture comparison and self-checking SystemVerilog
- Yosys synthesis and standard-cell library-based analysis
- Python automation, report parsing and regression testing
- Evidence-based reporting, mutation-impact analysis, clock-constraint sensitivity, and explicit disclosure of pre-layout limitations

### Honest project scope

The GCD results use one typical Nangate45 Liberty corner, ideal clocks and no extracted SPEF parasitics. Baseline DRV records include max-slew and max-capacitance violations; the combined golden-SDC hold slack is -0.002 ns. Mutation scoring reports 12 matched, 0 mismatched and 2 inconclusive observations. All-path Fmax includes I/O paths and is not an internal architecture-only speed comparison. The combined architecture's register-only minimum-period query is unresolved; do not claim a combined internal Fmax. This is an educational pre-layout benchmark, not production signoff.

## Project overview

"TimingForge is a constraint-aware STA benchmark I built around two 32-bit binary-GCD RTL architectures. I used the same synthesis library and timing constraints for both designs, then introduced seven controlled SDC defects such as a missing clock, missing I/O delays, an incorrect port collection and an unjustified false path. The flow runs Yosys synthesis and OpenROAD-integrated OpenSTA, checks the RTL against a reference model, and produces a 16-run timing matrix. The key lesson is that positive slack alone does not prove timing coverage: missing constraints can leave endpoints unconstrained or hide paths. I also document limitations such as the single typical library corner, ideal clocks and lack of extracted parasitics."

## Demonstration checklist

1. Show the two RTL architectures and explain their compare/subtract scheduling.
2. Run `make rtl-test` and `make ip-block-test`.
3. Show the golden SDC and explain the 10 ns clock and interface delays.
4. Show the seven mutations and explain what each one tests.
5. Open a raw OpenSTA report and identify startpoint, endpoint, arrival, required time and slack.
6. Show the parsed 16-run matrix and explain why all-path Fmax is not an internal speed comparison.
7. State the known hold issue and the unresolved combined minimum-period query honestly.
