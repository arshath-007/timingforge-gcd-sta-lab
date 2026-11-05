#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VERILATOR="${VERILATOR:-verilator}"
command -v "$VERILATOR" >/dev/null
mkdir -p build
"$VERILATOR" --version | tee build/verilator_version.txt
"$VERILATOR" --binary --timing --assert --top-module tb_gcd_sva \
  --Mdir build/verilator_sva \
  rtl/gcd_binary_combined.sv rtl/gcd_binary_split.sv tb/tb_gcd_sva.sv
build/verilator_sva/Vtb_gcd_sva
