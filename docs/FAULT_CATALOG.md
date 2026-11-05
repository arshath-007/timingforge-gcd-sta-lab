# SDC fault catalog

TimingForge v0.2 uses named edits to the illustrative GCD baseline. Each mutation is generated from the baseline so the change is traceable.

| ID | Deliberate edit | Expected checker finding | Interpretation |
|---|---|---|---|
| M01 | Remove create_clock | TF001 ERROR | No primary clock command remains |
| M02 | Remove input-delay lines for a_in | TF101 ERROR | One input group has no input arrival budget |
| M03 | Remove output-delay lines for gcd_out | TF201 ERROR | One output group has no output required-time budget |
| M04 | Add broad set_false_path | TF301 REVIEW | Exception needs human design-intent review |
| M05 | Rename a_in* timing collection to a_input* | TF101 ERROR | Similar-looking port names are not interchangeable |
| M06 | Remove hold clock uncertainty | TF402 ERROR | Hold margin assumption is absent |
| M07 | Set clock period to zero | TF002 ERROR | Non-positive clock period is invalid |

## Run the benchmark

```bash
make benchmark
```

The command writes:
- build/benchmark_report.json
- build/benchmark_report.md
- build/mutants/*.sdc

The detection score is a **static coverage score for these seven controlled examples only**. It does not measure arbitrary SDC correctness, prove that a false-path exception is invalid, or quantify timing impact. It must not be described as an STA signoff result.

## Next research extension

Run each mutation through the same mapped netlist, Liberty model, OpenSTA version, and analysis options as the golden baseline. Parse setup/hold reports and unconstrained endpoints. Record whether a path disappears or changes, while keeping the static checker finding separate.
