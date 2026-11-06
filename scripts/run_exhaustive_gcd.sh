#!/usr/bin/env bash
set -euo pipefail

mkdir -p build/formal
command -v iverilog >/dev/null
command -v vvp >/dev/null

iverilog -g2012 -s tb_gcd_exhaustive -o build/formal/gcd_exhaustive.vvp \
  rtl/gcd_binary_combined.sv rtl/gcd_binary_split.sv tb/tb_gcd_exhaustive.sv
vvp build/formal/gcd_exhaustive.vvp > build/formal/gcd_exhaustive.log 2>&1
cat build/formal/gcd_exhaustive.log
grep -q "EXHAUSTIVE_GCD_PASS width=8 pairs=65536" build/formal/gcd_exhaustive.log

python3 - <<'PY'
from pathlib import Path
for name in ("gcd_binary_combined", "gcd_binary_split"):
    source = Path("rtl") / f"{name}.sv"
    text = source.read_text(encoding="utf-8")
    old = "localparam integer SHIFT_WIDTH = (WIDTH < 2) ? 1 : $clog2(WIDTH + 1);"
    if old not in text:
        raise SystemExit(f"ERROR: N5 width mutant anchor missing in {source}")
    Path("build/formal", f"{name}_n5.sv").write_text(
        text.replace(old, "localparam integer SHIFT_WIDTH = 2;"), encoding="utf-8"
    )
PY

iverilog -g2012 -s tb_gcd_exhaustive -o build/formal/gcd_exhaustive_n5.vvp \
  build/formal/gcd_binary_combined_n5.sv build/formal/gcd_binary_split_n5.sv \
  tb/tb_gcd_exhaustive.sv
set +e
vvp build/formal/gcd_exhaustive_n5.vvp > build/formal/gcd_exhaustive_n5.log 2>&1
n5_status=$?
set -e
if [[ "$n5_status" -eq 0 ]] || ! grep -Eq "GCD mismatch|completion count mismatch" build/formal/gcd_exhaustive_n5.log; then
  echo "ERROR: exhaustive WIDTH=8 control did not reject shared SHIFT_WIDTH=2 mutant" >&2
  cat build/formal/gcd_exhaustive_n5.log
  exit 1
fi
echo "PASS: exhaustive WIDTH=8 reference check rejected shared SHIFT_WIDTH=2 mutant" | tee -a build/formal/gcd_exhaustive_n5.log
