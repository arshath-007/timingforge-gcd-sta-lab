# TimingForge — interview and project walkthrough

Use this page to prepare to explain the project in your own words. Do not memorise claims you cannot explain. Open the source and the corresponding reports while practising.

## 60–90 second project pitch

"TimingForge is an open-source benchmark I built to study a practical STA methodology problem: a timing report can appear clean even when the SDC is incomplete or a timing exception removes paths from analysis.

I use two synthesizable 32-bit binary-GCD architectures as a controlled RTL benchmark. I generate a golden SDC and seven deliberate constraint mutations, then compare a small static coverage checker with library-backed timing results from Yosys and the OpenROAD-integrated OpenSTA engine using the Nangate45 typical library.

The flow synthesises both architectures and analyses eight constraint scenarios per design, so there are 16 timing runs. It reports cell area, minimum clock period, Fmax, setup and hold slack, missing I/O delay coverage, unconstrained endpoints, and register-to-register path presence.

One finding is that a broad false-path exception removes register-to-register paths from the dedicated report; another is that removing an input delay can make the reported result look better by changing the constrained path set. The benchmark also includes seven controlled SDC mutations, 18 clock-constraint sensitivity experiments, OpenSTA DRV reporting, bounded WIDTH=3 formal verification against an independent 64-entry GCD oracle, Verilator protocol assertions, WIDTH=8/16/32 simulation, Nangate45 physical implementation, ASAP7 BC/TC/WC Liberty-scene analysis, and SKY130HD TT physical implementation. These are distinct evidence types: the bounded formal proof checks both architectures against the mathematical oracle and against each other for one WIDTH=3 transaction; simulation covers wider widths but is not a 32-bit formal proof. The ASAP7 combined design has -3.225 ps hold slack among the reported WC paths. The Nangate45 combined design also fails the 2.5 ns target closure gate because of a max-capacitance violation (54.633 versus a 53.406 limit, slack -1.227), even though setup and hold slack are non-negative at that point. The ASAP7 path report is capped at 100 paths per path group and is not an exhaustive signoff inventory. The project remains an educational research prototype, not foundry signoff.

The results are educational pre-layout Nangate45 measurements—not production signoff. The next step is multi-corner and physical implementation with realistic clock and parasitic assumptions."

## The engineering question

**How can we test whether the paths we intended to analyse are actually present in an STA run?**

The benchmark separates four things:
1. Design intent and the golden constraint file.
2. A named, controlled SDC mutation.
3. The linter's expected finding.
4. The observed STA result from the same mapped netlist and library.

This separation matters. A pattern checker can flag an obvious defect, but only a timing run can show how the analysed path set and timing results changed. Neither replaces an engineer's review of design intent.

## Key terms to explain

- **STA:** Static timing analysis evaluates timing paths in a gate-level design without simulating every input sequence.
- **SDC:** Synopsys Design Constraints; a Tcl-based format used to describe clocks, I/O timing budgets and timing exceptions.
- **Setup:** Checks whether data arrives early enough before the capture clock edge.
- **Hold:** Checks whether data remains stable long enough after the capture edge.
- **Slack:** Difference between required and actual arrival time. Positive slack meets that individual check; negative slack is a violation.
- **WNS / TNS:** Worst negative slack and total negative slack. In some reports WNS is zero when no negative slack exists; inspect worst slack as well to see positive margin.
- **Unconstrained endpoint:** A path endpoint for which the timing engine does not have enough applicable constraints to perform the intended timing check.
- **False path:** An exception telling STA not to time a path. It must be justified by the design's functional modes and intent; broad exceptions are dangerous.
- **Liberty:** A standard-cell library model containing timing, power and area information for cells.
- **Pre-layout STA:** Timing before extracted interconnect parasitics are included. It does not represent post-route signoff timing.

## How to explain the two GCD architectures

- **Combined:** The odd/odd compare and subtract decision/update occur in one processing state. It uses fewer cycles in the measured input corpus. In the single post-route physical run, it also has the shorter register-to-register minimum period (0.95 ns versus 1.02 ns).
- **Split:** The compare result is registered and subtraction occurs in a later state. This adds processing cycles for odd/odd iterations. The hypothesized shorter combinational path was not supported by the measured post-route register-to-register result in this one physical run.

The pre-layout all-path Fmax favours split (425.57 MHz versus 340.67 MHz), but those figures include I/O paths and depend on external timing constraints. They are not an internal register-to-register comparison. In the single post-route run, combined has the shorter register-only period (0.95 ns versus 1.02 ns) and split has lower standard-cell area (2502.00 versus 2654.95 area units). Treat this as a single-configuration observation, not a robust ranking; placement variation and uniform-random time-per-GCD studies are still needed.

## Questions a reviewer may ask

**Your combined architecture shows -0.002 ns hold slack—isn't that a failing design?**  
Yes. Under this specific ideal-clock, pre-layout model, the combined architecture has a small negative hold slack, so that hold check is a violation; I report it rather than hiding it. The result is not signoff evidence. A physical implementation would need hold analysis with the actual clock-tree and parasitic assumptions, followed by appropriate hold repair and re-verification. I cannot claim that the design is hold-clean from this pre-layout result.

**Why did you choose GCD?**  
It is small enough to understand and verify with a reference algorithm, yet contains comparison, subtraction, shifts, control logic and register feedback. That gives the timing experiment an understandable RTL test vehicle.

**Why inject faults instead of only checking a golden SDC?**  
A checker needs negative tests. Fault injection provides controlled examples with known expected outcomes, so we can ask whether the checker detects each defect and whether STA exposes a path-coverage or slack change.

**Does 7/7 mean the linter is 100% accurate?**  
No. It means it detected the seven deliberately constructed patterns in this prototype. It is not a full SDC parser, does not test arbitrary SDC files and does not prove semantic correctness.

**Why does the false-path test say no register-to-register paths found?**  
The mutation intentionally applies a broad false-path exception from all register outputs to all register data pins. The dedicated report shows the path class has been removed under that mutated constraint. This is a controlled negative test, not a valid production constraint.

**Why can missing an input delay make the result appear better?**  
The input path no longer receives the intended external arrival budget. The reported critical path can shift to another path with a different budget, so the selected timing result may look better even though the model is incomplete.

**What does the Nangate45 result prove?**  
It proves that this RTL and this illustrative SDC were synthesised and analysed in a reproducible educational library-backed flow. It does not prove production process timing, extracted interconnect timing, power, or signoff closure.

**What did the DRV reports reveal?**  
The golden combined architecture produced 10 max-slew and 15 max-capacitance violation records; the split architecture produced 9 and 15 respectively. The violator-only report emitted no max-fanout violation records, but it does not enumerate total applicable checks. I report these as review findings, not as signoff conclusions. Separately, in the physical target-period sweep, combined GCD did not close at 2.500 ns because pin `_3726_/ZN` had 54.633 capacitance against a 53.406 limit (slack -1.227); split GCD closed at 2.500 ns. This target-specific failure is recorded in `docs/PHYSICAL_ROBUSTNESS.md` and is not hidden by the successful ORFS run.

**How did you validate constraint sensitivity?**  
I changed one parameter family at a time from an immutable golden SDC: setup uncertainty (0.100/0.150/0.200 ns), hold uncertainty (0.025/0.050/0.075 ns), and source latency with early fixed at 0 and late at 0/0.050/0.100 ns. Nine variants per architecture produced 18 runs with explicit setup/hold slack deltas and source/tool/library/SDC identity.

**Why are two mutation results inconclusive?**  
M06 removes hold uncertainty, but the current parsed report does not directly expose whether that command was applied. A change in hold slack is evidence of sensitivity, not proof that the uncertainty command was present or absent. The tool therefore records M06 as inconclusive rather than overstating detection.

**What would you do next?**  
Next steps are to investigate and repair the reported ASAP7 WC hold issue and Nangate45 2.5 ns max-capacitance failure, expand timing-path inventory beyond the current 100-per-path-group report cap, add corner-specific RC extraction/scaling and validated variation-aware analysis, and complete fresh post-merge main-branch validation. Do not call the project signoff-clean: the current experiments establish reproducible educational flows, not production closure.

## Evidence to open during a walkthrough

- [Repository README](https://github.com/arshath-007/timingforge-gcd-sta-lab)
- [Measured initial results](INITIAL_RESULTS.md)
- [Fault catalog](FAULT_CATALOG.md)
- [RTL architectures](../rtl/)
- [Golden SDC](../constraints/gcd_baseline.sdc)
- [Phase 1 CI run #257](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42046659049)
- [Post-merge main CI run #258](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42047005600)
- [Phase 1 STA artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42047005600/artifacts/13425391627)
- [Validated baseline CI run #160](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42015328699)
- [Downloadable corrected-load STA matrix](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42015328699/artifacts/13408368824)
- [Downloadable static benchmark](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42015328699/artifacts/13408887449)

Run #160 (ID 42015328699) validated the corrected-load measurements on source commit `bdd42621749035fa088e326c766f3af8031af337`. Both CI jobs passed.

## Phase 2/3 evidence distinctions to explain

- **Formal correctness against the oracle:** the WIDTH=3 miter checks both architectures against a separate 64-entry mathematical GCD table and checks their captured results against each other. This is bounded to 3-bit operands and one accepted transaction.
- **Oracle-table validation:** the Python test parses all 64 explicit truth-table rows, rejects duplicates, and compares the complete mapping with Python `math.gcd`. The regression log also prints: `PASS: exhaustive 3-bit GCD oracle table verified for all 64 operand pairs`.
- **Simulation versus proof:** WIDTH=8/16/32 sweeps and Verilator SVA are dynamic simulation/assertion evidence, not 32-bit or unbounded formal proofs.
- **ASAP7 path inventory:** `report_checks -group_path_count 100` requests up to 100 paths per path group. Results are grouped by path group; the current published slack minima are minima among emitted paths, not an exhaustive signoff inventory. The project does not claim that a capped path report is a complete timing database.
- **ASAP7 RC limitation:** one TC-extracted SPEF is reused unchanged across BC/TC/WC; no corner-specific RC extraction or scaling is performed.
- **Known physical failures:** ASAP7 combined WC reported hold slack is -3.225 ps among the emitted paths. Nangate45 combined GCD is not closed at the 2.500 ns target because of the max-capacitance violation noted above.

## Personal preparation checklist

Before presenting this project, be able to:
- Explain one setup path from startpoint to endpoint.
- Explain why the input delay is part of the required timing model.
- Explain the difference between setup and hold slack.
- Show the baseline versus M02 timing summary.
- Show the register-to-register report before and after M04.
- Explain why all-path Fmax and register-to-register timing are different metrics, and why split uses more cycles in the tested corpus.
- State the Nangate45, pre-layout, no-SPEF limitations without prompting.
