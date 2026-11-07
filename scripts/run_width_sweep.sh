#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
IVERILOG="${IVERILOG:-iverilog}"
VVP="${VVP:-vvp}"
command -v "$IVERILOG" >/dev/null
command -v "$VVP" >/dev/null
mkdir -p build/width_sweep

echo "=== EXHAUSTIVE 3-BIT GCD ORACLE CHECK ==="
"$IVERILOG" -g2012 -s tb_gcd_oracle3 -o build/width_sweep/gcd_oracle3.vvp \
  formal/gcd_oracle_3bit.sv tb/tb_gcd_oracle3.sv
"$VVP" build/width_sweep/gcd_oracle3.vvp

for width in 8 16 32; do
  echo "=== PARAMETERIZED GCD WIDTH SWEEP: WIDTH=$width ==="
  "$IVERILOG" -g2012 -s tb_gcd_width_sweep -Ptb_gcd_width_sweep.WIDTH="$width" \
    -o "build/width_sweep/gcd_width_$width.vvp" \
    rtl/gcd_binary_combined.sv rtl/gcd_binary_split.sv tb/tb_gcd_width_sweep.sv
  "$VVP" "build/width_sweep/gcd_width_$width.vvp"
done
