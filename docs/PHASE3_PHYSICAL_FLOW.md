# Phase 3 — Nangate45 physical implementation

## Scope

Phase 3 adds a reproducible educational RTL-to-GDS flow for the two GCD architectures using the same pinned OpenROAD Flow Scripts Nangate45 platform as the pre-layout STA matrix.

The intended stages are floorplanning, global placement, clock-tree synthesis, global/detail routing, final database generation, OpenRCX parasitic extraction, KLayout GDS generation, and post-route STA with propagated clocks. KLayout batch validation then checks that the GDS is readable, contains the expected top cell, has a non-empty bounding box, and contains geometry. This is a structural GDS sanity check, not foundry DRC or LVS signoff. The physical CI pins an ORFS container image digest so the source flow, platform files, and tool binaries remain a matched set. The pre-layout matrix is regenerated inside that same job from the exact bundled Nangate45 Liberty/LEF files before physical implementation. However, pre-layout Yosys synthesis and ORFS synthesis use different configurations; the resulting netlists are not proven identical. The cross-stage comparison must therefore be interpreted as observational, not as a pure routing-parasitic delta.

## Run

Use the pinned OpenROAD Flow Scripts container or a compatible installation:

```bash
source /OpenROAD-flow-scripts/env.sh
export ORFS_IMAGE_DIGEST=sha256:f05cee3219a02f26289f02f00e11a3fc986ab51a482a0000a2da810cda219a6e
bash scripts/run_physical.sh
```

The script derives the repository root from its own path and exports `DESIGN_REPO_ROOT` for the ORFS configs, avoiding an undeclared `GITHUB_WORKSPACE` dependency. It records the source Git SHA, RTL/script/SDC hashes, tool versions, workflow-declared container digest, ORFS source revision when available, and Liberty/LEF hashes under `build/physical/`. The digest is recorded as workflow-declared provenance rather than independently measured from inside the container. The runner requires the caller to supply this exact digest and rejects a missing or different declaration; GitHub Actions enforces the actual container image reference by pulling the digest-pinned image. A local shell cannot independently attest the container runtime's image digest, so the local environment must be verified by the operator.

## Required evidence

For each architecture the flow must produce:

- `2_floorplan.odb`
- `3_place.odb`
- `4_cts.odb`
- `5_route.odb`
- `6_final.odb`
- `6_final.gds` plus `gds_validation.json` confirming KLayout read/top-cell/geometry checks
- `6_final.spef`
- `6_final.sdc`
- post-route STA log showing the extracted SPEF was loaded and propagated-clock reports were generated

`tools.physical_manifest` checks these files and writes a SHA-256 manifest. CI retains the raw physical outputs and reports as a 90-day artifact.

The runner uses `set -euo pipefail` and invokes the ORFS `make all` target followed by the explicit `gds` target for each design; a nonzero Make/ORFS stage result aborts the script. It then checks that the required intermediate/final databases, GDS, SPEF and SDC exist and verifies the post-route log's SPEF-loaded marker. In the archived run, the ORFS stage JSON reports zero flow errors for the recorded floorplan/place/CTS/global-route/detail-route/final stages, and detailed routing's internal DRC error count converges to zero by its final iteration. These are flow-completion and router checks, **not** foundry DRC/LVS signoff or proof of manufacturing rule closure.

## Interpretation limits

This is an educational Nangate45 typical-corner implementation, not foundry signoff. A successful flow does not establish manufacturing readiness, multi-corner closure, IR-drop/EM closure, DRC/LVS signoff, or silicon quality. The baseline block-level SDC is retained to support a controlled pre-layout/post-layout experiment; it is an illustrative interface budget, not a production timing contract.

This document covers only the Nangate45 typical-corner flow. The separately validated ASAP7 BC/TC/WC MCMM and SKY130HD TT experiments are documented in [technology-breadth methodology](PHASE3_TECHNOLOGY_BREADTH.md) and [measured technology-breadth results](PHASE3_TECHNOLOGY_BREADTH_RESULTS.md). The separate [physical robustness study](PHYSICAL_ROBUSTNESS.md) records placement/utilization variation and a target-period closure sweep. These are educational experiments and do not establish foundry signoff.


### Internal ORFS LEC boundary

The physical CI sets `LEC_CHECK=0` because the container's optional Kepler-based LEC child process intermittently terminates with an illegal-instruction signal during CTS timing repair. This does not disable CTS, timing repair, SPEF extraction, or post-route STA. The project runs a separate bounded RTL transaction-equivalence proof in Phase 2. Consequently, the physical flow does not claim a netlist-to-netlist LEC result across ORFS optimization stages; that check remains a documented limitation.

## Latest validated run

The earlier [physical-design workflow run #23](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957456) ran on PR #6 merge SHA `4686342491aeabc5746fecd36f7e33b2d90c8b5b`, not a standalone main commit. New workflow configuration runs on main pushes and version tags and records the exact checked-out SHA. Its [90-day evidence artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957456/artifacts/13439243211) contains the raw stage outputs, final databases, GDS, extracted SPEF, post-route timing logs, comparison JSON and SHA-256 manifest.

See [Phase 3 measured results](PHASE3_RESULTS.md) for the Nangate45 post-route table and cross-flow comparison caveats; see [technology-breadth methodology](PHASE3_TECHNOLOGY_BREADTH.md), [technology-breadth results](PHASE3_TECHNOLOGY_BREADTH_RESULTS.md), and [physical robustness experiments](PHYSICAL_ROBUSTNESS.md) for the separate multi-platform and variation evidence.
