#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
rm -rf build/formal
mkdir -p build/formal
command -v yosys >/dev/null
command -v yosys-smtbmc >/dev/null
command -v cvc5 >/dev/null
command -v iverilog >/dev/null
command -v vvp >/dev/null
command -v timeout >/dev/null

EXPECTED_YOSYS="Yosys 0.33 (git sha1 2584903a060)"
EXPECTED_CVC5="This is cvc5 version 1.1.2"
ACTUAL_YOSYS="$(yosys -V)"
ACTUAL_CVC5="$(cvc5 --version 2>&1 | head -n 1)"
[[ "$ACTUAL_YOSYS" == "$EXPECTED_YOSYS" ]] || { echo "ERROR: expected $EXPECTED_YOSYS, found $ACTUAL_YOSYS" >&2; exit 2; }
[[ "$ACTUAL_CVC5" == "$EXPECTED_CVC5" ]] || { echo "ERROR: expected $EXPECTED_CVC5, found $ACTUAL_CVC5" >&2; exit 2; }

{
  echo "Yosys: $ACTUAL_YOSYS"
  echo "Solver: cvc5 1.1.2"
  echo "Proof: WIDTH=3 and WIDTH=4 bounded transaction equivalence plus independent Euclidean GCD specification"
  echo "Timeout policy: 180s first attempt; retry once for 300s only after timeout"
} | tee build/formal/tool_versions.txt
printf "proof,attempt,timeout_seconds,elapsed_seconds,exit_code\n" > build/formal/solver_timings.csv

build_smt2() {
  local width="$1" combined="$2" split="$3" prefix="$4" depth="$5"
  yosys -p "read_verilog -formal -sv $combined $split formal/gcd_equiv.sv; chparam -set WIDTH $width gcd_equiv_formal; prep -top gcd_equiv_formal; write_smt2 -wires build/formal/$prefix.smt2" \
    > "build/formal/${prefix}_yosys.log" 2>&1
}

run_solver() {
  local prefix="$1" depth="$2" expected="$3"
  local timeout_seconds=180 attempt status start end elapsed
  for attempt in 1 2; do
    start="$(date +%s)"
    set +e
    timeout --signal=TERM --kill-after=10s "${timeout_seconds}s" \
      yosys-smtbmc -s cvc5 -t "$depth" \
      --dump-vcd "build/formal/${prefix}_attempt${attempt}.vcd" \
      "build/formal/${prefix}.smt2" \
      > "build/formal/${prefix}_attempt${attempt}.log" 2>&1
    status=$?
    set -e
    end="$(date +%s)"
    elapsed=$((end - start))
    echo "$prefix,$attempt,$timeout_seconds,$elapsed,$status" >> build/formal/solver_timings.csv
    cat "build/formal/${prefix}_attempt${attempt}.log"

    if [[ "$status" -eq 124 || "$status" -eq 137 ]]; then
      if [[ "$attempt" -eq 1 ]]; then
        timeout_seconds=300
        echo "WARN: $prefix timed out; retrying once with ${timeout_seconds}s"
        continue
      fi
      echo "ERROR: $prefix timed out after retry" >&2
      return 1
    fi
    if [[ "$expected" == "pass" ]]; then
      if [[ "$status" -eq 0 ]] && grep -q "Status: PASSED" "build/formal/${prefix}_attempt${attempt}.log"; then
        cp "build/formal/${prefix}_attempt${attempt}.log" "build/formal/${prefix}.log"
        echo "PASS: $prefix"
        return 0
      fi
      echo "ERROR: expected $prefix to pass" >&2
      return 1
    fi
    if [[ "$status" -ne 0 ]] && grep -q "Status: FAILED" "build/formal/${prefix}_attempt${attempt}.log"; then
      cp "build/formal/${prefix}_attempt${attempt}.log" "build/formal/${prefix}.log"
      echo "PASS: negative control $prefix was rejected"
      return 0
    fi
    echo "ERROR: expected negative control $prefix to fail an assertion" >&2
    return 1
  done
}

run_proof() {
  local width="$1" combined="$2" split="$3" prefix="$4" expected="$5"
  local max_cycles depth
  max_cycles=$((2 * ((1 << width) - 2) + 4))
  depth=$((max_cycles + 2))
  build_smt2 "$width" "$combined" "$split" "$prefix" "$depth"
  run_solver "$prefix" "$depth" "$expected"
}

run_proof 3 rtl/gcd_binary_combined.sv rtl/gcd_binary_split.sv baseline_w3 pass
run_proof 4 rtl/gcd_binary_combined.sv rtl/gcd_binary_split.sv baseline_w4 pass

python3 -m tools.make_formal_mutants
run_proof 3 build/formal/n1_combined.sv build/formal/n1_split.sv negative_n1_single_rtl fail
run_proof 3 build/formal/n3_combined.sv build/formal/n3_split.sv negative_n3_common_zero fail
run_proof 3 build/formal/n4_combined.sv build/formal/n4_split.sv negative_n4_common_shift fail
run_proof 3 build/formal/n6_combined.sv build/formal/n6_split.sv negative_n6_truncated_compare fail

bash scripts/run_exhaustive_gcd.sh

echo "=== Formal solver timing summary ==="
cat build/formal/solver_timings.csv
