# TimingForge Portfolio and STA Interview Notes

## Portfolio summary

**TimingForge — Constraint-Aware Static Timing Analysis Benchmark**

Built a reproducible RTL-to-STA learning benchmark using SystemVerilog, Yosys, OpenROAD-integrated OpenSTA and the Nangate45 educational platform. Compared two 32-bit binary-GCD architectures, introduced seven controlled SDC fault patterns, and automated functional regression, constraint checks and a 16-run timing matrix.

### Skills demonstrated

- Static timing analysis: setup, hold, slack, WNS/TNS and path inspection
- SDC constraints: clocks, uncertainty, input/output delays and timing exceptions
- RTL architecture comparison and self-checking SystemVerilog
- Yosys synthesis and standard-cell library-based analysis
- Python automation, report parsing and regression testing
- Evidence-based reporting and explicit disclosure of pre-layout limitations

### Honest project scope

The GCD results use one typical Nangate45 Liberty corner, ideal clocks and no extracted SPEF parasitics. All-path Fmax includes I/O paths and is not an internal architecture-only speed comparison. The combined architecture's register-only minimum-period query is unresolved; do not claim a combined internal Fmax. The combined golden-SDC hold slack is -0.002 ns. This is an educational pre-layout benchmark, not production signoff.

## Interview explanation (60–90 seconds)

"TimingForge is a constraint-aware STA benchmark I built around two 32-bit binary-GCD RTL architectures. I used the same synthesis library and timing constraints for both designs, then introduced seven controlled SDC defects such as a missing clock, missing I/O delays, an incorrect port collection and an unjustified false path. The flow runs Yosys synthesis and OpenROAD-integrated OpenSTA, checks the RTL against a reference model, and produces a 16-run timing matrix. The key lesson is that positive slack alone does not prove timing coverage: missing constraints can leave endpoints unconstrained or hide paths. I also document limitations such as the single typical library corner, ideal clocks and lack of extracted parasitics."

## Core STA interview questions

### 1. What is setup time?

The minimum time data must be stable before the active capture-clock edge. A setup violation means the data arrives too late for the capturing register.

### 2. What is hold time?

The minimum time data must remain stable after the active capture-clock edge. A hold violation means data changes too early.

### 3. What is slack?

For setup, slack is required arrival time minus actual arrival time. Positive slack meets the check; negative slack violates it. Hold uses the corresponding minimum-delay relationship.

### 4. What is WNS versus TNS?

WNS is the worst slack among the analysed checks. TNS is the sum of negative slack across violating endpoints. Always state whether the report is setup or hold.

### 5. Why do input and output delays matter?

They model the external timing budget at the block boundary. Without them, input-to-register or register-to-output paths may be unconstrained or omitted from the intended timing analysis.

### 6. What does a false path do?

It tells STA not to time a selected path. It must be justified by design intent and synchronisation architecture; a broad false path can hide real timing failures.

### 7. What is clock uncertainty?

A margin representing clock jitter and other uncertainty in the clock relationship. Setup and hold uncertainty affect their respective timing budgets.

### 8. Why is a positive setup slack not enough?

Because the path may not have been constrained, a required clock may be missing, or a timing exception may have excluded the path. Review coverage and exceptions as well as slack.

### 9. What is the difference between pre-layout and signoff STA?

Pre-layout analysis lacks final routed interconnect parasitics and realistic propagated clock-tree effects. Signoff uses implementation-specific parasitics, corners, modes and validated constraints.

### 10. What is the most important lesson from TimingForge?

The quality of STA conclusions depends on both timing calculations and constraint completeness. The benchmark tests whether known defects are visible; it does not prove arbitrary SDC files are correct.

## Demonstration checklist

1. Show the two RTL architectures and explain their compare/subtract scheduling.
2. Run `make rtl-test` and `make ip-block-test`.
3. Show the golden SDC and explain the 10 ns clock and interface delays.
4. Show the seven mutations and explain what each one tests.
5. Open a raw OpenSTA report and identify startpoint, endpoint, arrival, required time and slack.
6. Show the parsed 16-run matrix and explain why all-path Fmax is not an internal speed comparison.
7. State the known hold issue and the unresolved combined minimum-period query honestly.
