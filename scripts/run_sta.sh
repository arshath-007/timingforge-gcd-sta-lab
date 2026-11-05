#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
: "$LIBERTY"
: "$NETLIST"
: "$SDC"
mkdir -p build
sta -exit scripts/run_sta.tcl 2>&1 | tee "build/sta_$(basename "$SDC" .sdc).log"
