#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
: "${LIBERTY:?Set LIBERTY to the Nangate45 Liberty file}"
command -v yosys >/dev/null
mkdir -p build/netlist_equiv

for TOP in gcd_binary_combined gcd_binary_split; do
  GATE_TOP="${TOP}_mapped_gate"
  GATE_NETLIST="build/netlist_equiv/${GATE_TOP}.v"
  python3 - "$TOP" "build/$TOP.v" "$GATE_NETLIST" <<'PY'
import sys
from pathlib import Path
top, source, output = sys.argv[1:]
text = Path(source).read_text(encoding="utf-8")
old = f"module {top}("
new = f"module {top}_mapped_gate("
if text.count(old) != 1:
    raise SystemExit(f"expected one top module declaration {old!r} in {source}")
Path(output).write_text(text.replace(old, new, 1), encoding="utf-8")
PY

  echo "=== RTL-to-mapped-netlist equivalence: $TOP ==="
  yosys -p "read_liberty -ignore_miss_func $LIBERTY; read_verilog -sv rtl/$TOP.sv $GATE_NETLIST; proc; memory; opt; equiv_make -inames $TOP $GATE_TOP equiv_$TOP; hierarchy -check -top equiv_$TOP; flatten; techmap; opt; equiv_simple; equiv_induct -seq 8; equiv_status -assert" \
    2>&1 | tee "build/netlist_equiv/${TOP}.log"
  grep -q "Equivalence successfully proven" "build/netlist_equiv/${TOP}.log"
done

echo "PASS: both Nangate45 mapped netlists are sequentially equivalent to their RTL sources"
