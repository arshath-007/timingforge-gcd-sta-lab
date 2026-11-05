# SDC fault catalog

TimingForge v0.1 uses named edits to the illustrative GCD baseline. Every mutation is generated from the baseline so the change is traceable.

| ID | Deliberate edit | Expected checker finding | Interpretation |
|---|---|---|---|
| M01 | Remove create_clock | TF001 ERROR | No primary clock command remains |
| M02 | Remove input-delay lines for a_in | TF101 ERROR | One input group has no delay pattern |
| M03 | Remove output-delay lines for gcd_out | TF201 ERROR | One output group has no delay pattern |
| M04 | Add set_false_path -from [all_inputs] | TF301 REVIEW | The broad exception is flagged for a human review |

## Run the benchmark

```bash
make benchmark
```

The command writes:
- build/benchmark_report.json
- build/benchmark_report.md
- build/mutants/*.sdc

The score is a **static text-pattern detection score for these four controlled examples only**. It does not measure arbitrary SDC correctness, does not prove a false-path exception is invalid, and does not quantify timing impact. The score must not be described as an STA signoff result.

## Next research extension

Run each mutation through the same mapped netlist, Liberty model, OpenSTA version, and analysis options as the golden baseline. Parse setup/hold reports and unconstrained endpoints. Record whether a path disappears or changes, while keeping the static checker finding separate from the STA observation.
