#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ORFS_ROOT="${ORFS_ROOT:-/OpenROAD-flow-scripts}"
ORFS_REV="11aa833a11488c3a540a1d8eb4caa23fd22df703"
if [[ ! -f "$ORFS_ROOT/env.sh" ]]; then
  echo "OpenROAD Flow Scripts environment not found under $ORFS_ROOT" >&2
  exit 2
fi

# Load the tool binaries from the pinned ORFS container image.
# shellcheck disable=SC1090
source "$ORFS_ROOT/env.sh"

# Use the exact ORFS source revision used to pin the pre-layout Nangate45 files.
mkdir -p build/physical
ORFS_SOURCE="$ROOT/build/physical/OpenROAD-flow-scripts"
if [[ ! -d "$ORFS_SOURCE/.git" ]]; then
  git clone --filter=blob:none --no-checkout https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git "$ORFS_SOURCE"
fi
git -C "$ORFS_SOURCE" fetch --depth=1 origin "$ORFS_REV"
git -C "$ORFS_SOURCE" checkout --detach FETCH_HEAD
ACTUAL_REV="$(git -C "$ORFS_SOURCE" rev-parse HEAD)"
[[ "$ACTUAL_REV" == "$ORFS_REV" ]] || {
  echo "ORFS revision mismatch: expected $ORFS_REV, got $ACTUAL_REV" >&2
  exit 2
}
FLOW_ROOT="$ORFS_SOURCE/flow"
export FLOW_HOME="$FLOW_ROOT"
[[ -f "$FLOW_ROOT/Makefile" ]] || { echo "ORFS flow Makefile missing: $FLOW_ROOT" >&2; exit 2; }

PLATFORM_DIR="$FLOW_ROOT/platforms/nangate45"
LIBERTY="$PLATFORM_DIR/lib/NangateOpenCellLibrary_typical.lib"
TECH_LEF="$PLATFORM_DIR/lef/NangateOpenCellLibrary.tech.lef"
SC_LEF="$PLATFORM_DIR/lef/NangateOpenCellLibrary.macro.mod.lef"
for file in "$LIBERTY" "$TECH_LEF" "$SC_LEF"; do
  [[ -s "$file" ]] || { echo "Required Nangate45 file missing: $file" >&2; exit 2; }
done

# Run the 16-scenario pre-layout matrix using this same pinned platform.
export LIBERTY TECH_LEF SC_LEF
bash scripts/run_nangate_sta.sh

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
  # ORFS 'all' completes routing and extraction; GDS is a separate KLayout target.
  make -C "$FLOW_ROOT" DESIGN_CONFIG="$CONFIG" WORK_HOME="$WORK_HOME" gds

  RESULTS="$WORK_HOME/results/nangate45/$TOP/base"
  for artifact in 2_floorplan.odb 3_place.odb 4_cts.odb 5_route.odb 6_final.odb 6_final.gds 6_final.spef 6_final.sdc; do
    [[ -s "$RESULTS/$artifact" ]] || {
      echo "ERROR: required physical-flow artifact missing: $RESULTS/$artifact" >&2
      find "$WORK_HOME" -maxdepth 7 -type f | sort >&2
      exit 1
    }
  done

  echo "=== Extracted-parasitic post-route STA: $TOP ==="
  export ODB="$RESULTS/6_final.odb"
  export SDC="$RESULTS/6_final.sdc"
  export SPEF="$RESULTS/6_final.spef"
  openroad -exit "$ROOT/scripts/postroute_sta.tcl" 2>&1 \
    | tee "$ROOT/build/physical/$TOP/postroute_sta.log"
  grep -q "POST-ROUTE PARASITICS LOADED" "$ROOT/build/physical/$TOP/postroute_sta.log"
done

python3 -m tools.physical_manifest build/physical --output build/physical/physical_manifest.json
echo "Physical implementation and extracted-parasitic STA completed for both architectures."
