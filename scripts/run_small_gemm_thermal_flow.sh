#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT_DIR/tools/env_gemmini_thermal.sh"

CONFIG="${CONFIG:-GemminiRocketConfig}"
GEMM_TIMEOUT_SECS="${GEMM_TIMEOUT_SECS:-180}"
GEMM_MAX_CYCLES="${GEMM_MAX_CYCLES:-200000}"
RUN_TAG="${RUN_TAG:-small_gemm}"

SIM_DIR="$CHIPYARD_HOME/sims/verilator"
SIM="$SIM_DIR/simulator-chipyard.harness-$CONFIG-debug"
BINARY="$ROOT_DIR/sim/binaries/$CONFIG/small_gemm-baremetal"
VCD="$ROOT_DIR/sim/waves/$CONFIG/$RUN_TAG.vcd"
LOG="$ROOT_DIR/sim/logs/$CONFIG/$RUN_TAG.log"
ERR="$ROOT_DIR/sim/logs/$CONFIG/$RUN_TAG.err"
SIGNAL_CSV="$ROOT_DIR/sim/activity/${RUN_TAG}_signal_activity.csv"
REGION_CSV="$ROOT_DIR/sim/activity/${RUN_TAG}_region_activity.csv"
FLP="$ROOT_DIR/thermal/floorplans/${RUN_TAG}.flp"
PTRACE="$ROOT_DIR/thermal/power/${RUN_TAG}.ptrace"
TTRACE="$ROOT_DIR/thermal/steady/${RUN_TAG}.ttrace"
REPORT="$ROOT_DIR/reports/small_gemm/${RUN_TAG}_report.md"

mkdir -p \
  "$ROOT_DIR/sim/waves/$CONFIG" \
  "$ROOT_DIR/sim/logs/$CONFIG" \
  "$ROOT_DIR/sim/activity" \
  "$ROOT_DIR/thermal/floorplans" \
  "$ROOT_DIR/thermal/power" \
  "$ROOT_DIR/thermal/steady" \
  "$ROOT_DIR/reports/small_gemm"

echo "==> building small GEMM bare-metal binary"
"$ROOT_DIR/scripts/build_small_gemm_binary.sh" >/dev/null

if [ ! -x "$SIM" ]; then
  echo "==> building Verilator debug simulator with MAKE_JOBS=$MAKE_JOBS"
  make -C "$SIM_DIR" CONFIG="$CONFIG" -j "$MAKE_JOBS" debug
fi

echo "==> running small GEMM: timeout=${GEMM_TIMEOUT_SECS}s max_cycles=$GEMM_MAX_CYCLES"
rm -f "$VCD" "$LOG" "$ERR"
set +e
timeout "${GEMM_TIMEOUT_SECS}s" "$SIM" \
  +permissive \
  +dramsim \
  "+dramsim_ini_dir=$CHIPYARD_HOME/generators/testchipip/src/main/resources/dramsim2_ini" \
  "+max-cycles=$GEMM_MAX_CYCLES" \
  "+vcdfile=$VCD" \
  +permissive-off \
  "$BINARY" \
  >"$LOG" 2>"$ERR"
sim_status=$?
set -e

if [ ! -s "$VCD" ]; then
  echo "small GEMM VCD was not generated: $VCD" >&2
  echo "simulator status: $sim_status" >&2
  echo "stdout log: $LOG" >&2
  echo "stderr log: $ERR" >&2
  exit 1
fi

echo "==> extracting VCD activity"
python "$ROOT_DIR/scripts/extract_vcd_activity.py" \
  --vcd "$VCD" \
  --hierarchy-map "$ROOT_DIR/configs/gemmini/hierarchy_map.yaml" \
  --workload "$RUN_TAG" \
  --signal-csv "$SIGNAL_CSV" \
  --region-csv "$REGION_CSV"

echo "==> exporting HotSpot inputs"
python "$ROOT_DIR/scripts/export_smoke_hotspot_inputs.py" \
  --region-csv "$REGION_CSV" \
  --floorplan "$FLP" \
  --ptrace "$PTRACE"

echo "==> running HotSpot steady-state"
(
  cd "$HOTSPOT_HOME/examples/example1"
  hotspot -c example.config -f "$FLP" -p "$PTRACE" -o "$TTRACE" >/dev/null
)

if [ ! -s "$TTRACE" ]; then
  echo "HotSpot output was not generated: $TTRACE" >&2
  exit 1
fi

python "$ROOT_DIR/scripts/report_small_gemm_flow.py" \
  --run-tag "$RUN_TAG" \
  --config "$CONFIG" \
  --make-jobs "$MAKE_JOBS" \
  --max-cycles "$GEMM_MAX_CYCLES" \
  --sim-status "$sim_status" \
  --binary "$BINARY" \
  --log "$LOG" \
  --err "$ERR" \
  --vcd "$VCD" \
  --region-csv "$REGION_CSV" \
  --floorplan "$FLP" \
  --ptrace "$PTRACE" \
  --ttrace "$TTRACE" \
  --report "$REPORT"

echo "Small GEMM flow complete"
echo "  report : $REPORT"
echo "  vcd    : $VCD"
echo "  csv    : $REGION_CSV"
echo "  ttrace : $TTRACE"
