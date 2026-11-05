# Phase 3 technology breadth: ASAP7 MCMM and SKY130HD

## Purpose

The Nangate45 typical-corner flow remains the reference experiment. This extension adds:
1. A post-route, three-scene ASAP7 MCMM analysis for both GCD architectures.
2. A second, independent SKY130HD physical implementation and extracted-parasitic post-route STA for both architectures.

These are separate platform experiments. Absolute PPA numbers must not be ranked across libraries as if the platforms had identical process assumptions, cell architectures, RC models, units, or characterization methodology.

## Pinned platform source

The ORFS platform files are taken from the ORFS source revision pinned by the project container:

- ORFS revision: `11aa833a11488c3a540a1d8eb4caa23fd22df703`
- ASAP7 platform configuration: [platform config](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/blob/11aa833a11488c3a540a1d8eb4caa23fd22df703/flow/platforms/asap7/config.mk)
- SKY130HD platform configuration: [platform config](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/blob/11aa833a11488c3a540a1d8eb4caa23fd22df703/flow/platforms/sky130hd/config.mk)

The manifest records hashes of every Liberty file used, plus the final ODB, GDS, SPEF and SDC files for both designs and platforms. It also records the units reported by OpenSTA and the upstream platform-license references.

## ASAP7 PVT scenes

The ORFS ASAP7 NLDM configuration supplies three distinct PVT model groups:

| Scene | Liberty process model | Temperature | Voltage |
|---|---|---:|---:|
| ASAP7_BC | FF | 25°C | 0.77 V |
| ASAP7_TC | TT | 0°C | 0.70 V |
| ASAP7_WC | SS | 100°C | 0.63 V |

Each scene reads the five RVT NLDM libraries needed by the mapped design (AO, INVBUF, OA, SIMPLE and SEQ). The designs are physically implemented once at TC, with propagated clocks and extracted SPEF. OpenSTA then creates all three scenes in one MCMM session and reports setup, hold, clock skew and design-rule checks per scene. OpenSTA's scene model is documented in the [official OpenSTA examples](https://opensta.readthedocs.io/en/latest/Examples/).

**RC assumption:** the single TC-extracted SPEF is reused unchanged for BC, TC and WC. There is no corner-specific RC extraction or RC scaling in this experiment. The MCMM results therefore isolate the effect of the distinct Liberty PVT timing models under a shared parasitic network; they are not a full foundry-qualified PVT/RC signoff flow.

ASAP7 is a predictive academic platform. Its upstream PDK repository declares BSD-3-Clause licensing ([license](https://github.com/The-OpenROAD-Project/asap7/blob/main/LICENSE)). These experiments are educational and do not represent a production 7 nm process or silicon signoff.

## SKY130HD second-library experiment

Both RTL architectures are independently synthesized, placed, clock-tree synthesized, routed, extracted and exported to GDS on the ORFS SKY130HD platform. Post-route OpenSTA uses the platform's `sky130_fd_sc_hd__tt_025C_1v80.lib` typical model and the corresponding final ODB, exported SDC and extracted SPEF.

SKY130HD has one verified typical model in the pinned ORFS platform used here. The upstream SkyWater PDK declares Apache-2.0 licensing ([license](https://github.com/google/skywater-pdk/blob/main/LICENSE)). This extension does not invent fast/slow corners or claim SKY130HD MCMM.

The SKY130HD SDC expresses the same intended interface timing budget as the baseline, with the platform's units made explicit: ns for time and pF for output load (20 fF = 0.020 pF; 30 fF = 0.030 pF). The ASAP7 library units are ps and fF. The run manifest checks these units from OpenSTA's `report_units` output instead of relying only on assumptions.

## Reproducibility and artifacts

Run inside the pinned ORFS container:

```bash
make technology-breadth
```

The CI workflow runs the same script and uploads a 90-day artifact named `timingforge-technology-breadth`. The generated `technology_breadth_manifest.json` contains:
- ORFS, OpenROAD and Yosys version metadata.
- Exact Liberty hashes for ASAP7 BC/TC/WC and SKY130HD TT.
- Final ODB/GDS/SPEF/SDC paths and SHA-256 hashes for each architecture/platform.
- Per-scene setup/hold path inventories and worst slack among the reported paths.
- Explicit RC-reuse, cross-library-comparison and signoff limitations.

A reported path-inventory minimum is the minimum among paths emitted by the configured OpenSTA report, not a substitute for a separate exhaustive signoff report database.

## Signoff boundary

No foundry DRC/LVS signoff, OCV/AOCV/POCV model validation, crosstalk/SI, IR/EM, power signoff, or manufacturing readiness is claimed. The original Nangate45 physical results remain separately documented in [Phase 3 results](PHASE3_RESULTS.md).
