# QoR regression baseline

The committed benchmarks/qor_baseline.json is the reviewed golden-row snapshot generated from the pinned OpenROAD Flow Scripts Nangate45 typical-corner environment in physical workflow run #23 (checked-out merge commit 1ff8da7b8f2da3b99c7a3969ce07bd8b294bcc5b). It records the exact platform source revision, Liberty SHA-256, Yosys/OpenROAD versions, golden SDC hash, and the two architecture rows. Mutation rows are intentionally excluded from QoR regression; they are evaluated by the separate mutation-impact oracle.

CI creates a candidate snapshot and runs:

```bash
python3 -m tools.qor_history snapshot build/reports/sta_matrix_summary.json \
  --output build/reports/qor_snapshot.json
python3 -m tools.qor_history compare benchmarks/qor_baseline.json \
  build/reports/qor_snapshot.json \
  --output build/reports/qor_comparison.json \
  --area-tolerance-percent 0.5 --timing-tolerance-ns 0.005
```

The regression fails if the environment or golden SDC hash changes, if a metric changes between available/unavailable, if standard-cell area changes by more than 0.5%, or if any timing metric changes by more than 0.005 ns. The native combined register-only period is unavailable in the baseline; a newly available value is deliberately treated as a metric-availability change that requires review rather than silently accepted.

## Refreshing the baseline

Do not refresh the baseline just to make CI green. First verify that the RTL/SDC change is intentional, inspect the raw STA logs and sta_quality_findings.json, confirm the pinned platform/Liberty/tool versions, and review the exact area/timing deltas. Then regenerate the candidate snapshot inside the pinned ORFS container and copy it to the reviewed baseline:

```bash
source /OpenROAD-flow-scripts/env.sh
make sta-matrix
python3 -m tools.qor_history snapshot build/reports/sta_matrix_summary.json \
  --output build/reports/qor_snapshot.json
cp build/reports/qor_snapshot.json benchmarks/qor_baseline.json
python3 -m tools.qor_history compare benchmarks/qor_baseline.json \
  build/reports/qor_snapshot.json
git diff -- benchmarks/qor_baseline.json
```

Include the reason for the baseline change and the CI run/source SHA in the pull request. The baseline is a reproducibility guard for these measured metrics, not a measure of general STA correctness or design quality.
