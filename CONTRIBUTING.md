# Contributing to TimingForge

Thank you for considering a contribution.

TimingForge is an educational benchmark for testing whether SDC constraint review catches controlled defects and whether those defects change the paths reported by an STA engine.

## Ground rules

- Keep the golden SDC separate from deliberately mutated SDC files.
- Never use a mutated SDC as a design constraint.
- Do not describe the prototype linter as a complete SDC parser or signoff checker.
- Do not commit invented timing, area, power, or frequency values.
- Every published measurement must include RTL top, source commit, tool versions, Liberty/platform revision, SDC scenario, and parasitic assumptions.
- Explain whether a result is static-linter evidence, synthesis evidence, pre-layout STA, or post-route analysis.

## Adding a new SDC fault

A useful fault contribution includes:
1. A short, realistic defect description and the design intent it violates.
2. A mutation generated from the golden SDC.
3. An expected linter rule ID and/or a specific STA observation.
4. A negative/control test showing that a valid SDC is not incorrectly rejected.
5. A unit test and a row in `docs/FAULT_CATALOG.md`.
6. Any limitations or cases the rule cannot safely decide.

## Running tests

```bash
make rtl-test
make python-test
make lint-sdc
make benchmark
```

For the library-backed educational matrix:

```bash
source /OpenROAD-flow-scripts/env.sh
make sta-matrix
```

Do not submit a change that makes the static regression fail. When changing STA scripts, inspect raw reports rather than relying only on a green exit status.

## Pull requests

Please describe the engineering question, the files changed, how to reproduce the result, what evidence was observed, and any remaining limitations. Link related issues where possible.
