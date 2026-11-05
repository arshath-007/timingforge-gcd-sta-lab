# Phase 2 QoR history

The CI job emits `build/reports/qor_snapshot.json` for every library-backed STA run. Each snapshot records:

- Source commit SHA.
- OpenROAD/Yosys tool versions.
- Nangate45 platform revision, typical corner, and Liberty SHA-256.
- Each architecture/scenario pair and the exact SDC SHA-256.
- Cell area, all-path minimum period, register-to-register period when available, and worst setup/hold slack.

Snapshots are retained as GitHub Actions artifacts. To compare two downloaded snapshots:

```bash
python3 -m tools.qor_history compare baseline_qor_snapshot.json candidate_qor_snapshot.json --output qor_delta.json
```

The comparator allows the source SHA to differ but rejects differences in platform, corner, tool versions, Liberty hash, scenario set, or per-scenario SDC hash. A comparison is therefore a same-environment source change, not a comparison of unlike libraries or constraints.

This is artifact-backed QoR history, not a persistent database or automatic trend dashboard. The snapshots must be retained and supplied explicitly for comparison.
