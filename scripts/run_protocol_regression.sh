#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
IVERILOG="${IVERILOG:-iverilog}"
VVP="${VVP:-vvp}"
command -v "$IVERILOG" >/dev/null
command -v "$VVP" >/dev/null
mkdir -p build/protocol
"$IVERILOG" -g2012 -s tb_gcd_protocol -o build/protocol/gcd_protocol.vvp \
  rtl/gcd_binary_combined.sv rtl/gcd_binary_split.sv tb/tb_gcd_protocol.sv
"$VVP" build/protocol/gcd_protocol.vvp | tee build/protocol/gcd_protocol.log
grep -q "PASS: busy-start rejection, mid-operation reset, restart and sequential transactions" \
  build/protocol/gcd_protocol.log
