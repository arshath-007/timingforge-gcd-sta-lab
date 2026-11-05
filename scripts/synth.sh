#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
: "$LIBERTY"
TOP="$(printenv TOP || printf 'gcd_binary_combined')"
SRC="rtl/$TOP.sv"
mkdir -p build
if [ ! -f "$SRC" ]; then
  echo "RTL top not found: $SRC" >&2
  exit 2
fi
yosys -p "read_verilog -sv $SRC; hierarchy -check -top $TOP; synth -top $TOP; dfflibmap -liberty $LIBERTY; abc -liberty $LIBERTY; clean; stat -liberty $LIBERTY; write_verilog -noattr build/$TOP.v" 2>&1 | tee "build/yosys_$TOP.log"
echo "Netlist: build/$TOP.v"
