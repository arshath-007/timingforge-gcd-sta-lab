# TimingForge — interview and project walkthrough

Use this page to prepare to explain the project in your own words. Do not memorise claims you cannot explain. Open the source and the corresponding reports while practising.

## 60–90 second project pitch

"TimingForge is an open-source benchmark I built to study a practical STA methodology problem: a timing report can appear clean even when the SDC is incomplete or a timing exception removes paths from analysis.

I use two synthesizable 32-bit binary-GCD architectures as a controlled RTL benchmark. I generate a golden SDC and seven deliberate constraint mutations, then compare a small static coverage checker with library-backed timing results from Yosys and the OpenROAD-integrated OpenSTA engine using the Nangate45 typical library.

The flow synthesises both architectures and analyses eight constraint scenarios per design, so there are 16 timing runs. It reports cell area, minimum clock period, Fmax, setup and hold slack, missing I/O delay coverage, unconstrained endpoints, and register-to-register path presence.

One finding is that a broad false-path exception removes the register-to-register paths from the dedicated report. Another is that removing the input delay on a 32-bit bus changes the reported critical path and makes the timing result look better. The project reports all-path timing metrics, cell area, and RTL operation cycle counts separately. Because the reported minimum period includes port paths, it does not claim a register-to-register-only architecture speedup.

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

- **Combined:** The odd/odd compare and subtract decision/update occur in one processing state. This keeps the operation cycle count lower in the tested input corpus, but its combinational path can be longer.
- **Split:** The compare result is registered and subtraction occurs in a later state. This can shorten the combinational timing path but costs an extra processing cycle for odd/odd iterations.

In the historical 258-case corpus, combined averaged 63.63 cycles (maximum observed 93); split averaged 84.17 cycles (maximum observed 124). These are finite-corpus observations with a fixed random seed, not proven worst-case latency bounds. In the corrected-load STA run, all-path minimum period/Fmax were 2.940 ns / 340.67 MHz combined and 2.350 ns / 425.57 MHz split. The split design's register-to-register query reported 0.740 ns / 1353.86 MHz; the combined query returned 0.00 ns / infinity and is therefore recorded as n/a. A separate path report still finds register-to-register paths in the combined design. Do not claim the reported all-path Fmax proves a faster internal datapath or higher operation throughput.

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

**What would you do next?**  
Add generated-clock, clock-group and carefully justified multicycle/false-path cases; measure latency over more workloads; add FIFO and MAC benchmarks; then run floorplanning, clock-tree synthesis, routing and extracted-parasitic timing. Finally add multiple process corners and variation assumptions.

## Evidence to open during a walkthrough

- [Repository README](https://github.com/arshath-007/timingforge-gcd-sta-lab)
- [Measured initial results](INITIAL_RESULTS.md)
- [Fault catalog](FAULT_CATALOG.md)
- [RTL architectures](../rtl/)
- [Golden SDC](../constraints/gcd_baseline.sdc)
- [Corrected-load baseline run #144](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42014181193)
- [Latest corrected-load CI validation run #144](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42014181193)
- [Downloadable corrected-load STA logs and matrix](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42014181193/artifacts/13407244466)

Run #144 (ID 42014181193) generated the corrected-load numerical measurements and downloadable STA artifacts; both CI jobs passed on commit `dd1ccbf3a5379cc19fc0788edfb42c6b4f5d18d9`.

## Personal preparation checklist

Before presenting this project, be able to:
- Explain one setup path from startpoint to endpoint.
- Explain why the input delay is part of the required timing model.
- Explain the difference between setup and hold slack.
- Show the baseline versus M02 timing summary.
- Show the register-to-register report before and after M04.
- Explain why all-path Fmax and register-to-register timing are different metrics, and why split uses more cycles in the tested corpus.
- State the Nangate45, pre-layout, no-SPEF limitations without prompting.
