#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ORFS_ROOT="${ORFS_ROOT:-/OpenROAD-flow-scripts}"
EXPECTED_ORFS_IMAGE_DIGEST="sha256:f05cee3219a02f26289f02f00e11a3fc986ab51a482a0000a2da810cda219a6e"
ORFS_IMAGE_DIGEST="${ORFS_IMAGE_DIGEST:-}"
if [[ "$ORFS_IMAGE_DIGEST" != "$EXPECTED_ORFS_IMAGE_DIGEST" ]]; then
  echo "ERROR: physical experiments require declared ORFS digest $EXPECTED_ORFS_IMAGE_DIGEST" >&2
  exit 2
fi
[[ -f "$ORFS_ROOT/env.sh" && -f "$ORFS_ROOT/flow/Makefile" ]] || {
  echo "ERROR: ORFS source tree missing under $ORFS_ROOT" >&2
  exit 2
}
source "$ORFS_ROOT/env.sh"
FLOW_ROOT="$ORFS_ROOT/flow"
export FLOW_HOME="$FLOW_ROOT"
export DESIGN_REPO_ROOT="$ROOT"
export LIBERTY="$FLOW_ROOT/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib"
export TECH_LEF="$FLOW_ROOT/platforms/nangate45/lef/NangateOpenCellLibrary.tech.lef"
export SC_LEF="$FLOW_ROOT/platforms/nangate45/lef/NangateOpenCellLibrary.macro.mod.lef"
export NUM_CORES=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export LEC_CHECK=0
FLOW_TIMEOUT_SECONDS="${FLOW_TIMEOUT_SECONDS:-1800}"
SOURCE_SHA="$(git rev-parse HEAD)"
ROOT_OUT="$ROOT/build/physical_experiments"
mkdir -p "$ROOT_OUT/configs"

{
  echo "Git commit SHA: $SOURCE_SHA"
  echo "ORFS image digest (workflow-declared): $ORFS_IMAGE_DIGEST"
  echo "Yosys: $(yosys -V)"
  echo "OpenROAD: $(openroad -version)"
  echo "GPL_RANDOM_SEED: varied per placement experiment"
  echo "GRT_SEED: varied per placement experiment"
} > "$ROOT_OUT/tool_versions.txt"

write_config() {
  local top="$1" util="$2" density="$3" sdc="$4" output="$5"
  python3 - "$ROOT/physical/config/$top.mk" "$util" "$density" "$sdc" "$output" <<'PY'
import sys
from pathlib import Path
source, util, density, sdc, output = sys.argv[1:]
text = Path(source).read_text(encoding="utf-8")
text = text.replace(
    "export SDC_FILE = $(DESIGN_REPO_ROOT)/constraints/gcd_baseline.sdc",
    f"export SDC_FILE = {sdc}",
)
text = text.replace("export CORE_UTILIZATION = 35", f"export CORE_UTILIZATION = {util}")
text = text.replace("export PLACE_DENSITY = 0.60", f"export PLACE_DENSITY = {density}")
Path(output).write_text(text, encoding="utf-8")
PY
}

write_period_sdc() {
  local period="$1" output="$2"
  python3 - "$ROOT/constraints/gcd_baseline.sdc" "$period" "$output" <<'PY'
import sys
from pathlib import Path
source, period, output = sys.argv[1:]
text = Path(source).read_text(encoding="utf-8")
old = "-period 10.000"
if text.count(old) != 1:
    raise SystemExit("expected one golden create_clock period")
Path(output).write_text(text.replace(old, f"-period {float(period):.3f}", 1), encoding="utf-8")
PY
}

run_one() {
  local experiment="$1" variant="$2" top="$3" util="$4" density="$5" seed="$6" period="$7" sdc="$8"
  local run_dir="$ROOT_OUT/$experiment/$variant/$top"
  local config="$ROOT_OUT/configs/${experiment}_${variant}_${top}.mk"
  local status=0 flow_status="success"
  mkdir -p "$run_dir"
  write_config "$top" "$util" "$density" "$sdc" "$config"

  echo "=== $experiment/$variant/$top util=$util density=$density seed=$seed period=$period ==="
  set +e
  timeout --signal=TERM --kill-after=30s "${FLOW_TIMEOUT_SECONDS}s" \
    make -C "$FLOW_ROOT" DESIGN_CONFIG="$config" WORK_HOME="$run_dir" \
      GPL_RANDOM_SEED="$seed" GRT_SEED="$seed" all \
      > "$run_dir/flow.log" 2>&1
  status=$?
  set -e
  if [[ "$status" -ne 0 ]]; then
    flow_status="flow_failed"
    echo "WARN: $experiment/$variant/$top flow failed with exit code $status"
    tail -n 40 "$run_dir/flow.log" || true
  else
    local results="$run_dir/results/nangate45/$top/base"
    if [[ ! -s "$results/6_final.odb" || ! -s "$results/6_final.spef" || ! -s "$results/6_final.v" ]]; then
      flow_status="final_artifacts_missing"
    else
      export ODB="$results/6_final.odb" SDC="$results/6_final.sdc" SPEF="$results/6_final.spef"
      set +e
      openroad -exit "$ROOT/scripts/postroute_sta.tcl" > "$run_dir/postroute_sta.log" 2>&1
      status=$?
      set -e
      if [[ "$status" -ne 0 ]]; then flow_status="postroute_sta_failed"; fi
    fi
  fi

  python3 - "$run_dir/metadata.json" "$experiment" "$variant" "$top" "$util" "$density" "$seed" "$period" "$SOURCE_SHA" "$ORFS_IMAGE_DIGEST" "$flow_status" "$status" <<'PY'
import json, sys
from pathlib import Path
path, experiment, variant, top, util, density, seed, period, sha, digest, flow_status, exit_code = sys.argv[1:]
data = {
    "experiment": experiment, "variant": variant, "top": top,
    "core_utilization": int(util), "place_density": float(density),
    "gpl_random_seed": int(seed), "grt_seed": int(seed),
    "clock_period_ns": None if period == "none" else float(period),
    "source_sha": sha, "orfs_image_digest_declared": digest,
    "flow_status": flow_status, "flow_exit_code": int(exit_code),
}
Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
}

while read -r variant util density seed; do
  [[ -n "$variant" ]] || continue
  for top in gcd_binary_combined gcd_binary_split; do
    run_one variance "$variant" "$top" "$util" "$density" "$seed" none "$ROOT/constraints/gcd_baseline.sdc"
  done
done <<'VARIATIONS'
v1_baseline 35 0.60 1
v2_low_util_low_density 30 0.55 2
v3_low_util_high_density 30 0.65 3
v4_high_util_low_density 40 0.55 4
v5_high_util_high_density 40 0.65 5
VARIATIONS

for period in 3.000 2.500 2.000 1.500 1.200 1.000; do
  variant="period_${period//./p}"
  sdc="$ROOT_OUT/configs/${variant}.sdc"
  write_period_sdc "$period" "$sdc"
  for top in gcd_binary_combined gcd_binary_split; do
    run_one clock_sweep "$variant" "$top" 35 0.60 1 "$period" "$sdc"
  done
done

python3 -m tools.physical_experiments "$ROOT_OUT" --output "$ROOT_OUT/physical_experiments_summary.json"
