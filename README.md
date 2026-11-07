[![TimingForge regression](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/workflows/rtl-regression.yml/badge.svg)](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/workflows/rtl-regression.yml)
[![TimingForge formal](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/workflows/formal-equivalence.yml/badge.svg)](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/workflows/formal-equivalence.yml)
[![TimingForge physical design](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/workflows/physical-design.yml/badge.svg)](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/workflows/physical-design.yml)
[![TimingForge physical robustness](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/workflows/physical-experiments.yml/badge.svg)](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/workflows/physical-experiments.yml)
[![TimingForge technology breadth](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/workflows/technology-breadth.yml/badge.svg)](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/workflows/technology-breadth.yml)

# TimingForge
## An Open Benchmark for Trustworthy Static Timing Analysis

**Status:** Research prototype · **Version:** 0.4.0 candidate (PR #10 release-gate hardening in progress; awaiting final CI, independent review, merge and main-branch validation) · **Latest published release:** [v0.2.1](https://github.com/arshath-007/timingforge-gcd-sta-lab/releases/tag/v0.2.1) · **License:** MIT

> A timing report can look clean even when the constraints are incomplete. TimingForge studies whether an STA flow can identify deliberately introduced constraint defects before engineers trust its results.

TimingForge is an educational, reproducible benchmark for **constraint quality and timing-analysis trust**. It uses two 32-bit binary-GCD RTL architectures as a controlled test vehicle, injects named SDC defects, runs a conservative constraint-coverage checker, and analyses the golden/mutated constraints with a library-backed OpenROAD-integrated OpenSTA flow.

This is not a replacement for signoff STA, an official EDA signoff qualification, or a claim that an unconstrained path is automatically a silicon failure. It is a research and learning framework that makes assumptions visible and experiments reproducible.

## Why this problem matters

Static timing analysis is only as meaningful as the design model and timing constraints supplied to it. Missing clocks or I/O delays, incorrect port matches, and unjustified timing exceptions can leave paths unconstrained or excluded. A positive slack value is not sufficient evidence that all intended paths were analysed.

TimingForge makes this failure mode testable:

1. Establish a reference RTL and SDC baseline, documenting any observed setup or hold violations.
2. Generate controlled, named SDC mutations from that baseline.
3. Run static constraint-coverage checks.
4. Synthesize both RTL architectures against the same standard-cell Liberty library.
5. Run the golden and mutated SDC files through the same timing engine and netlist.
6. Compare setup/hold results, unconstrained endpoints, critical paths, and register-to-register path coverage.
7. Publish every assumption and result rather than inventing PPA numbers.

## Architecture

```mermaid
flowchart TD
    A[Reference GCD RTL: combined and split] --> B[Yosys synthesis + Nangate45 Liberty]
    B --> C[Mapped gate-level netlists]
    D[Golden SDC] --> E[Controlled SDC mutations]
    D --> F[OpenROAD-integrated OpenSTA]
    E --> G[Static SDC coverage checker]
    E --> F
    C --> F
    G --> H[Static JSON/Markdown scorecard]
    F --> I[Setup, hold, critical-path and unconstrained reports]
    I --> J[Parsed 16-scenario timing matrix]
```

The static checker is a conservative, interface-specific prototype—not a full SDC Tcl parser. The library-backed matrix uses Yosys, the OpenROAD-integrated OpenSTA engine, and the educational Nangate45 typical Liberty platform.

## Core features

- Two synthesizable iterative binary-GCD microarchitectures: combined compare/subtract and split compare/subtract.
- A self-checking SystemVerilog testbench using a Euclidean-algorithm reference model.
- Additional parameterized synchronous FIFO and signed MAC accumulator blocks with directed SystemVerilog regression tests (functional extension; not yet part of the GCD STA matrix).
- A documented 10 ns block-level SDC example with setup/hold uncertainty and min/max I/O delays.
- Seven controlled SDC mutation cases:
  - M01 missing primary clock.
  - M02 missing input delay.
  - M03 missing output delay.
  - M04 broad register-to-register false-path exception.
  - M05 near-match/incorrect port collection.
  - M06 missing hold clock uncertainty.
  - M07 non-positive clock period.
- Static SDC coverage checker, fault generator, JSON/Markdown scorecard, and Python unit tests.
- Yosys synthesis scripts and a library-backed OpenROAD-integrated STA matrix runner.
- STA report parser that summarises area, minimum clock period, Fmax, worst setup/hold slack, WNS/TNS, register-to-register path presence, unconstrained endpoints, heuristic critical-path classes, and OpenSTA max-slew/max-capacitance/max-fanout violation records.
- Phase 1 quality findings, SDC mutation impact scoring, and reproducible clock-uncertainty/source-latency sensitivity experiments.
- Conservative golden-result quality checks that flag missing metrics, unconstrained endpoints, missing I/O delays, negative hold slack, and unavailable native register-only period without inventing a derived Fmax.
- Bounded WIDTH=3 formal miter with an independent exhaustive GCD truth-table oracle, protocol assertions, and a deliberately broken RTL negative control (validated by [PR #10 formal run](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754417)).
- Verilator concurrent-SVA protocol checks and WIDTH=8/16/32 simulation sweeps; these are simulation/assertion evidence, not full-width formal proofs.
- Environment-specific fail-closed Nangate45 typical-corner QoR regression gate.
- Validated ASAP7 BC/TC/WC MCMM and SKY130HD TT physical-flow extension; see the [measured technology-breadth results](docs/PHASE3_TECHNOLOGY_BREADTH_RESULTS.md) and [PR #10 workflow](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754263).
- GitHub Actions regression, formal, physical-design and technology-breadth workflows.

## Repository layout

```text
rtl/             synthesizable GCD architectures plus FIFO/MAC extension blocks
tb/              self-checking GCD, FIFO and MAC SystemVerilog testbenches
constraints/     golden SDC
tools/           fault injector, SDC linter, STA/QoR and physical-evidence parsers
tests/           Python unit tests for STA, QoR, and physical evidence
scripts/         synthesis, formal, OpenSTA and OpenROAD entry points
formal/          bounded transaction-equivalence miter and SymbiYosys config
physical/        matched Nangate45 ORFS design configurations
docs/            scope, fault catalog, verification and physical results
reports/         generated reports (not committed by default)
.github/         automated RTL/Python and library-backed STA workflows
```

## Quick start

### 1. Functional RTL regression

Requirements: Icarus Verilog with SystemVerilog support.

```bash
make rtl-test
make ip-block-test
```

### 2. Static SDC fault-injection benchmark

Requirements: Python 3.10+.

```bash
make mutants
make lint-sdc
make python-test
make benchmark
python3 -m unittest discover -s tests -p 'test_quality_checks.py' -v
```

Generated SDC files are written under `build/mutants/`. The checker validates simple expected clock, setup/hold uncertainty, and min/max I/O-delay patterns for the GCD interface. The benchmark writes JSON and Markdown scorecards under `build/`; its score covers seven controlled pattern/coverage mutations only, not general SDC correctness or signoff.

### 3. Library-backed synthesis and timing matrix

Requirements: OpenROAD Flow Scripts environment with Yosys, OpenROAD-integrated OpenSTA, Python 3, and curl.

```bash
source /OpenROAD-flow-scripts/env.sh
make sta-matrix
make sensitivity
python3 -m tools.quality_checks build/reports/sta_matrix_summary.json --output build/reports/sta_quality_findings.json
```

The script downloads the Nangate45 typical Liberty and two LEF files from a pinned OpenROAD Flow Scripts source revision when they are not present. It synthesizes both GCD architectures and runs the golden SDC plus seven mutations through the timing engine (16 STA runs total). It then writes:

- `build/reports/sta_matrix_summary.md`
- `build/reports/sta_matrix_summary.json`
- `build/reports/sta_quality_findings.json`
- `build/reports/sta_mutation_impact.json`
- `build/sensitivity/sensitivity_summary.json` plus generated SDC variants
- Raw baseline and sensitivity STA logs in `build/reports/`
- Yosys synthesis logs in `build/`

The summary separates register-to-register minimum period/Fmax from all-path minimum period/Fmax (which includes I/O port paths), and includes Yosys cell area, worst setup/hold slack, WNS/TNS, path presence, missing I/O-delay warnings, and unconstrained endpoints. The supported matrix flow uses the OpenROAD-integrated OpenSTA executable (`openroad`) and its LEF-aware setup.

### 4. Manual synthesis and STA

For a locally configured standard-cell library:

```bash
export LIBERTY=/absolute/path/to/your/stdcells.lib
make synth
export NETLIST=build/gcd_binary_combined.v
export SDC=constraints/gcd_baseline.sdc
make sta
```

Review the raw Yosys/OpenSTA logs and tool versions. A successful script exit alone is not a substitute for understanding the reported paths and constraints.

## Verified evidence

The v0.2.0 release was validated by [GitHub Actions run #160](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42015328699), source commit `bdd42621749035fa088e326c766f3af8031af337`. Both RTL/Python regression and the 16-run Nangate45 STA matrix passed.

- Two synthesizable GCD architectures evaluated.
- Seven defined SDC fault patterns detected (7/7).
- Both architectures synthesized against the pinned Nangate45 typical Liberty file.
- Eight SDC scenarios analysed per architecture (16 STA logs).
- Corrected golden output loads: 20 fF on scalar outputs and 30 fF on the GCD output bus.
- Combined: 1657.180 area units, 2.94 ns all-path period, 340.67 MHz all-path Fmax, +7.065 ns worst setup slack and -0.002 ns worst hold slack.
- Split: 1681.918 area units, 2.35 ns all-path period, 425.57 MHz all-path Fmax, +7.650 ns worst setup slack and +0.005 ns worst hold slack.
- All-path period includes I/O port paths. These figures are not a register-to-register-only architecture speed comparison.
- Split register-to-register minimum period: 0.740 ns. The equivalent combined-design minimum-period query returned no usable measurement, although a separate path report finds register-to-register paths.
- Latency figures are finite-corpus observations, not proven worst-case bounds.

Download the [STA matrix artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42015328699/artifacts/13408368824) and [static benchmark artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42015328699/artifacts/13408887449).

## Phase 1 reliability evidence — v0.3.0 candidate

The Phase 1 implementation is merged to `main`. The final feature-branch validation [run #257](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42046659049) and post-merge main validation [run #258](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42047005600) both passed regression and library-backed STA. The [run #258 STA artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42047005600/artifacts/13425391627) contains raw logs and machine-readable results.

- 18 clock-sensitivity experiments completed: nine constraint variants for each GCD architecture.
- SDC mutation impact: 12 matched, 0 mismatched, 2 inconclusive. Both inconclusive observations are M06 because the current reports do not directly expose whether hold uncertainty was applied.
- Baseline DRV violation records: combined GCD — 10 max-slew and 15 max-capacitance; split GCD — 9 max-slew and 15 max-capacitance. No max-fanout violation records were emitted; the violator-only report does not enumerate total applicable checks.
- Golden quality findings: REVIEW, with five warnings and three informational findings. The combined design retains -0.002 ns hold slack, and its native register-only minimum-period metric remains unavailable.
- These are pre-layout Nangate45 typical-corner results with ideal clocks and no SPEF. No physical-design or signoff claim is made.

See [Phase 1 diagnostics and measured sensitivity](docs/PHASE1_DIAGNOSTICS.md).

The current main-branch extension and diagnostic changes passed both CI jobs in [run #196](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42029353553) at commit `30b7a7bcf862762627935813a31330efa85a1eff`. Its [latest STA matrix artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42029353553/artifacts/13415850763) contains the 16 raw logs, parsed report, and explicit register-path inventory. The original v0.2.0 baseline values remain traceable to [release validation run #160](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42015328699); reproducibility is documented in [initial results](docs/INITIAL_RESULTS.md).

See [initial results](docs/INITIAL_RESULTS.md), the [architecture and STA report walkthrough](docs/ARCHITECTURE_AND_STA_WALKTHROUGH.md), the [portfolio summary and project demonstration](docs/PORTFOLIO_AND_INTERVIEW.md), and [advanced SDC exercises](docs/ADVANCED_SDC_EXERCISES.md).


## Phase 2 verification evidence — bounded formal + reproducible simulation

The updated oracle-backed formal miter passed in [PR #10 formal workflow run #42225754417](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754417); download the [formal proof artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754417/artifacts/13494245840). The positive CVC5 proof passed at 26 SMT steps / 12 positive clock edges (11:08 solver time). The deliberately broken subtract mutant was rejected at step 5 for the counterexample operands a=5, b=3.

- The formal oracle covers all 64 symbolic WIDTH=3 operand pairs and is cross-checked against Python math.gcd; both GCD architectures are checked against that independent oracle, against each other, and for one-transaction completion/protocol behavior.
- The proof remains bounded at WIDTH=3. It does not prove all 32-bit inputs, arbitrary back-to-back transactions, or an unbounded sequential invariant.
- The 32-bit regression includes directed cases and 250 deterministic constrained-random cases using seed 0x54462026; 259 cases were checked on each architecture, with parity, zero/equal, high-bit, GCD-class and latency-bin coverage.
- Verilator concurrent-SVA protocol checks and WIDTH=8/16/32 simulations are complementary dynamic evidence, not part of the Yosys/CVC5 proof.
- QoR snapshots record source SHA, tool versions, platform/corner, Liberty hash, scenario and SDC hashes. The comparator rejects environment or scenario mismatches. Snapshots are artifact-backed, not a persistent database/dashboard.
- The [PR #10 regression and library-backed STA run #42225754505](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754505) passed the RTL/width/SVA/FIFO/MAC/Python checks, SDC lint, static fault-injection benchmark, Nangate45 STA matrix and QoR gate. Artifacts: [Nangate45 STA matrix](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754505/artifacts/13506026425) and [static benchmark scorecard](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754505/artifacts/13506240639).



## Phase 3 physical-design evidence — Nangate45 typical

The latest PR #10 [physical-design workflow run #42225754311](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754311) passed for both architectures. Download the [complete physical evidence artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754311/artifacts/13505672933), which includes final ODB/GDS/SPEF/SDC, stage logs/reports, post-route STA logs, comparison JSON and SHA-256 manifest. Detailed interpretation is in [Phase 3 measured results](docs/PHASE3_RESULTS.md).

| Post-route metric | Combined GCD | Split GCD |
|---|---:|---:|
| Register-to-register minimum period | 0.95 ns | 1.02 ns |
| Register-to-register Fmax | 1048.98 MHz | 984.86 MHz |
| All-path minimum period | 2.13 ns | 2.26 ns |
| All-path Fmax | 469.98 MHz | 442.15 MHz |
| Worst setup slack | +7.872 ns | +7.738 ns |
| Worst hold slack | +0.031 ns | +0.018 ns |
| Reported setup skew (worst reported path) | +0.16 ns | +0.16 ns |
| Reported hold skew (worst reported path) | -0.06 ns | -0.06 ns |

The register-to-register metric excludes I/O paths; all-path period includes constrained port paths. The two metrics must not be interchanged. Both flows produced final GDS, ODB, SDC and extracted SPEF; post-route STA loaded SPEF and used propagated clocks. These are Nangate45 typical-corner educational results, not signoff. The separate ASAP7/SKY130HD technology-breadth experiment is documented below and remains subject to its own CI validation; it does not retroactively change these Nangate45 measurements. The optional ORFS Kepler-based internal LEC subprocess is disabled and no netlist-to-netlist LEC claim is made.

## Phase 3 technology breadth — PR validation passed

The dedicated [PR #10 technology-breadth workflow run #42225754263](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754263) passed for both architectures on ASAP7 and SKY130HD. The [90-day artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754263/artifacts/13505838538) contains 412 files, final ODB/GDS/SPEF/SDC for all four platform/design combinations, per-scene reports, tool/library provenance and a SHA-256 manifest. All 36 manifest-listed per-design implementation artifacts were independently hash-checked after download.

- ASAP7 uses distinct FF/TT/SS Liberty scenes: BC (FF, 0°C, 0.77 V), TC (TT, 25°C, 0.70 V), and WC (SS, 100°C, 0.63 V). The top 100 setup and hold paths per scene were reported for each architecture.
- The combined design's minimum hold slack among the emitted WC hold paths was -3.225 ps; this is a real hold warning and must not be described as full hold closure. The split design's minimum among the emitted paths was +5.691 ps. OpenSTA is asked for up to 100 paths per path group; the manifest emitted 100 hold rows per scene in this run. The reported minima are limited to emitted reports, not an exhaustive path inventory.
- The ASAP7 experiment reuses one TC-extracted SPEF unchanged across BC/TC/WC; there is no corner-specific RC extraction or scaling. The OpenSTA `-group_path_count 100` setting caps output at 100 paths per path group (not 100 paths total); the parser calculates minima only from emitted slack rows, not an exhaustive signoff path inventory.
- SKY130HD was implemented independently at its verified TT, 25°C, 1.80 V model. Post-route all-path minimum period was 4.96 ns (combined) and 5.06 ns (split); the split register-to-register minimum period was 4.91 ns. See the detailed [technology-breadth results](docs/PHASE3_TECHNOLOGY_BREADTH_RESULTS.md).
- ASAP7 is an academic predictive platform; SKY130HD is an open PDK platform. Cross-library absolute PPA ranking and foundry signoff are not claimed. The final merge and fresh main-branch validation remain pending.



## Research questions

- Does the checker detect each mutation that it is designed to recognise?
- Can a timing exception hide register-to-register paths that are present under the golden SDC?
- Can missing I/O delays cause paths to become unconstrained or make the apparent minimum period look better?
- How do critical path, setup slack, hold slack, and unconstrained endpoints change between scenarios?
- How do the combined and split GCD architectures trade logic depth against cycle count and cell area?
- Which checks can be automated safely, and which require design intent or engineer review?

## Current limitations

- The Python linter is a first-pass line/pattern-based checker, not a full SDC parser or proof of constraint correctness. It recognises the project's canonical option ordering and simple `get_ports` forms; alternative but valid Tcl/SDC command orderings may be rejected. It checks presence and positivity of uncertainty, not whether an I/O delay is realistic for a product. False paths, multicycle paths, clock groups, disabled timing arcs and case analysis are flagged for human review.
- A false-path statement is flagged for review; a broad false-path test is only a controlled negative experiment. The tool does not decide whether a real exception is valid without design intent.
- The first SDC is an illustrative block-level budget, not a product specification. Output loads are expressed in the Liberty capacitance unit (fF); the current SDC uses 20 fF for scalar control outputs and 30 fF for the GCD bus. Changing these loads requires regenerating the baseline timing evidence.
- The pre-layout matrix uses one Nangate45 typical corner, ideal clocks, and no SPEF. A separate reproducible ORFS flow now produces placed, CTS, routed and extracted-SPEF post-route results for both GCD architectures at that same typical corner.
- The ASAP7 experiment provides distinct BC/TC/WC Liberty timing scenes over one unchanged TC-extracted SPEF; combined WC hold has -3.225 ps minimum slack among emitted hold paths (up to 100 paths per path group). SKY130HD is TT-only. No corner-specific RC extraction/scaling, OCV/AOCV/POCV, crosstalk/SI, timing ECO closure, or netlist-to-netlist LEC across ORFS optimization stages is claimed. The optional ORFS Kepler LEC subprocess is disabled in this container; Phase 2 supplies a separate bounded RTL transaction-equivalence proof.
- The physical run is an educational flow, not foundry signoff. DRC/LVS signoff, IR-drop/EM qualification, and manufacturing readiness are not claimed.
- The educational Nangate45 platform is not a modern production process or signoff reference.
- No power measurement is claimed.

## Prior art and positioning

TimingForge builds on existing open-source EDA infrastructure rather than competing with it:
- [OpenSTA](https://github.com/The-OpenROAD-Project/OpenSTA) performs static timing analysis.
- [Yosys](https://github.com/YosysHQ/yosys) performs RTL synthesis.
- [OpenROAD](https://github.com/The-OpenROAD-Project/OpenROAD) provides physical-design implementation flows.
- Existing SDC lint and constraint-analysis projects already address parts of constraint validation.

The intended project contribution is a **reproducible fault-injection benchmark that links named SDC defects to both static checker findings and library-backed STA observations**. This is a differentiated project direction, not a claim of global novelty. The prior-art review should be expanded as the project matures.

## Roadmap

- [x] Two synthesizable GCD architectures.
- [x] Self-checking functional regression.
- [x] Golden SDC with explicit setup/hold and min/max I/O assumptions.
- [x] Seven controlled SDC mutation scenarios and unit tests.
- [x] Static SDC checker and machine-readable scorecard.
- [x] Yosys synthesis against a documented/pinned Liberty platform.
- [x] OpenROAD-integrated STA matrix for both architectures and all eight SDC scenarios.
- [x] Parsed STA matrix report and initial measured results.
- [x] Add functional FIFO and MAC extension blocks with directed tests (not yet included in the GCD STA matrix).
- [x] Add OpenSTA DRV violation reporting and conservative quality findings.
- [x] Add reproducible setup/hold uncertainty and source-latency sensitivity experiments.
- [x] Add expected-versus-observed SDC mutation impact scoring with inconclusive outcomes preserved.
- [ ] Add generated-clock, multicycle, clock-group, and justified false-path scenarios.
- [x] Add OpenROAD floorplanning, placement, CTS, routing, GDS generation, and SPEF-based post-route STA for both architectures at Nangate45 typical.
- [x] Compare pre-layout and post-route metrics using the same baseline SDC and typical Liberty; treat deltas as cross-flow observations because the synthesis settings/netlists are not matched; archive raw logs and SHA-256 manifests.
- [x] Validate the ASAP7 BC/TC/WC MCMM and SKY130HD TT experiments using the dedicated technology-breadth workflow and its artifact manifest ([PR #10 run #42225754263](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754263)); final main-branch validation remains part of the release gate.
- [ ] Add variation-aware experiments (OCV/AOCV/POCV) only with appropriate validated models and methodology.
- [ ] Validate findings with external contributors and maintainers.

## Contributing and citation

See [development phases and acceptance criteria](docs/DEVELOPMENT_PHASES.md), [CONTRIBUTING.md](CONTRIBUTING.md), [CITATION.cff](CITATION.cff), [docs/PROJECT_SCOPE.md](docs/PROJECT_SCOPE.md), [docs/FAULT_CATALOG.md](docs/FAULT_CATALOG.md), .

## Author

Maintained by [arshath-007](https://github.com/arshath-007).

**Recruiter-facing note:** The goal is to demonstrate engineering method—clear assumptions, functional verification, SDC reasoning, tool use, reproducibility, and honest interpretation—not to claim production signoff experience.


## Physical evidence integrity and robustness

The Nangate45 pre-layout Yosys synthesis and ORFS physical synthesis configurations are not netlist-matched. Timing deltas are therefore cross-flow observations; they must not be attributed solely to routing or parasitics. The physical manifest records the source revision, RTL/SDC/script hashes and declared pinned container digest. The post-route flow checks SPEF annotation and reports register-only and all-path minimum periods separately. The optional ORFS Kepler netlist-LEC subprocess remains disabled, so no netlist-to-netlist equivalence claim is made.

The [physical robustness experiment](docs/PHYSICAL_ROBUSTNESS.md) includes five paired placement/utilization variants and six clock-period targets for both GCD architectures. Its latest successful [PR #10 workflow run #42225754303](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42225754303) parsed 22/22 physical runs. Across the five placement pairs, combined GCD had the shorter register-only period in all five; split GCD averaged about 5.9% less cell area. At a 2.5 ns target, combined GCD retained a max-capacitance violation at pin `_3726_/ZN` (54.633 against a 53.406 limit; slack -1.227) and was correctly classified as not closed; split GCD closed. These are educational Nangate45 typical-corner experiments, not signoff or a guarantee across all placement seeds.

The separate [ASAP7 and SKY130HD technology-breadth results](docs/PHASE3_TECHNOLOGY_BREADTH_RESULTS.md) are not mixed with the Nangate45 measurements. ASAP7 WC combined-GCD hold slack is -3.225 ps among the emitted hold paths (100-path-per-group reporting cap), and the same TC-extracted SPEF is reused across its three Liberty scenes; this is not full PVT/RC signoff.
