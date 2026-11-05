# Phase 3 technology-breadth results — PR validation

## Latest validated run

- Workflow: [TimingForge technology breadth](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727158)
- Source commit: `6f5a9c1b9c73261005445a6fd941242e6dde54cb`
- Artifact: [timingforge-technology-breadth.zip](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42098727158/artifacts/13449087689) (55,750,648 bytes; 90-day retention)
- Artifact SHA-256: `d043643e285e840120da9e407c59ae744d58bf4379773c708e6c85bb7768127c`
- Manifest: `technology_breadth_manifest.json` (schema 1.0; 412 files in the archive)
- Tool provenance: OpenROAD `26Q3-1080-gab6fd26351`; Yosys `0.68+post`; ORFS source revision `11aa833a11488c3a540a1d8eb4caa23fd22df703`; pinned container digest `sha256:f05cee3219a02f26289f02f00e11a3fc986ab51a482a0000a2da810cda219a6e`.

The workflow completed successfully for both GCD architectures on both platforms. Each of the four platform/design combinations includes final ODB, Verilog, GDS, SPEF and SDC. All 36 manifest-listed implementation-artifact hashes were independently checked after downloading the archive; no missing file or SHA-256 mismatch was found.

## ASAP7 post-route MCMM

The physical implementation is performed once per architecture at TC. OpenSTA then evaluates three distinct Liberty PVT scenes using the same extracted SPEF for that architecture.

| Scene | Process | Temperature | Voltage |
|---|---|---:|---:|
| ASAP7_BC | FF | 0°C | 0.77 V |
| ASAP7_TC | TT | 25°C | 0.70 V |
| ASAP7_WC | SS | 100°C | 0.63 V |

**Minimum slack among the 100 reported setup and 100 reported hold paths per scene:**

| Architecture | Scene | Setup slack (ps) | Hold slack (ps) |
|---|---|---:|---:|
| Combined GCD | BC | 7973.601 | 8.200 |
| Combined GCD | TC | 7803.926 | 17.088 |
| Combined GCD | WC | 7504.804 | -3.225 |
| Split GCD | BC | 7948.192 | 5.724 |
| Split GCD | TC | 7780.835 | 16.630 |
| Split GCD | WC | 7490.069 | 5.691 |

The combined architecture has a negative hold slack of -3.225 ps among the 100 reported WC paths. This must remain visible; the experiment does not establish full hold closure. The path cap is 100 per path type/scene/architecture, so these values are minima among the emitted paths, not an exhaustive signoff path inventory. All six scenes produced setup, hold and design-rule report files.

The ASAP7 experiment uses these exact library models, with PVT metadata parsed from every Liberty file actually read by each scene. The SIMPLE corner Liberty files are filtered to remove XOR, XNOR and HAxp5 cells because the pinned platform's FF/TT/SS models do not provide consistent timing groups for those cells; the same cell exclusions are applied to physical mapping. The manifest records source and filtered Liberty hashes.

**RC limitation:** one TC-extracted SPEF is reused unchanged across BC/TC/WC for each architecture. No corner-specific RC extraction or RC scaling is performed. The scenes therefore compare distinct cell-timing models under a shared parasitic network; this is not a full PVT/RC signoff analysis.

## SKY130HD second-library physical implementation

Both architectures completed the separate SKY130HD TT physical flow through floorplan, placement, CTS, routing, extraction, final ODB/GDS/SPEF/SDC generation and post-route OpenSTA with SPEF loaded.

| Architecture | Corner | Register-to-register minimum period | Register-to-register Fmax | All-path minimum period | All-path Fmax | Worst setup slack | Worst hold slack |
|---|---|---:|---:|---:|---:|---:|---:|
| Combined GCD | TT, 25°C, 1.80 V | 4.96 ns | 201.70 MHz | 4.96 ns | 201.70 MHz | +5.042 ns | +0.066 ns |
| Split GCD | TT, 25°C, 1.80 V | 4.91 ns | 203.52 MHz | 5.06 ns | 197.46 MHz | +4.936 ns | +0.257 ns |

Register-to-register period excludes I/O paths; all-path period includes constrained I/O paths. The pinned SKY130HD platform exposes the verified `sky130_fd_sc_hd__tt_025C_1v80.lib` model used in this experiment. No fast/slow SKY130HD corners or SKY130HD MCMM are claimed.

## Platform and methodology boundaries

- ASAP7 is a predictive academic platform; SKY130HD is an open PDK platform. This is educational implementation evidence, not foundry signoff.
- Absolute cell area, delay or Fmax comparisons across Nangate45, ASAP7 and SKY130HD are not apples-to-apples process comparisons.
- ASAP7 units are ps/fF; SKY130HD units are ns/pF. The run checks the units reported by OpenSTA.
- The ASAP7 FF/TT/SS Liberty nominal temperatures are 0°C/25°C/100°C. The upstream ORFS config.mk BC/TC temperature labels differ for the first two scenes; the workflow treats each Liberty file's nom_temperature and nom_voltage as authoritative and records this discrepancy.
- No OCV/AOCV/POCV, crosstalk/SI, IR/EM, power signoff, foundry DRC/LVS signoff or manufacturing-readiness claim is made.
- The separate Nangate45 typical baseline remains documented in [Phase 3 measured results](PHASE3_RESULTS.md); these cross-library experiments do not overwrite or retroactively change its metrics.

## Reproduction

Run `make technology-breadth` in the pinned ORFS container. The CI artifact preserves the raw reports, final databases, GDS, SPEF, SDC, tool versions, per-library hashes and `technology_breadth_manifest.json`.