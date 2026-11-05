# Generated reports

This directory is the local destination for generated Yosys/OpenSTA logs and parsed measurements. CI-generated evidence is uploaded as workflow artifacts rather than committed to the repository.

The v0.2 baseline measurements are documented in [docs/INITIAL_RESULTS.md](../docs/INITIAL_RESULTS.md). Download the corresponding raw STA logs, parsed matrix, and static benchmark scorecard from the linked successful [baseline CI run](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/41999231060).

For every new or updated published result, record:
- Tool name and version.
- RTL top and commit SHA.
- Liberty/platform and process corner.
- SDC file and hash.
- Synthesis/STA commands and options.
- Whether parasitics are ideal, estimated, or extracted.

The checked-in measured-results document and CI artifacts are evidence for the educational, pre-layout v0.2 experiment. No raw generated report logs are committed in this directory. Do not describe these measurements as post-route PPA or production signoff.
