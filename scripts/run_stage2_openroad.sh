#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT_DIR/tools/env_gemmini_thermal.sh"

DESIGN_CONFIG="$ROOT_DIR/physical/stage2_tiled_matmul_os_baseline_asap7/config.mk"
PLATFORM_HOME="$ROOT_DIR/configs/openroad/reduced_platforms"
FLOW_TARGETS=("$@")

if [ ${#FLOW_TARGETS[@]} -eq 0 ]; then
  FLOW_TARGETS=(synth)
fi

ORFS_NUM_CORES="${NUM_CORES:-${MAKE_JOBS:-128}}"
ORFS_MAKE_JOBS="${MAKE_JOBS:-$ORFS_NUM_CORES}"

exec make -j "$ORFS_MAKE_JOBS" -C "$FLOW_HOME" \
  PLATFORM_HOME="$PLATFORM_HOME" \
  DESIGN_CONFIG="$DESIGN_CONFIG" \
  YOSYS_EXE="$YOSYS_EXE" \
  OPENROAD_EXE="$OPENROAD_EXE" \
  OPENSTA_EXE="$OPENSTA_EXE" \
  MAKE_JOBS="$ORFS_MAKE_JOBS" \
  NUM_CORES="$ORFS_NUM_CORES" \
  "${FLOW_TARGETS[@]}"
