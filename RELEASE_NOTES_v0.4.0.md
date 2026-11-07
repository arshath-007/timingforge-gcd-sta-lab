# TimingForge v0.4.0 — release notes

## Release candidate source

- Validated source commit: `d6a7247d066e668165a8b4ce0187779fc2ae8164`
- Main-branch validation: all five required GitHub Actions workflows passed.
- Scope: educational RTL-to-STA benchmark; not production or foundry signoff.

## Included capabilities

- Two synthesizable 32-bit iterative binary-GCD RTL architectures.
- Seven controlled SDC fault patterns and a conservative static coverage checker.
- Yosys synthesis and OpenROAD-integrated OpenSTA timing analysis.
- Bounded WIDTH=3 formal equivalence against an independent exhaustive 64-entry GCD oracle, plus dynamic WIDTH=8/16/32 simulation and protocol assertions.
- Fail-closed Nangate45 typical-corner QoR regression checks.
- Nangate45 physical implementation through placement, CTS, routing, extraction and post-route STA.
- ASAP7 BC/TC/WC Liberty-scene analysis and SKY130HD TT physical-flow extension.
- Five paired placement/utilization variants and six target-clock-period robustness sweeps.
- Provenance records, machine-readable summaries, CI evidence artifacts and documented methodology limitations.

## Main-branch validation evidence

| Workflow | Run | Artifact |
|---|---|---|
| RTL regression + library-backed STA | [#42361605851](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605851) | [STA matrix](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605851/artifacts/13569358610), [static scorecard](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605851/artifacts/13570052103) |
| Formal equivalence | [#42361605849](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605849) | [Formal proof](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605849/artifacts/13570052527) |
| Nangate45 physical design | [#42361605868](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605868) | [Physical evidence](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605868/artifacts/13570500287) |
| Technology breadth | [#42361605880](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605880) | [ASAP7/SKY130HD evidence](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605880/artifacts/13570383217) |
| Physical robustness | [#42361605870](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605870) | [Placement and clock-sweep evidence](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42361605870/artifacts/13571333561) |

## Important limitations

- Formal equivalence is bounded to WIDTH=3 and one accepted transaction; it is not an unbounded or all-32-bit proof.
- WIDTH=8/16/32 results are simulation/assertion evidence, not formal proofs.
- The SDC checker recognises a limited, interface-specific subset of SDC/Tcl; it is not a complete parser or signoff checker.
- ASAP7 combined-GCD WC hold slack is -3.225 ps among emitted paths; the same TC-extracted SPEF is reused across BC/TC/WC, and reports are capped at 100 paths per path group.
- SKY130HD coverage is TT-only.
- No OCV/AOCV/POCV, crosstalk/SI, power signoff, IR/EM, foundry DRC/LVS, manufacturing-readiness, or ORFS post-route netlist-to-netlist LEC claim is made.
- Absolute PPA comparisons across Nangate45, ASAP7 and SKY130HD are not apples-to-apples.

## Publication state

This file documents the validated v0.4.0 release candidate. Do not treat the version as published until the `v0.4.0` Git tag and GitHub Release are present.
