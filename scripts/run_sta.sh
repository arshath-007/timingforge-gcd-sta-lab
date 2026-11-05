#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
: "${LIBERTY:?Set LIBERTY to a compatible standard-cell Liberty file}"
: "${NETLIST:?Set NETLIST to a mapped Verilog netlist}"
: "${SDC:?Set SDC to an SDC file}"
TOP="${TOP:-gcd_binary_combined}"
STA_BIN="${STA:-openroad}"
mkdir -p build/reports
if ! command -v "$STA_BIN" >/dev/null 2>&1; then
  echo "STA executable '$STA_BIN' was not found. Set STA=openroad or STA=sta." >&2
  exit 2
fi
LOG="build/reports/sta_${TOP}_$(basename "$SDC" .sdc).log"
"$STA_BIN" -exit scripts/run_sta.tcl 2>&1 | tee "$LOG"
echo "STA report log: $LOG"
