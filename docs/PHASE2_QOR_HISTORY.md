# Phase 2 QoR history and regression policy

The library-backed Nangate45 CI job emits `build/reports/qor_snapshot.json` for every run. Each snapshot records source commit, OpenROAD/Yosys versions, platform revision, typical corner, Liberty SHA-256, architecture/scenario, exact SDC SHA-256, cell area, minimum periods, and worst setup/hold slack.

Snapshots are retained as GitHub Actions artifacts. To compare two downloaded snapshots:

```bash
python3 -m tools.qor_history compare baseline_qor_snapshot.json candidate_qor_snapshot.json --output qor_delta.json
```

The comparator rejects unlike environments, scenario sets, and SDC hashes. This is a same-environment source change, not a comparison of unlike libraries or constraints.

## Fail-closed CI guardrail

The current CI also runs `tools.qor_gate` against the reviewed Nangate45 typical-corner baseline in `baselines/nangate45_qor_baseline.json`, using `config/qor_gate_policy.json`.

- Maximum cell-area growth: 8%.
- Maximum all-path minimum-period growth: 8%.
- Maximum setup-slack loss: 0.25 ns.
- Maximum hold-slack loss: 0.02 ns.
- Missing/non-finite metrics, a different platform revision/corner/Liberty/tool set, or a different golden SDC hash fail closed.

The reference is anchored to the exact successful CI environment and commit recorded in the baseline file. Refreshing it requires a deliberate reviewed change with retained artifacts; do not automatically bless a new baseline.

This is artifact-backed QoR history plus a static reviewed regression gate, not a persistent database or automatic trend dashboard. It is an educational guardrail, not signoff methodology.
