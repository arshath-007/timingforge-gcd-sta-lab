# Generated reports

This directory is the local destination for generated Yosys/OpenSTA logs and parsed measurements. CI-generated evidence is uploaded as workflow artifacts rather than committed to the repository.

The corrected-load v0.2 baseline measurements are documented in [docs/INITIAL_RESULTS.md](../docs/INITIAL_RESULTS.md). Download raw STA logs and the parsed 16-run matrix from [run #136 artifact](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42013708525/artifacts/13406904777); download the static fault-injection scorecard from [the same run](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/runs/42013708525/artifacts/13408252094). Both CI jobs passed on source commit `66885ced80f9cea43977b576ba187dac671ff4e9`. The earlier run `41999231060` used incorrect 0.02/0.03 fF loads and is superseded for current numerical claims.

For every new or updated published result, record:
- Tool name and version.
- RTL top and commit SHA.
- Liberty/platform and process corner.
- SDC file and hash.
- Synthesis/STA commands and options.
- Whether parasitics are ideal, estimated, or extracted.

The checked-in measured-results document and CI artifacts are evidence for the educational, pre-layout v0.2 experiment. No raw generated report logs are committed in this directory. Do not describe these measurements as post-route PPA or production signoff.
