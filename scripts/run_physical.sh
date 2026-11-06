#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ORFS_ROOT="${ORFS_ROOT:-/OpenROAD-flow-scripts}"
EXPECTED_ORFS_IMAGE_DIGEST="sha256:f05cee3219a02f26289f02f00e11a3fc986ab51a482a0000a2da810cda219a6e"
ORFS_IMAGE_DIGEST="${ORFS_IMAGE_DIGEST:-$EXPECTED_ORFS_IMAGE_DIGEST}"
if [[ "$ORFS_IMAGE_DIGEST" != "$EXPECTED_ORFS_IMAGE_DIGEST" ]]; then
  echo "ORFS image digest mismatch: expected $EXPECTED_ORFS_IMAGE_DIGEST, received $ORFS_IMAGE_DIGEST" >&2
  exit 2
fi
export DESIGN_REPO_ROOT="$ROOT"
if [[ ! -f "$ORFS_ROOT/env.sh" || ! -f "$ORFS_ROOT/flow/Makefile" ]]; then
  echo "OpenROAD Flow Scripts environment/Makefile not found under $ORFS_ROOT" >&2
  exit 2
fi

# The pinned container supplies a matched ORFS source tree and tool binaries.
# shellcheck disable=SC1090
source "$ORFS_ROOT/env.sh"
FLOW_ROOT="$ORFS_ROOT/flow"
export FLOW_HOME="$FLOW_ROOT"
export YOSYS_EXE="$(command -v yosys)"
export OPENROAD_EXE="$(command -v openroad)"
export OPENSTA_EXE="$(command -v sta || true)"
export PYTHON_EXE="$(command -v python3)"
export KLAYOUT_CMD="$(command -v klayout)"
export NUM_CORES=1
export LEC_CHECK=0
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
[[ -x "$YOSYS_EXE" && -x "$OPENROAD_EXE" && -x "$PYTHON_EXE" && -x "$KLAYOUT_CMD" ]] || {
  echo "Required Yosys/OpenROAD/Python/KLayout executable missing from PATH" >&2
  exit 2
}

PLATFORM_DIR="$FLOW_ROOT/platforms/nangate45"
LIBERTY="$PLATFORM_DIR/lib/NangateOpenCellLibrary_typical.lib"
TECH_LEF="$PLATFORM_DIR/lef/NangateOpenCellLibrary.tech.lef"
SC_LEF="$PLATFORM_DIR/lef/NangateOpenCellLibrary.macro.mod.lef"
for file in "$LIBERTY" "$TECH_LEF" "$SC_LEF"; do
  [[ -s "$file" ]] || { echo "Required Nangate45 file missing: $file" >&2; exit 2; }
done

ORFS_SOURCE_REV="container-image-pinned"
if git -C "$ORFS_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  ORFS_SOURCE_REV="$(git -C "$ORFS_ROOT" rev-parse HEAD)"
fi

mkdir -p build/physical
export LIBERTY TECH_LEF SC_LEF
bash scripts/run_nangate_sta.sh

GIT_SHA="$(git -C "$ROOT" rev-parse HEAD)"
{
  echo "Git commit SHA: $GIT_SHA"
  echo "OpenROAD: $(openroad -version)"
  echo "Yosys: $(yosys -V)"
  echo "ORFS source revision: $ORFS_SOURCE_REV"
  echo "ORFS container image digest (declared by workflow): $ORFS_IMAGE_DIGEST"
  echo "Platform: Nangate45"
  echo "Corner: typical"
  echo "Liberty SHA256: $(sha256sum "$LIBERTY" | awk '{print $1}')"
  echo "Tech LEF SHA256: $(sha256sum "$TECH_LEF" | awk '{print $1}')"
  echo "Std-cell LEF SHA256: $(sha256sum "$SC_LEF" | awk '{print $1}')"
  echo "RTL SHA256 (rtl/gcd_binary_combined.sv): $(sha256sum rtl/gcd_binary_combined.sv | awk '{print $1}')"
  echo "RTL SHA256 (rtl/gcd_binary_split.sv): $(sha256sum rtl/gcd_binary_split.sv | awk '{print $1}')"
  echo "Script SHA256 (scripts/run_physical.sh): $(sha256sum scripts/run_physical.sh | awk '{print $1}')"
  echo "Script SHA256 (scripts/postroute_sta.tcl): $(sha256sum scripts/postroute_sta.tcl | awk '{print $1}')"
  echo "Script SHA256 (tools/physical_manifest.py): $(sha256sum tools/physical_manifest.py | awk '{print $1}')"
  echo "Script SHA256 (tools/physical_metrics.py): $(sha256sum tools/physical_metrics.py | awk '{print $1}')"
  echo "Script SHA256 (tools/physical_annotation.py): $(sha256sum tools/physical_annotation.py | awk '{print $1}')"
  echo "Source SDC SHA256: $(sha256sum constraints/gcd_baseline.sdc | awk '{print $1}')"
  echo "Config SHA256 (physical/config/gcd_binary_combined.mk): $(sha256sum physical/config/gcd_binary_combined.mk | awk '{print $1}')"
  echo "Config SHA256 (physical/config/gcd_binary_split.mk): $(sha256sum physical/config/gcd_binary_split.mk | awk '{print $1}')"
  echo "Workflow SHA256 (.github/workflows/physical-design.yml): $(sha256sum .github/workflows/physical-design.yml | awk '{print $1}')"
} | tee build/physical/tool_versions.txt

for TOP in gcd_binary_combined gcd_binary_split; do
  WORK_HOME="$ROOT/build/physical/$TOP"
  CONFIG="$ROOT/physical/config/$TOP.mk"
  [[ -s "$CONFIG" ]] || { echo "Missing config: $CONFIG" >&2; exit 2; }
  rm -rf "$WORK_HOME"
  echo "=== OpenROAD RTL-to-GDS flow: $TOP ==="
  make -C "$FLOW_ROOT" DESIGN_CONFIG="$CONFIG" WORK_HOME="$WORK_HOME" all
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
  openroad -exit "$ROOT/scripts/postroute_sta.tcl" 2>&1 | tee "$ROOT/build/physical/$TOP/postroute_sta.log"
  grep -q "POST-ROUTE PARASITICS LOADED" "$ROOT/build/physical/$TOP/postroute_sta.log"
done

python3 -m tools.physical_manifest build/physical --output build/physical/physical_manifest.json --repo-root "$ROOT"
echo "Physical implementation and extracted-parasitic STA completed for both architectures."
