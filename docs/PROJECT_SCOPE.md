# Project scope and benchmark methodology

## Objective

Test whether a timing-constraint review flow identifies a small, explicitly defined set of SDC defects on the GCD benchmark. Keep the golden SDC, mutated SDC, expected finding, and observed tool result separate.

## In scope for v0.2

- Positive primary-clock period and expected clock-port presence.
- Minimum and maximum input-delay coverage for each top-level input group.
- Minimum and maximum output-delay coverage for each top-level output group.
- Presence of setup and hold clock uncertainty assumptions.
- Timing-exception presence and mandatory human review.
- Exact/simple wildcard port-name matching to avoid substring false matches.
- Functional equivalence of two GCD architectures.
- Reproducible synthesis and STA entry points.

## Out of scope

- Full SDC Tcl grammar parsing or semantic elaboration.
- Proving that a false path is functionally or architecturally valid.
- Automatic creation of signoff constraints.
- Full MMMC/PVT signoff, OCV/AOCV/POCV, crosstalk/SI, extracted parasitics, and ECO closure.
- Claims of production qualification or silicon signoff.

## Defect catalog

| ID | Mutation | Expected static finding | Why it matters |
|---|---|---|---|
| M01 | Remove create_clock | TF001 ERROR | Sequential paths may lack a clock relationship |
| M02 | Remove a_in input delay | TF101 ERROR | Input-to-register timing budget is incomplete |
| M03 | Remove gcd_out output delay | TF201 ERROR | Register-to-output timing budget is incomplete |
| M04 | Add broad set_false_path | TF301 REVIEW | A timing exception can exclude paths from analysis |
| M05 | Rename a_in collection to a_input | TF101 ERROR | Similar names must not satisfy port coverage |
| M06 | Remove hold uncertainty | TF402 ERROR | Hold analysis assumptions are incomplete |
| M07 | Set period to zero | TF002 ERROR | A clock period must be positive |

The checker is interface-specific and uses simple line-oriented pattern checks. It requires a positive period on the named clock, setup and hold uncertainty, and both min/max I/O delay patterns; exact/simple wildcard matching is used for the known GCD top-level ports. A PASS means only that its expected patterns were found. It does not prove that the SDC is complete, semantically correct, or appropriate for a real design.

## Experimental protocol

1. Run RTL simulation on both architectures.
2. Run the Python unit tests.
3. Generate each mutation from the golden SDC.
4. Run the static checker on the golden and mutated inputs.
5. If a Liberty library is configured, synthesise the selected top and run OpenSTA on golden/mutated constraints; the Nangate45 matrix script runs both GCD architectures and generates a summary from setup/hold reports.
6. Record tool versions, Liberty/platform, top module, SDC hash, commands, and logs.
7. Compare path coverage and timing results only when the same netlist, Liberty, tool options, and corner assumptions are used.

## Published evidence

The v0.2 baseline and all seven controlled mutations have been evaluated in the successful library-backed CI run:

- [GitHub Actions run #41999231060](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/41999231060) — both the RTL/Python regression job and the Nangate45 library-backed STA job completed successfully.
- [STA matrix artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/41999231060/artifacts/13401821413) — raw timing logs and parsed matrix evidence for both architectures and eight SDC scenarios each.
- [Static benchmark artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/41999231060/artifacts/13402245334) — generated static SDC fault-injection scorecard.
- [Measured results and scenario interpretations](INITIAL_RESULTS.md).

Keep scenario-level values sourced from the generated artifacts and measured-results report. Do not fill gaps with estimates or infer unreported WNS, hold, or unconstrained-path values.
