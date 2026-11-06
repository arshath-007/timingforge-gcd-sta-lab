# Physical robustness and clock-period closure experiments

The physical-experiments workflow uses the digest-pinned Nangate45 ORFS container and runs both architectures with matched settings.

## Placement/utilization variation

Five paired runs use the following CORE_UTILIZATION / PLACE_DENSITY / GPL_RANDOM_SEED / GRT_SEED settings:

| Variant | CORE_UTILIZATION | PLACE_DENSITY | GPL_RANDOM_SEED | GRT_SEED |
|---|---:|---:|---:|---:|
| v1 baseline | 35 | 0.60 | 1 | 1 |
| v2 low/low | 30 | 0.55 | 2 | 2 |
| v3 low/high | 30 | 0.65 | 3 | 3 |
| v4 high/low | 40 | 0.55 | 4 | 4 |
| v5 high/high | 40 | 0.65 | 5 | 5 |

Each setting is run for both combined and split architectures. The same seed and floorplan settings are used within each pair. The report summarizes the mean, minimum, maximum, range, and population standard deviation of post-route register-only period, all-path period, standard-cell area/count, clock buffers, and timing-repair buffers. It also records which architecture has the shorter register-only period in each paired variant. A ranking that flips across variants must be described as placement-sensitive rather than as a robust winner.

## Clock-period sweep

A separate six-point sweep uses periods 3.000, 2.500, 2.000, 1.500, 1.200, and 1.000 ns at CORE_UTILIZATION=35, PLACE_DENSITY=0.60, GPL_RANDOM_SEED=1, and GRT_SEED=1. Both architectures are run at every period. Each run uses its own generated SDC copy; constraints/gcd_baseline.sdc is never modified.

For every completed flow, the summary records setup WNS/TNS, hold WNS/TNS, post-route register-only and all-path minimum periods, standard-cell area/count, clock-buffer count, and timing-repair-buffer count. A point is classified as timing-closed only if worst setup slack and worst hold slack are non-negative, all reported max-slew/capacitance/fanout violation counts are zero, and no connected unannotated SPEF driver remains. A flow that cannot complete is retained as a failed point rather than silently omitted.

## Reproduction

Inside the pinned ORFS container, set the expected image digest and run:

```bash
export ORFS_IMAGE_DIGEST=sha256:f05cee3219a02f26289f02f00e11a3fc986ab51a482a0000a2da810cda219a6e
bash scripts/run_physical_experiments.sh
```

The workflow uploads raw ORFS logs, final ODB/SPEF/SDC/netlist artifacts, post-route STA reports, per-run metadata, and physical_experiments_summary.json. The summary is observational evidence for the Nangate45 typical corner, not foundry signoff or silicon characterization.

## Measured results — validated run

The [physical robustness workflow run #42191546348](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42191546348) completed all 22 physical flows: 10 placement/utilization variants and 12 clock-period sweep runs. All 22 reports were parsed and no ORFS flow failed. The [90-day evidence artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42191546348/artifacts/13492292148) contains 2,386 files, including run metadata, final ODB/GDS/SPEF/SDC/netlists, stage logs, post-route STA and the machine-readable summary. Downloaded artifact SHA-256: `beeea9e1fd59282e1115dfe8ed79b8f3ad633c90ca10de9daef0e4d66a7674c4`.

### Five paired placement/utilization variants

| Metric | Combined GCD | Split GCD |
|---|---:|---:|
| Register-to-register period — mean | 0.922 ns | 1.050 ns |
| Register-to-register period — range | 0.89–0.96 ns | 1.01–1.18 ns |
| Register-to-register period — population standard deviation | 0.027857 ns | 0.065115 ns |
| All-path period — mean | 2.132 ns | 2.192 ns |
| Standard-cell area — mean | 2657.66 | 2500.88 |

The combined architecture had the shorter register-to-register period in all five paired variants (5/5). The split architecture's mean standard-cell area was about 5.9% lower. This is evidence for these five controlled Nangate45 configurations only; it is not a universal architecture ranking or a statistical guarantee over all placement seeds.

### Six-point clock-period sweep

| Target clock period | Combined GCD | Split GCD |
|---:|---|---|
| 1.000 ns | Not closed | Not closed |
| 1.200 ns | Not closed | Not closed |
| 1.500 ns | Not closed | Not closed |
| 2.000 ns | Closed | Closed |
| 2.500 ns | Not closed — max-capacitance violation | Closed |
| 3.000 ns | Closed | Closed |

At the 2.500 ns combined-GCD point, timing slack was non-negative, but the final max-capacitance report still showed a violation at pin `_3726_/ZN` (reported capacitance 54.633 against a limit of 53.406; slack -1.227). The closure gate correctly retained that point as not closed. A successful ORFS flow exit is not itself a timing-closure pass.

These results demonstrate why timing closure must include setup, hold, design-rule checks and parasitic-annotation review, rather than treating the target clock period or WNS alone as sufficient. The entire experiment remains a Nangate45 typical-corner educational study, not signoff.
