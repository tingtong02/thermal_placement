#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CONFIG="${CONFIG:-GemminiRocketConfig}"
MAKE_JOBS="${MAKE_JOBS:-$(nproc)}"
BUILD_SIM="${BUILD_SIM:-0}"
BUILD_DEBUG_SIM="${BUILD_DEBUG_SIM:-0}"
SBT_CMD="${SBT_CMD:-sbt -batch -Dsbt.log.noformat=true}"

source "$ROOT/tools/env_gemmini_thermal.sh"

SIM_DIR="$CHIPYARD_HOME/sims/verilator"
LONG_NAME="chipyard.harness.TestHarness.$CONFIG"
BUILD_DIR="$SIM_DIR/generated-src/$LONG_NAME"
GEN_COLLATERAL_DIR="$BUILD_DIR/gen-collateral"
EXPORT_DIR="$ROOT/rtl_exports/generated-verilog/$CONFIG"

run_make() {
  env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
    make -C "$SIM_DIR" CONFIG="$CONFIG" SBT="$SBT_CMD" "$@"
}

echo "==> generating Verilog for CONFIG=$CONFIG"
run_make -j "$MAKE_JOBS" verilog

if [[ ! -d "$GEN_COLLATERAL_DIR" ]]; then
  echo "missing generated collateral: $GEN_COLLATERAL_DIR" >&2
  exit 1
fi

echo "==> exporting generated collateral to $EXPORT_DIR"
mkdir -p "$EXPORT_DIR"
rsync -a --delete "$GEN_COLLATERAL_DIR/" "$EXPORT_DIR/gen-collateral/"

for artifact in \
  "$BUILD_DIR/$LONG_NAME.fir" \
  "$BUILD_DIR/$LONG_NAME.anno.json" \
  "$BUILD_DIR/$LONG_NAME.appended.anno.json" \
  "$BUILD_DIR/$LONG_NAME.chisel.log" \
  "$BUILD_DIR/$LONG_NAME.firtool.log" \
  "$BUILD_DIR/$LONG_NAME.all.f" \
  "$BUILD_DIR/$LONG_NAME.model.f" \
  "$BUILD_DIR/$LONG_NAME.top.f" \
  "$BUILD_DIR/$LONG_NAME.bb.f" \
  "$BUILD_DIR/model_module_hierarchy.json" \
  "$BUILD_DIR/model_module_hierarchy.uniquified.json" \
  "$BUILD_DIR/top_module_hierarchy.json"; do
  if [[ -f "$artifact" ]]; then
    cp -f "$artifact" "$EXPORT_DIR/"
  fi
done

cat > "$EXPORT_DIR/manifest.txt" <<EOF
config=$CONFIG
long_name=$LONG_NAME
chipyard_home=$CHIPYARD_HOME
chipyard_commit=$(git -C "$CHIPYARD_HOME" rev-parse --short HEAD)
gemmini_commit=$(git -C "$GEMMINI_HOME" rev-parse --short HEAD)
source_build_dir=$BUILD_DIR
source_gen_collateral_dir=$GEN_COLLATERAL_DIR
export_dir=$EXPORT_DIR
generated_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

if [[ "$BUILD_SIM" == "1" ]]; then
  echo "==> building non-debug Verilator simulator"
  run_make -j "$MAKE_JOBS"
fi

if [[ "$BUILD_DEBUG_SIM" == "1" ]]; then
  echo "==> building debug Verilator simulator with waveform support"
  run_make -j "$MAKE_JOBS" debug
fi

echo "==> inspecting Gemmini module hierarchy"
python "$ROOT/scripts/inspect_gemmini_hierarchy.py" \
  --rtl-dir "$EXPORT_DIR/gen-collateral" \
  --hierarchy-json "$EXPORT_DIR/model_module_hierarchy.uniquified.json" \
  --out-md "$ROOT/reports/notes/gemmini_module_inventory.md" \
  --out-yaml "$ROOT/configs/gemmini/hierarchy_map.yaml"

echo "Gemmini RTL generation complete"
echo "  RTL export: $EXPORT_DIR"
echo "  inventory: $ROOT/reports/notes/gemmini_module_inventory.md"
echo "  hierarchy map: $ROOT/configs/gemmini/hierarchy_map.yaml"
