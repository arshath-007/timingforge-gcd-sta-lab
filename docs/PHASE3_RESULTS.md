# Phase 3 measured results — Nangate45 typical

## Experiment boundary

Both 32-bit GCD RTL architectures were implemented with the pinned OpenROAD Flow Scripts container and Nangate45 typical Liberty/LEF platform. The flow ran floorplanning, placement, clock-tree synthesis, global/detail routing, final database generation, OpenRCX parasitic extraction, KLayout GDS generation, and post-route STA.

Post-route analysis loaded each design's final ODB, final SDC and extracted SPEF, then propagated the clocks. The pre-layout and post-route runs use the same Nangate45 typical corner and source baseline SDC hash, but are **not netlist-matched**: `scripts/synth.sh` and ORFS synthesis use different synthesis settings (`ABC_AREA=1` in ORFS). This is a cross-flow comparison, not an isolated measurement of routing impact. Placement/CTS resizing, buffering, clock skew and parasitics can all contribute; the available evidence does not isolate the cause of the period difference. Source baseline SDC hash:

`e16af6df47394c8f5ea3b5ad8cd8d1cbcfc8d3c5935b9bce40165eb25165279f`

This is an educational single-corner experiment, not foundry signoff or a multi-corner timing-closure claim.

## Post-route timing

| Metric | Combined GCD | Split GCD |
|---|---:|---:|
| Register-to-register minimum period | 0.95 ns | 1.02 ns |
| Register-to-register Fmax | 1048.98 MHz | 984.86 MHz |
| All-path minimum period (includes I/O paths) | 2.13 ns | 2.26 ns |
| All-path Fmax | 469.98 MHz | 442.15 MHz |
| Worst setup slack | +7.872 ns | +7.738 ns |
| Worst hold slack | +0.031 ns | +0.018 ns |
| Setup WNS / TNS | 0.000 / 0.000 ns | 0.000 / 0.000 ns |
| Hold WNS / TNS | 0.000 / 0.000 ns | 0.000 / 0.000 ns |
| Reported setup skew (worst reported path) | +0.16 ns | +0.16 ns |
| Reported hold skew (worst reported path) | -0.06 ns | -0.06 ns |

The register-to-register minimum period and all-path minimum period are different metrics. The all-path metric includes constrained I/O-to-register and register-to-I/O paths; it is not an internal-only clock-frequency result. Fmax values are the reciprocal of the corresponding reported minimum period.

## Architecture conclusion

For this single post-route Nangate45 typical-corner run, the combined architecture ranks ahead on both timing-period measures: 0.95 ns versus 1.02 ns register-to-register, and 2.13 ns versus 2.26 ns all-path. It also has slightly better worst setup and hold slack in this run. The split architecture ranks ahead on post-route standard-cell area: 2502.00 versus 2654.95 area units (about 5.8% lower).

The pre-layout all-path result favours split (2.35 ns versus 2.94 ns), but this includes I/O paths and is sensitive to the interface timing budget. It does not establish that split has a faster internal clock path. The combined pre-layout native register-to-register minimum-period query was unavailable, so no pre-layout register-only ranking can be made.

**Confidence is limited.** These rankings come from one floorplan/placement configuration and one Nangate45 typical corner. They do not establish a robust architecture winner across placement seeds or utilization/density choices. A uniform-random time-per-GCD measure and a placement-variation study are separate experiments; do not infer application throughput from Fmax alone.

The clock-skew numbers above are the values emitted by OpenROAD's `report_clock_skew` for its reported paths, rounded to 0.01 ns. The two designs display the same rounded values, but the archived reports identify different startpoint/endpoint pairs. The ORFS final-stage metrics retain more precision: setup skew is 0.155729 ns for combined and 0.157116 ns for split; the corresponding hold-skew magnitudes are 0.055729 ns and 0.056917 ns. The displayed equality is therefore a rounding coincidence, not evidence that the clock trees or selected paths are identical. These are path-specific reports, not a worst-skew guarantee for every clock sink.

## Pre-layout versus post-route

| Metric | Combined GCD | Split GCD |
|---|---:|---:|
| Pre-layout all-path minimum period | 2.94 ns | 2.35 ns |
| Post-route all-path minimum period | 2.13 ns | 2.26 ns |
| Change in all-path minimum period | -0.81 ns | -0.09 ns |
| Pre-layout worst setup slack | +7.065 ns | +7.650 ns |
| Post-route worst setup slack | +7.872 ns | +7.738 ns |
| Pre-layout worst hold slack | -0.002 ns | +0.005 ns |
| Post-route worst hold slack | +0.031 ns | +0.018 ns |

These changes are observations from this one cross-flow comparison and constraint set, not a matched-netlist experiment. They are not a general claim that routing improves timing; synthesis differences, placement, buffering, CTS, parasitic extraction and timing repair can all influence the final result. The available data does not isolate the contribution of each factor.

## Physical evidence

The successful [physical-design workflow run #23](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957456) uploaded the [90-day physical evidence artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42077957456/artifacts/13439243211).

For each architecture the archive contains:
- Final ODB, GDS, SPEF and SDC.
- Floorplan, placement, CTS, routing and final-stage databases/reports/logs.
- Post-route STA log showing SPEF loading, propagated clocks, setup/hold reports and clock-skew reports.
- SHA-256 manifest entries for the archived physical artifacts.

The original manifest reports 84 files per design. The updated manifest also records the source Git commit, hashes of both RTL files and the key flow/parser scripts, and classifies OpenSTA's unannotated-driver list against the final routed netlist. The archived report's unannotated drivers were classified as dangling cell outputs with no sinks; partially unannotated drivers and any unannotated connected driver cause the evidence gate to fail. This is distinct from claiming that OpenSTA reported zero unannotated driver pins. The workflow-supplied ORFS image digest is labelled as declared provenance; the running container does not independently attest its own registry digest.

### Source SDC versus final exported SDC

The source baseline SDC hash is `e16af6df47394c8f5ea3b5ad8cd8d1cbcfc8d3c5935b9bce40165eb25165279f`. The final `6_final.sdc` files are **not byte-identical** to that source file: OpenROAD's `write_sdc` exports a normalized, expanded constraint view of the implemented design. The archived final-SDC hashes are `17a98c9147a7b576cac50336f34cee4fdfef66ea3d52b3e5baca7c23f1ac4012` (combined) and `a14698163c50396ac5440f716ad493fad05edd7a5f1b82fe232a5337093de802` (split). The exported files expand bus wildcards into individual bit-level input/output delay and load commands and include implementation-stage clock/transition and design-rule settings. This is expected export normalization, not a claim that the source SDC and final SDC have identical hashes. Both the source hash and each final exported-SDC hash are retained in the physical manifest so the exact input and post-implementation constraint artifact remain distinguishable.

## Interpretation and limitations

- The result is for Nangate45 typical only. No distinct slow/fast Liberty PVT models were verified, so multi-corner analysis is not claimed.
- No second technology library, OCV/AOCV/POCV, crosstalk/SI, IR-drop/EM, DRC/LVS signoff, power measurement or manufacturing-readiness claim is made.
- The baseline block-level SDC is illustrative, not a production timing contract.
- The optional ORFS Kepler-based internal LEC subprocess is disabled in this container. The separate Phase 2 bounded RTL transaction-equivalence proof does not establish netlist-to-netlist equivalence across ORFS optimization stages.
- Pre-layout golden STA quality findings remain visible: the combined design has -0.002 ns hold slack, and both architectures have reported transition and capacitance violation records. The post-route metrics are separate measurements and do not erase those baseline findings.
- WNS/TNS can be zero when worst slack is positive; consult worst slack and detailed path reports rather than treating zero WNS as a zero-margin result.

## Reproduction

Use the pinned OpenROAD Flow Scripts environment:

```bash
source /OpenROAD-flow-scripts/env.sh
export ORFS_IMAGE_DIGEST=sha256:f05cee3219a02f26289f02f00e11a3fc986ab51a482a0000a2da810cda219a6e
bash scripts/run_physical.sh
```

The script produces the physical outputs under `build/physical/`, the comparison JSON under `build/physical/physical_comparison.json`, and the SHA-256 manifest under `build/physical/physical_manifest.json`.
