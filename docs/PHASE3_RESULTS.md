# Phase 3 measured results — Nangate45 typical

## Experiment boundary

Both 32-bit GCD RTL architectures were implemented with the pinned OpenROAD Flow Scripts container and Nangate45 typical Liberty/LEF platform. The flow ran floorplanning, placement, clock-tree synthesis, global/detail routing, final database generation, OpenRCX parasitic extraction, KLayout GDS generation, and post-route STA.

Post-route analysis loaded each design's final ODB, final SDC and extracted SPEF, then propagated the clocks. The pre-layout and post-route comparison uses the same Nangate45 typical corner and the same source baseline SDC hash:

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

These changes are observations from this one matched flow and constraint set. They are not a general claim that routing improves timing; placement, buffering, CTS, parasitic extraction and timing repair all influence the final result.

## Physical evidence

The latest PR #8 [physical-design workflow run #42098727330](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727330) uploaded the [90-day physical evidence artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727330/artifacts/13450410051).

For each architecture the archive contains:
- Final ODB, GDS, SPEF and SDC.
- Floorplan, placement, CTS, routing and final-stage databases/reports/logs.
- Post-route STA log showing SPEF loading, propagated clocks, setup/hold reports and clock-skew reports.
- SHA-256 manifest entries for the archived physical artifacts.

The manifest reports 84 files per design. Tool provenance includes OpenROAD 26Q3-1080-gab6fd26351, Yosys 0.68+post, the pinned ORFS container digest, Nangate45 typical Liberty SHA-256, LEF hashes and baseline SDC hash.

### Source SDC versus final exported SDC

The source baseline SDC hash is `e16af6df47394c8f5ea3b5ad8cd8d1cbcfc8d3c5935b9bce40165eb25165279f`. The final `6_final.sdc` files are **not byte-identical** to that source file: OpenROAD's `write_sdc` exports a normalized, expanded constraint view of the implemented design. The archived final-SDC hashes are `17a98c9147a7b576cac50336f34cee4fdfef66ea3d52b3e5baca7c23f1ac4012` (combined) and `a14698163c50396ac5440f716ad493fad05edd7a5f1b82fe232a5337093de802` (split). The exported files expand bus wildcards into individual bit-level input/output delay and load commands and include implementation-stage clock/transition and design-rule settings. This is expected export normalization, not a claim that the source SDC and final SDC have identical hashes. Both the source hash and each final exported-SDC hash are retained in the physical manifest so the exact input and post-implementation constraint artifact remain distinguishable.

## Interpretation and limitations

- This measured result is for the Nangate45 typical baseline only. The separate ASAP7 BC/TC/WC and SKY130HD TT experiments are documented in [technology-breadth results](PHASE3_TECHNOLOGY_BREADTH_RESULTS.md); they use different platform assumptions and do not alter this table.
- No corner-specific RC extraction/scaling, OCV/AOCV/POCV, crosstalk/SI, IR-drop/EM, DRC/LVS signoff, power measurement or manufacturing-readiness claim is made.
- The baseline block-level SDC is illustrative, not a production timing contract.
- The optional ORFS Kepler-based internal LEC subprocess is disabled in this container. The separate Phase 2 bounded RTL transaction-equivalence proof does not establish netlist-to-netlist equivalence across ORFS optimization stages.
- Pre-layout golden STA quality findings remain visible: the combined design has -0.002 ns hold slack, and both architectures have reported transition and capacitance violation records. The post-route metrics are separate measurements and do not erase those baseline findings.
- WNS/TNS can be zero when worst slack is positive; consult worst slack and detailed path reports rather than treating zero WNS as a zero-margin result.

See the separate [Phase 3 technology-breadth results](PHASE3_TECHNOLOGY_BREADTH_RESULTS.md) for ASAP7 BC/TC/WC MCMM and SKY130HD TT experiments; those results are not mixed into this Nangate45 table.

## Reproduction

Use the pinned OpenROAD Flow Scripts environment:

```bash
source /OpenROAD-flow-scripts/env.sh
bash scripts/run_physical.sh
```

The script produces the physical outputs under `build/physical/`, the comparison JSON under `build/physical/physical_comparison.json`, and the SHA-256 manifest under `build/physical/physical_manifest.json`.
