# Phase 3 technology breadth results

This page is populated only from a successful `TimingForge technology breadth` GitHub Actions run. It must not be filled with estimates or results from a different tool/platform revision.

## Latest validated run

- Workflow: [TimingForge technology breadth](https://github.com/arshath-007/timingforge-gcd-sta-lab/actions/workflows/technology-breadth.yml)
- Run ID: pending first successful run
- Commit: pending
- Artifact: `timingforge-technology-breadth` (90-day retention)

## Expected experiments

| Platform | Architectures | Implementation | Timing analysis |
|---|---|---|---|
| ASAP7 | combined and split GCD | TC physical flow through detailed route and extraction | OpenSTA MCMM BC/TC/WC; one TC SPEF reused unchanged |
| SKY130HD | combined and split GCD | TT physical flow through detailed route and extraction | OpenSTA TT post-route using final SPEF |

Measured values, tool hashes, Liberty hashes, and artifact checksums are taken from `technology_breadth_manifest.json` after the first successful run. Until then, no numerical results are asserted here.

## Interpretation

The cross-library experiments test portability and flow integration. Absolute cell area, delay, or frequency values across ASAP7 and SKY130HD are not an apples-to-apples process comparison. Neither platform experiment is foundry signoff.
