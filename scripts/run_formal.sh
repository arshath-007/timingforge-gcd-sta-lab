#!/usr/bin/env bash
set -euo pipefail

mkdir -p build/formal
command -v yosys >/dev/null
command -v yosys-smtbmc >/dev/null
command -v boolector >/dev/null

{
  echo "Yosys: $(yosys -V)"
  echo "Solver: $(boolector --version 2>&1 | head -n 1)"
  echo "Proof: bounded transaction-level equivalence, WIDTH=8, depth=82"
} | tee build/formal/tool_versions.txt

yosys -p "read_verilog -formal -sv rtl/gcd_binary_combined.sv rtl/gcd_binary_split.sv formal/gcd_equiv.sv; prep -top gcd_equiv_formal; write_smt2 -wires build/formal/gcd_equiv.smt2" \
  | tee build/formal/yosys.log

yosys-smtbmc -s boolector -t 82 --noprogress --dump-vcd build/formal/gcd_equiv.vcd build/formal/gcd_equiv.smt2 \
  | tee build/formal/smtbmc.log

grep -q "Status: PASSED" build/formal/smtbmc.log
