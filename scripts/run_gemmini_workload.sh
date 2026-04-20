#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT_DIR/tools/env_gemmini_thermal.sh"

CONFIG="${CONFIG:-GemminiRocketConfig}"
MAKE_JOBS="${MAKE_JOBS:-$(nproc)}"
TEST_NAME="${1:-mvin_mvout}"
RUN_TAG="${RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
BUILD_DEBUG_SIM="${BUILD_DEBUG_SIM:-1}"
USE_FST="${USE_FST:-0}"

SIM_DIR="$CHIPYARD_HOME/sims/verilator"
LONG_NAME="chipyard.harness.TestHarness.${CONFIG}"
OUTPUT_DIR="$SIM_DIR/output/$LONG_NAME"
BINARY_ROOT="$ROOT_DIR/sim/binaries/$CONFIG"

mkdir -p "$ROOT_DIR/sim/binaries/$CONFIG" "$ROOT_DIR/sim/logs/$CONFIG" "$ROOT_DIR/sim/waves/$CONFIG"

binary_name="$TEST_NAME"
if [[ "$binary_name" != *-baremetal ]]; then
  binary_name="${binary_name}-baremetal"
fi

binary_path="$BINARY_ROOT/$binary_name"
if [ ! -f "$binary_path" ]; then
  binary_path="$GEMMINI_HOME/software/gemmini-rocc-tests/build/bareMetalC/$binary_name"
fi

if [ ! -f "$binary_path" ]; then
  echo "Binary not found: $binary_name" >&2
  echo "Build it first with scripts/build_gemmini_workloads.sh $TEST_NAME" >&2
  exit 1
fi

if [ "$(readlink -f "$binary_path")" != "$(readlink -f "$BINARY_ROOT/$binary_name")" ]; then
  cp -f "$binary_path" "$BINARY_ROOT/"
fi
binary_path="$BINARY_ROOT/$binary_name"

if [ "$BUILD_DEBUG_SIM" = "1" ] || [ ! -x "$SIM_DIR/simulator-chipyard.harness-$CONFIG-debug" ]; then
  echo "==> building Verilator debug simulator for $CONFIG with MAKE_JOBS=$MAKE_JOBS"
  make -C "$SIM_DIR" -j "$MAKE_JOBS" CONFIG="$CONFIG" debug
fi

echo "==> running $binary_name with waveform dump"
make -C "$SIM_DIR" \
  CONFIG="$CONFIG" \
  USE_FST="$USE_FST" \
  DUMP_BINARY=0 \
  EXTRA_SIM_OUT_NAME="$RUN_TAG" \
  run-binary-debug \
  BINARY="$binary_path"

base_name="${binary_name%-baremetal}"
sim_out_base="$OUTPUT_DIR/${base_name}.$RUN_TAG"
wave_ext="vcd"
if [ "$USE_FST" = "1" ]; then
  wave_ext="fst"
fi

for artifact in \
  "$sim_out_base.log" \
  "$sim_out_base.out" \
  "$sim_out_base.$wave_ext"
do
  if [ -f "$artifact" ]; then
    case "$artifact" in
      *.log|*.out)
        cp -f "$artifact" "$ROOT_DIR/sim/logs/$CONFIG/"
        ;;
      *."$wave_ext")
        cp -f "$artifact" "$ROOT_DIR/sim/waves/$CONFIG/"
        ;;
    esac
  fi
done

echo "Run complete"
echo "  binary : $binary_path"
echo "  logs   : $ROOT_DIR/sim/logs/$CONFIG"
echo "  waves  : $ROOT_DIR/sim/waves/$CONFIG"
