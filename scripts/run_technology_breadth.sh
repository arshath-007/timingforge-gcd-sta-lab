#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ORFS_ROOT="${ORFS_ROOT:-/OpenROAD-flow-scripts}"
ORFS_IMAGE_DIGEST="sha256:f05cee3219a02f26289f02f00e11a3fc986ab51a482a0000a2da810cda219a6e"
if [[ ! -f "$ORFS_ROOT/env.sh" || ! -f "$ORFS_ROOT/flow/Makefile" ]]; then
  echo "OpenROAD Flow Scripts environment/Makefile not found under $ORFS_ROOT" >&2
  exit 2
fi
# shellcheck disable=SC1090
source "$ORFS_ROOT/env.sh"
FLOW_ROOT="$ORFS_ROOT/flow"
export TIMINGFORGE_ROOT="$ROOT"
export NUM_CORES=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export LEC_CHECK=0
export OPENROAD_EXE="$(command -v openroad)"
export YOSYS_EXE="$(command -v yosys)"
export KLAYOUT_CMD="$(command -v klayout || true)"
if [[ -z "$KLAYOUT_CMD" ]]; then
  apt-get update
  apt-get install -y klayout
  export KLAYOUT_CMD="$(command -v klayout)"
fi
[[ -x "$OPENROAD_EXE" && -x "$YOSYS_EXE" && -x "$KLAYOUT_CMD" ]] || {
  echo "Required OpenROAD/Yosys/KLayout executable missing" >&2
  exit 2
}

OUT="$ROOT/build/technology_breadth"
mkdir -p "$OUT"
{
  echo "OpenROAD: $(openroad -version)"
  echo "Yosys: $(yosys -V)"
  echo "ORFS container image digest: $ORFS_IMAGE_DIGEST"
  echo "ORFS source revision: $(git -C "$ORFS_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
} | tee "$OUT/tool_versions.txt"

for PLATFORM in asap7 sky130hd; do
  for TOP in gcd_binary_combined gcd_binary_split; do
    CONFIG="$ROOT/physical/config/${TOP}_${PLATFORM}.mk"
    WORK_HOME="$OUT/$PLATFORM/$TOP"
    [[ -s "$CONFIG" ]] || { echo "Missing config: $CONFIG" >&2; exit 2; }
    rm -rf "$WORK_HOME"
    echo "=== PHYSICAL IMPLEMENTATION: platform=$PLATFORM top=$TOP ==="
    if [[ "$PLATFORM" == "asap7" ]]; then
      make -C "$FLOW_ROOT" DESIGN_CONFIG="$CONFIG" WORK_HOME="$WORK_HOME" CORNER=TC all
      make -C "$FLOW_ROOT" DESIGN_CONFIG="$CONFIG" WORK_HOME="$WORK_HOME" CORNER=TC gds
    else
      make -C "$FLOW_ROOT" DESIGN_CONFIG="$CONFIG" WORK_HOME="$WORK_HOME" all
      make -C "$FLOW_ROOT" DESIGN_CONFIG="$CONFIG" WORK_HOME="$WORK_HOME" gds
    fi

    RESULTS="$WORK_HOME/results/$PLATFORM/$TOP/base"
    for artifact in 2_floorplan.odb 3_place.odb 4_cts.odb 5_route.odb 6_final.odb 6_final.gds 6_final.spef 6_final.sdc; do
      [[ -s "$RESULTS/$artifact" ]] || {
        echo "Missing required $PLATFORM physical artifact: $RESULTS/$artifact" >&2
        find "$WORK_HOME" -maxdepth 7 -type f | sort >&2
        exit 1
      }
    done

    if [[ "$PLATFORM" == "asap7" ]]; then
      export TECH_LEF="$FLOW_ROOT/platforms/asap7/lef/asap7_tech_1x_201209.lef"
      export SC_LEF="$FLOW_ROOT/platforms/asap7/lef/asap7sc7p5t_28_R_1x_220121a.lef"
      export ASAP7_LIB_DIR="$FLOW_ROOT/platforms/asap7/lib/NLDM"
      export ODB="$RESULTS/6_final.odb"
      export SDC="$RESULTS/6_final.sdc"
      export SPEF="$RESULTS/6_final.spef"
      echo "=== POST-ROUTE MCMM: ASAP7 BC/TC/WC top=$TOP ==="
      openroad -exit "$ROOT/scripts/asap7_mcmm_postroute.tcl" 2>&1 | tee "$WORK_HOME/asap7_mcmm_postroute.log"
      grep -q "TIMINGFORGE_ASAP7_MCMM_COMPLETE" "$WORK_HOME/asap7_mcmm_postroute.log"
    else
      export LIBERTY="$FLOW_ROOT/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
      export TECH_LEF="$FLOW_ROOT/platforms/sky130hd/lef/sky130_fd_sc_hd.tlef"
      export SC_LEF="$FLOW_ROOT/platforms/sky130hd/lef/sky130_fd_sc_hd_merged.lef"
      export ODB="$RESULTS/6_final.odb"
      export SDC="$RESULTS/6_final.sdc"
      export SPEF="$RESULTS/6_final.spef"
      echo "=== POST-ROUTE STA: SKY130HD TT top=$TOP ==="
      openroad -exit "$ROOT/scripts/postroute_sta.tcl" 2>&1 | tee "$WORK_HOME/sky130hd_postroute_sta.log"
      grep -q "POST-ROUTE PARASITICS LOADED" "$WORK_HOME/sky130hd_postroute_sta.log"
    fi
  done
done

python3 -m tools.technology_breadth --root "$OUT" --orfs-root "$ORFS_ROOT" --output "$OUT/technology_breadth_manifest.json"
echo "Technology-breadth physical and STA experiments completed."
