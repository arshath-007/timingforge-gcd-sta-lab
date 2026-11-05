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

The checker is interface-specific and uses simple line-oriented pattern checks. A PASS means only that its expected patterns were found. It does not prove that the SDC is complete, semantically correct, or appropriate for a real design.

## Experimental protocol

1. Run RTL simulation on both architectures.
2. Run the Python unit tests.
3. Generate each mutation from the golden SDC.
4. Run the static checker on the golden and mutated inputs.
5. If a Liberty library is configured, synthesise the selected top and run OpenSTA on golden/mutated constraints.
6. Record tool versions, Liberty/platform, top module, SDC hash, commands, and logs.
7. Compare path coverage and timing results only when the same netlist, Liberty, tool options, and corner assumptions are used.

## Evidence table (fill only from actual runs)

| Scenario | Checker result | Setup WNS | Hold WNS | Unconstrained paths | Tool/platform |
|---|---|---:|---:|---:|---|
| Golden | Pending | Pending | Pending | Pending | Pending |
| M01 | Pending | Pending | Pending | Pending | Pending |
| M02 | Pending | Pending | Pending | Pending | Pending |
| M03 | Pending | Pending | Pending | Pending | Pending |
| M04 | Pending | Pending | Pending | Pending | Pending |
| M05 | Pending | Pending | Pending | Pending | Pending |
| M06 | Pending | Pending | Pending | Pending | Pending |
| M07 | Pending | Pending | Pending | Pending | Pending |

Do not replace Pending with estimated or fabricated numbers.
