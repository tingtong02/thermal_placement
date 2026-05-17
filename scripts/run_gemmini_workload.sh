#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT_DIR/tools/env_gemmini_thermal.sh"

CONFIG="${CONFIG:-GemminiRocketConfig}"
RUN_ROOT="${RUN_ROOT:-}"
MAKE_JOBS="${MAKE_JOBS:-$(nproc)}"
TEST_NAME="${1:-mvin_mvout}"
RUN_TAG="${RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
BUILD_DEBUG_SIM="${BUILD_DEBUG_SIM:-1}"
CLEAN_DEBUG_SIM="${CLEAN_DEBUG_SIM:-0}"
USE_FST="${USE_FST:-0}"
EXTRACT_ACTIVITY="${EXTRACT_ACTIVITY:-1}"
VCD_PARSER_WORKERS="${VCD_PARSER_WORKERS:-1}"
WINDOW_BINS="${WINDOW_BINS:-200}"
TIMEOUT_CYCLES="${TIMEOUT_CYCLES:-10000000}"
VERILATOR_THREADS="${VERILATOR_THREADS:-1}"
NUMACTL="${NUMACTL:-0}"

if [ -n "$RUN_ROOT" ]; then
  mkdir -p "$RUN_ROOT"
  RUN_ROOT=$(cd "$RUN_ROOT" && pwd)
  BINARY_ROOT="$RUN_ROOT/workloads/$TEST_NAME"
  LOG_DIR="$RUN_ROOT/sim/$TEST_NAME/logs"
  WAVE_DIR="$RUN_ROOT/sim/$TEST_NAME/waves"
  ACTIVITY_DIR="$RUN_ROOT/activity/$TEST_NAME"
  REPORT_DIR="$RUN_ROOT/reports/$TEST_NAME"
  ARTIFACT_DIR="$RUN_ROOT/artifacts/$TEST_NAME"
  DEFAULT_REPORT_PREFIX="stage1_${TEST_NAME}_signoff"
  DEFAULT_HIERARCHY_MAP="$RUN_ROOT/rtl/hierarchy/hierarchy_map.yaml"
else
  BINARY_ROOT="$ROOT_DIR/sim/binaries/$CONFIG"
  LOG_DIR="$ROOT_DIR/sim/logs/$CONFIG"
  WAVE_DIR="$ROOT_DIR/sim/waves/$CONFIG"
  ACTIVITY_DIR="$ROOT_DIR/sim/activity"
  REPORT_DIR="$ROOT_DIR/reports"
  ARTIFACT_DIR="$ROOT_DIR/artifacts/stage1"
  DEFAULT_REPORT_PREFIX="stage1_${TEST_NAME}_baseline"
  DEFAULT_HIERARCHY_MAP="$ROOT_DIR/configs/gemmini/hierarchy_map.yaml"
fi

STAGE1_REPORT_PREFIX="${STAGE1_REPORT_PREFIX:-$DEFAULT_REPORT_PREFIX}"
HIERARCHY_MAP="${HIERARCHY_MAP:-$DEFAULT_HIERARCHY_MAP}"

SIM_DIR="$CHIPYARD_HOME/sims/verilator"
LONG_NAME="chipyard.harness.TestHarness.${CONFIG}"
OUTPUT_DIR="$SIM_DIR/output/$LONG_NAME"

mkdir -p \
  "$BINARY_ROOT" \
  "$LOG_DIR" \
  "$WAVE_DIR" \
  "$ACTIVITY_DIR" \
  "$REPORT_DIR" \
  "$ARTIFACT_DIR"

binary_name="$TEST_NAME"
if [[ "$binary_name" != *-baremetal ]]; then
  binary_name="${binary_name}-baremetal"
fi

binary_path="$BINARY_ROOT/$binary_name"
if [ ! -f "$binary_path" ]; then
  binary_path="$GEMMINI_HOME/software/gemmini-rocc-tests/build/bareMetalC/$binary_name"
fi
if [ ! -f "$binary_path" ] && [ -z "$RUN_ROOT" ]; then
  binary_path="$ROOT_DIR/sim/binaries/$CONFIG/$binary_name"
fi

if [ ! -f "$binary_path" ]; then
  echo "Binary not found: $binary_name" >&2
  echo "Build it first with RUN_ROOT=$RUN_ROOT scripts/build_gemmini_workloads.sh $TEST_NAME" >&2
  exit 1
fi

if [ "$(readlink -f "$binary_path")" != "$(readlink -f "$BINARY_ROOT/$binary_name" 2>/dev/null || true)" ]; then
  cp -f "$binary_path" "$BINARY_ROOT/"
fi
binary_path="$BINARY_ROOT/$binary_name"

if [ "$EXTRACT_ACTIVITY" = "1" ] && [ ! -s "$HIERARCHY_MAP" ]; then
  echo "Hierarchy map not found or empty: $HIERARCHY_MAP" >&2
  echo "Run RUN_ROOT=$RUN_ROOT scripts/run_gemmini_rtl_generation.sh first, or set HIERARCHY_MAP explicitly." >&2
  exit 1
fi

if [ "$CLEAN_DEBUG_SIM" = "1" ]; then
  echo "==> cleaning Verilator debug simulator for $CONFIG"
  make -C "$SIM_DIR" CONFIG="$CONFIG" clean-sim-debug
fi

if [ "$BUILD_DEBUG_SIM" = "1" ] || [ ! -x "$SIM_DIR/simulator-chipyard.harness-$CONFIG-debug" ]; then
  echo "==> building Verilator debug simulator for $CONFIG with MAKE_JOBS=$MAKE_JOBS VERILATOR_THREADS=$VERILATOR_THREADS USE_FST=$USE_FST"
  make -C "$SIM_DIR" -j "$MAKE_JOBS" CONFIG="$CONFIG" VERILATOR_THREADS="$VERILATOR_THREADS" USE_FST="$USE_FST" debug
fi

wave_ext="vcd"
if [ "$USE_FST" = "1" ]; then
  wave_ext="fst"
fi

sim_out_base="$OUTPUT_DIR/${binary_name}.${RUN_TAG}"
rm -f "$sim_out_base.log" "$sim_out_base.out" "$sim_out_base.$wave_ext"

echo "==> running $binary_name with waveform dump"
set +e
make -C "$SIM_DIR" \
  CONFIG="$CONFIG" \
  VERILATOR_THREADS="$VERILATOR_THREADS" \
  NUMACTL="$NUMACTL" \
  USE_FST="$USE_FST" \
  DUMP_BINARY=0 \
  EXTRA_SIM_OUT_NAME="$RUN_TAG" \
  TIMEOUT_CYCLES="$TIMEOUT_CYCLES" \
  run-binary-debug \
  BINARY="$binary_path"
sim_status=$?
set -e

copied_log="$LOG_DIR/${binary_name}.${RUN_TAG}.log"
copied_out="$LOG_DIR/${binary_name}.${RUN_TAG}.out"
copied_wave="$WAVE_DIR/${binary_name}.${RUN_TAG}.${wave_ext}"
manifest_path="$REPORT_DIR/${STAGE1_REPORT_PREFIX}_manifest.txt"

for artifact in \
  "$sim_out_base.log" \
  "$sim_out_base.out" \
  "$sim_out_base.$wave_ext"
do
  if [ -f "$artifact" ]; then
    case "$artifact" in
      *.log)
        cp -f "$artifact" "$copied_log"
        ;;
      *.out)
        cp -f "$artifact" "$copied_out"
        ;;
      *."$wave_ext")
        cp -f "$artifact" "$copied_wave"
        ;;
    esac
  fi
done

if [ "$sim_status" -ne 0 ]; then
  cat > "$manifest_path" <<EOF
stage=1
config=$CONFIG
workload=$TEST_NAME
binary=$binary_path
run_tag=$RUN_TAG
run_root=$RUN_ROOT
use_fst=$USE_FST
timeout_cycles=$TIMEOUT_CYCLES
verilator_threads=$VERILATOR_THREADS
numactl=$NUMACTL
clean_debug_sim=$CLEAN_DEBUG_SIM
vcd_parser_workers=$VCD_PARSER_WORKERS
sim_status=$sim_status
stdout_log=$copied_log
out_log=$copied_out
source_waveform=$sim_out_base.$wave_ext
failure=simulation did not complete; waveform copy and activity extraction skipped
failed_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
  echo "Simulation failed with status $sim_status" >&2
  echo "  log  : $copied_log" >&2
  echo "  out  : $copied_out" >&2
  echo "  wave : $sim_out_base.$wave_ext" >&2
  exit "$sim_status"
fi

if [ ! -s "$copied_wave" ]; then
  echo "Waveform was not copied or is empty: $copied_wave" >&2
  echo "Expected simulator output: $sim_out_base.$wave_ext" >&2
  exit 1
fi

artifact_wave="$ARTIFACT_DIR/${binary_name}.${RUN_TAG}.${wave_ext}"
ln -sfn "$copied_wave" "$artifact_wave"

signal_csv="$ACTIVITY_DIR/${RUN_TAG}_signal_activity.csv"
region_csv="$ACTIVITY_DIR/${RUN_TAG}_region_activity.csv"
window_csv="$ACTIVITY_DIR/${RUN_TAG}_window_activity.csv"
window_report="$REPORT_DIR/${STAGE1_REPORT_PREFIX}_windows.md"
activity_report="$REPORT_DIR/${STAGE1_REPORT_PREFIX}_activity_summary.md"

signal_activity_manifest=""
region_activity_manifest=""
window_activity_manifest=""
window_report_manifest=""
activity_report_manifest=""

if [ "$EXTRACT_ACTIVITY" = "1" ]; then
  if [ "$wave_ext" != "vcd" ]; then
    echo "Skipping activity extraction because wave_ext=$wave_ext; rerun with USE_FST=0 or convert to VCD."
  else
    echo "==> extracting VCD activity"
    python "$ROOT_DIR/scripts/extract_vcd_activity.py" \
      --vcd "$copied_wave" \
      --hierarchy-map "$HIERARCHY_MAP" \
      --workload "$RUN_TAG" \
      --signal-csv "$signal_csv" \
      --region-csv "$region_csv" \
      --top-signals 0 \
      --workers "$VCD_PARSER_WORKERS"

    echo "==> selecting Stage 1 activity windows"
    python "$ROOT_DIR/scripts/analyze_vcd_windows.py" \
      --vcd "$copied_wave" \
      --hierarchy-map "$HIERARCHY_MAP" \
      --workload "$RUN_TAG" \
      --window-csv "$window_csv" \
      --window-report "$window_report" \
      --bins "$WINDOW_BINS"

    echo "==> writing Stage 1 activity summary"
    python "$ROOT_DIR/scripts/report_stage1_activity.py" \
      --run-tag "$RUN_TAG" \
      --config "$CONFIG" \
      --workload "$TEST_NAME" \
      --binary "$binary_path" \
      --log "$copied_log" \
      --out "$copied_out" \
      --wave "$copied_wave" \
      --signal-csv "$signal_csv" \
      --region-csv "$region_csv" \
      --window-csv "$window_csv" \
      --window-report "$window_report" \
      --report "$activity_report" \
      --sim-status 0
  fi
fi

if [ -f "$signal_csv" ]; then
  signal_activity_manifest="$signal_csv"
  region_activity_manifest="$region_csv"
  window_activity_manifest="$window_csv"
  window_report_manifest="$window_report"
  activity_report_manifest="$activity_report"
fi

cat > "$manifest_path" <<EOF
stage=1
config=$CONFIG
workload=$TEST_NAME
binary=$binary_path
run_tag=$RUN_TAG
run_root=$RUN_ROOT
use_fst=$USE_FST
timeout_cycles=$TIMEOUT_CYCLES
verilator_threads=$VERILATOR_THREADS
numactl=$NUMACTL
clean_debug_sim=$CLEAN_DEBUG_SIM
vcd_parser_workers=$VCD_PARSER_WORKERS
hierarchy_map=$HIERARCHY_MAP
sim_status=0
waveform=$copied_wave
artifact_wave_symlink=$artifact_wave
stdout_log=$copied_log
out_log=$copied_out
signal_activity=$signal_activity_manifest
region_activity=$region_activity_manifest
window_activity=$window_activity_manifest
window_report=$window_report_manifest
activity_report=$activity_report_manifest
generated_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

echo "Run complete"
echo "  binary          : $binary_path"
echo "  log             : $copied_log"
echo "  out             : $copied_out"
echo "  wave            : $copied_wave"
echo "  artifact link   : $artifact_wave"
if [ -n "$region_activity_manifest" ]; then
  echo "  activity csv    : $region_activity_manifest"
  echo "  parser workers  : $VCD_PARSER_WORKERS"
  echo "  window report   : $window_report_manifest"
  echo "  activity report : $activity_report_manifest"
else
  echo "  activity        : skipped"
fi
