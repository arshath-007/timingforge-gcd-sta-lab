# TimingForge v0.2.2 — Functional Extension Verification

## Overview

This release candidate strengthens the functional regression and aligns project documentation with the implemented FIFO and MAC extension blocks.

## Changes

- Corrected the README roadmap to distinguish implemented functional FIFO/MAC blocks from future integration into the GCD STA matrix.
- Added FIFO directed checks for simultaneous read/write at non-full occupancy and simultaneous read/write while full, documenting the current implementation's behavior.
- Added MAC directed checks for the most-negative signed operand boundary case and synchronous clear priority over enable.
- Updated the interview guide to describe FIFO/MAC STA-matrix integration as future work, not as missing RTL functionality.
- Added conservative golden-result quality findings to the library-backed STA CI artifact.
- Added heuristic GCD critical-path classification (input-to-register, register-to-register, register-to-output, input-to-output, or unknown) to the parsed STA matrix report.
- Added unit tests for quality findings and path-class parsing.

## Verification

- GitHub Actions run #202: regression PASS; library-backed STA PASS.
- GitHub Actions run #203: regression PASS; library-backed STA PASS.
- Both runs execute the 16-scenario GCD Nangate45 matrix. FIFO and MAC remain functional-only extensions and are not included in that matrix.

## Scope and limitations

No new GCD PPA baseline or FIFO/MAC STA measurements are claimed. The published GCD timing evidence remains the existing educational, pre-layout, single typical Nangate45-corner result with ideal clocks and no extracted SPEF. The combined architecture's register-only minimum-period query remains unresolved, and its golden-SDC hold slack remains -0.002 ns.

This release is not a signoff qualification or a claim of production-ready timing closure.

**Previous release:** v0.2.1
