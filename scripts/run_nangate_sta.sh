#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LIB_DIR="build/platform/nangate45"
LIBERTY="${LIBERTY:-$LIB_DIR/NangateOpenCellLibrary_typical.lib}"
LIBERTY_URL="https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/master/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib"
STA="${STA:-openroad}"

if ! command -v yosys >/dev/null 2>&1; then
  echo "Yosys is required but was not found in PATH." >&2
  exit 2
fi
if ! command -v "$STA" >/dev/null 2>&1; then
  echo "STA executable '$STA' was not found in PATH." >&2
  exit 2
fi

mkdir -p "$LIB_DIR" build/netlists build/reports
if [[ ! -s "$LIBERTY" ]]; then
  echo "Downloading the educational Nangate45 typical Liberty file..."
  if ! command -v curl >/dev/null 2>&1; then
    echo "curl is required to download the library, or set LIBERTY to a local file." >&2
    exit 2
  fi
  curl --fail --location --silent --show-error "$LIBERTY_URL" --output "$LIBERTY"
fi
export LIBERTY

python3 -m tools.make_mutants
SDCS=("constraints/gcd_baseline.sdc")
while IFS= read -r file; do SDCS+=("$file"); done < <(find build/mutants -maxdepth 1 -type f -name '*.sdc' | sort)

for TOP in gcd_binary_combined gcd_binary_split; do
  echo "=== SYNTHESIS: $TOP ==="
  export TOP
  bash scripts/synth.sh
  export NETLIST="build/$TOP.v"
  for SDC in "${SDCS[@]}"; do
    echo "=== STA: top=$TOP sdc=$SDC ==="
    export SDC
    export STA
    bash scripts/run_sta.sh
  done
done

python3 -m tools.parse_sta_matrix
cat build/reports/sta_matrix_summary.md
echo "Completed synthesis for both architectures and STA for ${#SDCS[@]} SDC scenarios."
echo "Review build/yosys_*.log and build/reports/sta_*.log."
