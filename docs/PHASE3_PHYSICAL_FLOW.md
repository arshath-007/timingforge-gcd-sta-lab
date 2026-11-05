# Phase 3 — Nangate45 physical implementation

## Scope

Phase 3 adds a reproducible educational RTL-to-GDS flow for the two GCD architectures using the same pinned OpenROAD Flow Scripts Nangate45 platform as the pre-layout STA matrix.

The intended stages are floorplanning, global placement, clock-tree synthesis, global/detail routing, final database generation, OpenRCX parasitic extraction, KLayout GDS generation, and post-route STA with propagated clocks. The physical CI pins an ORFS container image digest so the source flow, platform files, and tool binaries remain a matched set. The pre-layout matrix is regenerated inside that same job from the exact bundled Nangate45 Liberty/LEF files before physical implementation.

## Run

Use the pinned OpenROAD Flow Scripts container or a compatible installation:

```bash
source /OpenROAD-flow-scripts/env.sh
bash scripts/run_physical.sh
```

The script builds both `gcd_binary_combined` and `gcd_binary_split` with matched floorplan and baseline SDC settings. It records tool versions, pinned container digest, ORFS source revision when available, Liberty/LEF hashes, and SDC hash under `build/physical/`.

## Required evidence

For each architecture the flow must produce:

- `2_floorplan.odb`
- `3_place.odb`
- `4_cts.odb`
- `5_route.odb`
- `6_final.odb`
- `6_final.gds`
- `6_final.spef`
- `6_final.sdc`
- post-route STA log showing the extracted SPEF was loaded and propagated-clock reports were generated

`tools.physical_manifest` checks these files and writes a SHA-256 manifest. CI retains the raw physical outputs and reports as a 90-day artifact.

The runner uses `set -euo pipefail` and invokes the ORFS `make all` target followed by the explicit `gds` target for each design; a nonzero Make/ORFS stage result aborts the script. It then checks that the required intermediate/final databases, GDS, SPEF and SDC exist and verifies the post-route log's SPEF-loaded marker. In the archived run, the ORFS stage JSON reports zero flow errors for the recorded floorplan/place/CTS/global-route/detail-route/final stages, and detailed routing's internal DRC error count converges to zero by its final iteration. These are flow-completion and router checks, **not** foundry DRC/LVS signoff or proof of manufacturing rule closure.

## Interpretation limits

This is an educational Nangate45 typical-corner implementation, not foundry signoff. A successful flow does not establish manufacturing readiness, multi-corner closure, IR-drop/EM closure, DRC/LVS signoff, or silicon quality. The baseline block-level SDC is retained to support a controlled pre-layout/post-layout experiment; it is an illustrative interface budget, not a production timing contract.

No second library or multi-corner result is claimed. Add those only after independently validating distinct Liberty corner models, units, licenses, and platform mappings.


### Internal ORFS LEC boundary

The physical CI sets `LEC_CHECK=0` because the container's optional Kepler-based LEC child process intermittently terminates with an illegal-instruction signal during CTS timing repair. This does not disable CTS, timing repair, SPEF extraction, or post-route STA. The project runs a separate bounded RTL transaction-equivalence proof in Phase 2. Consequently, the physical flow does not claim a netlist-to-netlist LEC result across ORFS optimization stages; that check remains a documented limitation.

## Latest validated run

The current implementation was exercised successfully in [physical-design workflow run #23](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957456). Its [90-day evidence artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957456/artifacts/13439243211) contains the raw stage outputs, final databases, GDS, extracted SPEF, post-route timing logs, comparison JSON and SHA-256 manifest.

See [Phase 3 measured results](PHASE3_RESULTS.md) for the post-route timing table, matched pre-layout comparison, and interpretation limits.
