#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ORFS_ROOT="${ORFS_ROOT:-/OpenROAD-flow-scripts}"
FLOW_ROOT="${ORFS_FLOW_ROOT:-$ORFS_ROOT/flow}"\nORFS_REV="11aa833a11488c3a540a1d8eb4caa23fd22df703"
if [[ ! -f "$ORFS_ROOT/env.sh" || ! -f "$FLOW_ROOT/Makefile" ]]; then
  echo "OpenROAD Flow Scripts not found under $ORFS_ROOT" >&2
  exit 2
fi
# Load the exact OpenROAD/Yosys environment supplied by the pinned ORFS image.
# shellcheck disable=SC1090
source "$ORFS_ROOT/env.sh"

PLATFORM_DIR="$FLOW_ROOT/platforms/nangate45"
LIBERTY="$PLATFORM_DIR/lib/NangateOpenCellLibrary_typical.lib"
TECH_LEF="$PLATFORM_DIR/lef/NangateOpenCellLibrary.tech.lef"
SC_LEF="$PLATFORM_DIR/lef/NangateOpenCellLibrary.macro.mod.lef"
for file in "$LIBERTY" "$TECH_LEF" "$SC_LEF"; do
  [[ -s "$file" ]] || { echo "Required Nangate45 file missing: $file" >&2; exit 2; }
done

mkdir -p build/physical
{
  echo "OpenROAD: $(openroad -version)"
  echo "Yosys: $(yosys -V)"
  echo "ORFS revision: $ACTUAL_REV"
  echo "Platform: Nangate45"
  echo "Corner: typical"
  echo "Liberty SHA256: $(sha256sum "$LIBERTY" | awk '{print $1}')"
  echo "SDC SHA256: $(sha256sum constraints/gcd_baseline.sdc | awk '{print $1}')"
} | tee build/physical/tool_versions.txt

for TOP in gcd_binary_combined gcd_binary_split; do
  WORK_HOME="$ROOT/build/physical/$TOP"
  CONFIG="$ROOT/physical/config/$TOP.mk"
  [[ -s "$CONFIG" ]] || { echo "Missing config: $CONFIG" >&2; exit 2; }
  rm -rf "$WORK_HOME"
  echo "=== OpenROAD RTL-to-GDS flow: $TOP ==="
  make -C "$FLOW_ROOT" DESIGN_CONFIG="$CONFIG" WORK_HOME="$WORK_HOME" all

  RESULTS="$WORK_HOME/results/nangate45/$TOP/base"
  for artifact in 2_floorplan.odb 3_place.odb 4_cts.odb 5_route.odb 6_final.odb 6_final.gds 6_final.spef 6_final.sdc; do
    [[ -s "$RESULTS/$artifact" ]] || {
      echo "ERROR: required physical-flow artifact missing: $RESULTS/$artifact" >&2
      find "$WORK_HOME" -maxdepth 6 -type f | sort >&2
      exit 1
    }
  done

  echo "=== Extracted-parasitic post-route STA: $TOP ==="
  export LIBERTY TECH_LEF SC_LEF
  export ODB="$RESULTS/6_final.odb"
  export SDC="$RESULTS/6_final.sdc"
  export SPEF="$RESULTS/6_final.spef"
  mkdir -p "$ROOT/build/physical/$TOP"
  openroad -exit "$ROOT/scripts/postroute_sta.tcl" 2>&1 \
    | tee "$ROOT/build/physical/$TOP/postroute_sta.log"
  grep -q "POST-ROUTE PARASITICS LOADED" "$ROOT/build/physical/$TOP/postroute_sta.log"
done

python3 -m tools.physical_manifest build/physical --output build/physical/physical_manifest.json
echo "Physical implementation and extracted-parasitic STA completed for both architectures."
