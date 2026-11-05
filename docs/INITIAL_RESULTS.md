# TimingForge v0.2 — Initial measured results

**Status:** Reproducible pre-layout educational experiment  
**Platform:** OpenROAD Flow Scripts Nangate45 typical Liberty  
**Platform source revision:** `11aa833a11488c3a540a1d8eb4caa23fd22df703`  
**Synthesis:** Yosys 0.68+post with Liberty mapping through ABC  
**Timing engine:** OpenROAD-integrated OpenSTA  
**CI evidence:** [Successful library-backed run](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/41999231060)  
**Source commit for the run:** `bd29bcd96914f0415771aa5aa76949cf7163b66e`

## Baseline architecture comparison

The same 32-bit GCD top-level interface and illustrative SDC were used for both architectures. Yosys reported the following Liberty cell-area totals:

| Measurement | Combined compare/subtract | Split compare/subtract |
|---|---:|---:|
| Yosys-reported cell area (Liberty area units) | 1657.180 | 1681.918 |
| Minimum clock period reported | 2.94 ns | 2.35 ns |
| Corresponding reported Fmax | 340.67 MHz | 425.57 MHz |
| Worst setup slack | +7.065 ns | +7.650 ns |
| Setup WNS | 0.000 ns | 0.000 ns |
| Worst hold slack | -0.002 ns | +0.005 ns |
| Hold WNS | -0.002 ns | 0.000 ns |

*The minimum clock periods are displayed to two decimal places; Fmax is calculated from the underlying unrounded period, so recomputing from the displayed value may differ slightly.*

**Observed trade-off in this run:** the split architecture uses about 1.49% more Liberty cell area, while its reported minimum period is about 20.1% lower (reported Fmax about 24.9% higher). However, the self-checking RTL simulation also measured operation latency over the same 258-case corpus:

| Latency measurement | Combined | Split |
|---|---:|---:|
| Average cycles from accepted start to done | 63.63 | 84.17 |
| Maximum cycles in the corpus | 93 | 124 |

The split architecture averages about 32.3% more cycles because it registers the comparison and performs subtraction in a separate state. Multiplying the sample-average cycle count by each architecture's reported minimum clock period gives a rough timing-budget proxy of about 187.1 ns (combined) versus 197.8 ns (split), roughly 5.7% longer for split. This product is only an illustrative proxy—not measured silicon latency—and assumes the same ideal-clock, pre-layout timing model. The key conclusion is that a higher Fmax does not automatically mean lower operation latency.

WNS is zero for the positive setup margins because the report command returns zero when there is no negative slack; the positive margin is shown in the worst-setup-slack column. The combined architecture's baseline hold result is a small negative slack (-0.002 ns), while the split architecture has a small positive margin (+0.005 ns). These are educational pre-layout values, not signoff conclusions.

## What the injected faults demonstrated

The successful matrix ran 8 SDC scenarios for each architecture (16 STA log files total). Download the [raw STA matrix artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/41999231060/artifacts/13401821413) or the [static benchmark artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/41999231060/artifacts/13402245334).

| Mutation | Observed STA evidence | Interpretation |
|---|---|---|
| M01 — missing primary clock | No minimum clock period can be reported; the logs report 138 and 140 unconstrained endpoints for the two architectures. | Without a clock, clocked timing analysis is not meaningful. |
| M02 — missing input delay on `a_in` | The combined design's reported minimum period changes from 2.94 ns to 2.33 ns and the selected setup path shifts to another input (for example, `b_in[19]`). The explicit OpenSTA setup check lists all 32 `a_in` bits as missing `set_input_delay` (32 input ports missing delay). | Removing an input budget can make the reported timing look better by excluding the intended input path. |
| M03 — missing output delay on `gcd_out` | 32 unconstrained endpoints are reported for each architecture, and the explicit setup check reports 32 output ports missing `set_output_delay`. | Output timing coverage is incomplete even though internal clocked paths can still be analysed. |
| M04 — broad register-to-register false path | The dedicated register-to-register setup report says `No paths found.` for the mutated case; the golden report contains register-to-register paths. | A broad exception can remove an entire path class from timing analysis. This mutation is deliberately invalid and exists only in the test suite. |
| M05 — near-match port typo | OpenSTA reports that `a_input*` does not match a design port. | Similar-looking names are not valid substitutes for the actual `a_in` bus. |
| M06 — missing hold uncertainty | Worst hold slack improves by exactly 0.050 ns in both architectures relative to baseline: combined -0.002 to +0.048 ns; split +0.005 to +0.055 ns. | Removing a hold-margin assumption makes the apparent hold result more optimistic. |
| M07 — zero clock period | Worst setup slack becomes -2.935 ns (combined) and -2.350 ns (split), with strongly negative TNS. | A non-positive clock period is invalid and produces a failing timing result. |

The static linter detects seven controlled pattern/coverage defects. The STA run shows why several are important: paths can become unconstrained or disappear, and removing a margin assumption can improve reported slack without changing the RTL.

## Reproduction

Run inside an OpenROAD Flow Scripts environment with Yosys/OpenROAD installed:

```bash
source /OpenROAD-flow-scripts/env.sh
make rtl-test
make python-test
make benchmark
make sta-matrix
```

The matrix script pins the Nangate45 platform files to the source revision listed above and writes raw logs under `build/reports/`, Yosys logs under `build/`, and a generated matrix summary in Markdown/JSON.

## Scope and limitations

- Single typical Liberty corner only; no MMMC analysis.
- No SPEF or extracted interconnect parasitics.
- Clock network is ideal in this pre-layout experiment; no clock-tree synthesis or routed clock effects are represented.
- No routed physical-design result is claimed.
- The 10 ns SDC is an illustrative teaching budget, not a real product interface specification.
- The Python SDC checker is an interface-specific pattern/coverage prototype, not a full Tcl/SDC parser and not proof of constraint correctness.
- A timing exception must be justified by design intent; the tool cannot decide that a false path is valid merely because the command parses.
- The Nangate45 platform is for educational benchmarking, not production signoff or a modern commercial process.
- These results must not be interpreted as silicon performance, power, or production PPA.

The next research stage is to measure the designs after a consistent physical implementation with defined clock-tree and parasitic assumptions, then add more representative blocks (FIFO and MAC) and multi-corner experiments.
