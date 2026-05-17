#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT_DIR/tools/env_gemmini_thermal.sh"

RUN_ROOT="${RUN_ROOT:-$ROOT_DIR/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff}"
DESIGN_CONFIG="${DESIGN_CONFIG:-$RUN_ROOT/physical/config/config.mk}"
PLATFORM_HOME="${PLATFORM_HOME:-$ROOT_DIR/configs/openroad/reduced_platforms}"
ORFS_MAKE_JOBS="${MAKE_JOBS:-1}"
ORFS_NUM_CORES="${NUM_CORES:-128}"
DR_END_ITER="${DETAILED_ROUTE_END_ITERATION:-16}"
FLOW_TARGETS=("$@")

if [ ${#FLOW_TARGETS[@]} -eq 0 ]; then
  FLOW_TARGETS=(synth)
fi

for forbidden in FLOW_VARIANT REMOVE_ABC_BUFFERS GPL_TIMING_DRIVEN SKIP_CTS_REPAIR_TIMING SKIP_REPORT_METRICS SKIP_LAST_GASP; do
  if [ -n "${!forbidden:-}" ]; then
    echo "Forbidden Stage 2 signoff fallback/debug knob is set: $forbidden=${!forbidden}" >&2
    exit 2
  fi
done

exec make -j "$ORFS_MAKE_JOBS" -C "$FLOW_HOME" \
  PLATFORM_HOME="$PLATFORM_HOME" \
  DESIGN_CONFIG="$DESIGN_CONFIG" \
  YOSYS_EXE="$YOSYS_EXE" \
  OPENROAD_EXE="$OPENROAD_EXE" \
  OPENSTA_EXE="$OPENSTA_EXE" \
  MAKE_JOBS="$ORFS_MAKE_JOBS" \
  NUM_CORES="$ORFS_NUM_CORES" \
  DETAILED_ROUTE_END_ITERATION="$DR_END_ITER" \
  "${FLOW_TARGETS[@]}"
