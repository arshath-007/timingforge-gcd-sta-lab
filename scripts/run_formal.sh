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

# Negative control: the same property must reject a deliberately broken RTL.
sed 's/x <= x - y;/x <= x - y + 1;/' rtl/gcd_binary_combined.sv > build/formal/gcd_binary_combined_broken.sv
if cmp -s rtl/gcd_binary_combined.sv build/formal/gcd_binary_combined_broken.sv; then
  echo "ERROR: formal negative-control mutation did not modify the RTL"
  exit 1
fi

yosys -p "read_verilog -formal -sv build/formal/gcd_binary_combined_broken.sv rtl/gcd_binary_split.sv formal/gcd_equiv.sv; prep -top gcd_equiv_formal; write_smt2 -wires build/formal/gcd_equiv_broken.smt2" \
  | tee build/formal/yosys_negative.log

set +e
yosys-smtbmc -s boolector -t 82 --noprogress --dump-vcd build/formal/gcd_equiv_negative.vcd build/formal/gcd_equiv_broken.smt2 \
  > build/formal/smtbmc_negative.log 2>&1
negative_status=$?
set -e

if [ "$negative_status" -eq 0 ] || ! grep -q "Status: FAILED" build/formal/smtbmc_negative.log; then
  echo "ERROR: formal proof did not reject the deliberately broken RTL"
  cat build/formal/smtbmc_negative.log
  exit 1
fi
echo "PASS: formal property rejected deliberately broken RTL" | tee -a build/formal/smtbmc_negative.log
