# Phase 3 — Nangate45 physical implementation

## Scope

Phase 3 adds a reproducible educational RTL-to-GDS flow for the two GCD architectures using the same pinned OpenROAD Flow Scripts Nangate45 platform as the pre-layout STA matrix.

The intended stages are floorplanning, global placement, clock-tree synthesis, global/detail routing, final database generation, OpenRCX parasitic extraction, KLayout GDS generation, and post-route STA with propagated clocks. In ORFS, GDS generation is a separate `gds` target after `all`.

## Run

Use the pinned OpenROAD Flow Scripts container or a compatible installation:

```bash
source /OpenROAD-flow-scripts/env.sh
bash scripts/run_physical.sh
```

The script builds both `gcd_binary_combined` and `gcd_binary_split` with matched floorplan and baseline SDC settings. It records tool versions, platform revision, Liberty hash, and SDC hash under `build/physical/`.

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

## Interpretation limits

This is an educational Nangate45 typical-corner implementation, not foundry signoff. A successful flow does not establish manufacturing readiness, multi-corner closure, IR-drop/EM closure, DRC/LVS signoff, or silicon quality. The baseline block-level SDC is retained to support a controlled pre-layout/post-layout experiment; it is an illustrative interface budget, not a production timing contract.

No second library or multi-corner result is claimed. Add those only after independently validating distinct Liberty corner models, units, licenses, and platform mappings.
