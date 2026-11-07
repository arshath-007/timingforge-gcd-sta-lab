# Phase 3 technology-breadth results — PR #10 validation

## Latest validated run

- Workflow: [TimingForge technology breadth, run #58](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42199460181)
- Source commit: `6140483a93dec20f0dff4c014ff9a9f852802a75`
- Artifact: [timingforge-technology-breadth.zip](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42199460181/artifacts/13494468655) (55,751,174 bytes; 90-day retention)
- Artifact SHA-256: `bed410bfef04cbd23211c1f13f24653e16301823431448c10f6ae521f5a75112`
- Manifest: `technology_breadth_manifest.json` (schema 1.0; produced by the PR #10 run)
- Tool provenance: OpenROAD/Yosys versions and ORFS source revision are recorded in the artifact's `tool_versions.txt`; pinned container digest `sha256:f05cee3219a02f26289f02f00e11a3fc986ab51a482a0000a2da810cda219a6e`.

The PR #10 workflow completed successfully for both GCD architectures on both platforms. It generated final ODB, Verilog, GDS, SPEF and SDC for all four platform/design combinations and passed manifest validation. The build-time manifest generator reads the actual pinned Liberty files used by the three ASAP7 scenes, parses each file's `nom_voltage` and `nom_temperature`, compares those values with the expected scene values, and records the parsed values and SHA-256 hashes. A successful run therefore confirms that this check passed against the actual libraries in the pinned ORFS environment; it is not merely a unit test against synthetic headers.

## ASAP7 post-route MCMM

The physical implementation is performed once per architecture at TC. OpenSTA then evaluates three distinct Liberty PVT scenes using the same extracted SPEF for that architecture.

| Scene | Process | Temperature | Voltage |
|---|---|---:|---:|
| ASAP7_BC | FF | 0°C | 0.77 V |
| ASAP7_TC | TT | 25°C | 0.70 V |
| ASAP7_WC | SS | 100°C | 0.63 V |

**Minimum slack among emitted setup/hold paths (OpenSTA request: up to 100 paths per path group, scene and design):**

| Architecture | Scene | Setup slack (ps) | Hold slack (ps) |
|---|---|---:|---:|
| Combined GCD | BC | 7973.601 | 8.200 |
| Combined GCD | TC | 7803.926 | 17.088 |
| Combined GCD | WC | 7504.804 | -3.225 |
| Split GCD | BC | 7948.192 | 5.724 |
| Split GCD | TC | 7780.835 | 16.630 |
| Split GCD | WC | 7490.069 | 5.691 |

The combined architecture has a negative hold slack of -3.225 ps among the reported WC hold paths. This must remain visible; the experiment does not establish full hold closure. The TCL uses OpenSTA `report_checks -group_path_count 100`: OpenSTA defines this as up to 100 paths **per path group**, not 100 paths total. The reports remain grouped by path group (the optional `-sort_by_slack` mode instead sorts across groups). The parser computes the minimum only from slack rows present in those emitted reports. Accordingly, the values below are minima among the emitted path set; they are not a full path inventory, and the project does not claim exhaustive signoff WNS/TNS from this capped report. All six scenes produced setup, hold and design-rule report files. See the [OpenSTA `report_checks` command reference](https://opensta.readthedocs.io/en/latest/Commands/) for the path-group and sorting options.

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