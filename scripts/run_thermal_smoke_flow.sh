#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT_DIR/tools/env_gemmini_thermal.sh"

CONFIG="${CONFIG:-GemminiRocketConfig}"
SMOKE_TIMEOUT_SECS="${SMOKE_TIMEOUT_SECS:-60}"
SMOKE_MAX_CYCLES="${SMOKE_MAX_CYCLES:-1000}"
RUN_TAG="${RUN_TAG:-thermal_smoke}"

SIM_DIR="$CHIPYARD_HOME/sims/verilator"
SIM="$SIM_DIR/simulator-chipyard.harness-$CONFIG-debug"
BINARY="$ROOT_DIR/sim/binaries/$CONFIG/thermal_smoke-baremetal"
VCD="$ROOT_DIR/sim/waves/$CONFIG/$RUN_TAG.vcd"
LOG="$ROOT_DIR/sim/logs/$CONFIG/$RUN_TAG.log"
ERR="$ROOT_DIR/sim/logs/$CONFIG/$RUN_TAG.err"
SIGNAL_CSV="$ROOT_DIR/sim/activity/${RUN_TAG}_signal_activity.csv"
REGION_CSV="$ROOT_DIR/sim/activity/${RUN_TAG}_region_activity.csv"
FLP="$ROOT_DIR/thermal/floorplans/${RUN_TAG}.flp"
PTRACE="$ROOT_DIR/thermal/power/${RUN_TAG}.ptrace"
TTRACE="$ROOT_DIR/thermal/steady/${RUN_TAG}.ttrace"

mkdir -p \
  "$ROOT_DIR/sim/waves/$CONFIG" \
  "$ROOT_DIR/sim/logs/$CONFIG" \
  "$ROOT_DIR/sim/activity" \
  "$ROOT_DIR/thermal/floorplans" \
  "$ROOT_DIR/thermal/power" \
  "$ROOT_DIR/thermal/steady" \
  "$ROOT_DIR/reports/smoke"

echo "==> building smoke bare-metal binary"
"$ROOT_DIR/scripts/build_thermal_smoke_binary.sh" >/dev/null

if [ ! -x "$SIM" ]; then
  echo "==> building Verilator debug simulator with MAKE_JOBS=$MAKE_JOBS"
  make -C "$SIM_DIR" CONFIG="$CONFIG" -j "$MAKE_JOBS" debug
fi

echo "==> running bounded Verilator smoke: timeout=${SMOKE_TIMEOUT_SECS}s max_cycles=$SMOKE_MAX_CYCLES"
rm -f "$VCD" "$LOG" "$ERR"
set +e
timeout "${SMOKE_TIMEOUT_SECS}s" "$SIM" \
  +permissive \
  +dramsim \
  "+dramsim_ini_dir=$CHIPYARD_HOME/generators/testchipip/src/main/resources/dramsim2_ini" \
  "+max-cycles=$SMOKE_MAX_CYCLES" \
  "+vcdfile=$VCD" \
  +permissive-off \
  "$BINARY" \
  >"$LOG" 2>"$ERR"
sim_status=$?
set -e

if [ ! -s "$VCD" ]; then
  echo "smoke VCD was not generated: $VCD" >&2
  echo "simulator status: $sim_status" >&2
  echo "stdout log: $LOG" >&2
  echo "stderr log: $ERR" >&2
  exit 1
fi
echo "==> simulator status=$sim_status, VCD generated: $VCD"

echo "==> extracting VCD activity"
python "$ROOT_DIR/scripts/extract_vcd_activity.py" \
  --vcd "$VCD" \
  --hierarchy-map "$ROOT_DIR/configs/gemmini/hierarchy_map.yaml" \
  --workload "$RUN_TAG" \
  --signal-csv "$SIGNAL_CSV" \
  --region-csv "$REGION_CSV"

echo "==> exporting minimal HotSpot inputs"
python "$ROOT_DIR/scripts/export_smoke_hotspot_inputs.py" \
  --region-csv "$REGION_CSV" \
  --floorplan "$FLP" \
  --ptrace "$PTRACE"

echo "==> running HotSpot smoke"
(
  cd "$HOTSPOT_HOME/examples/example1"
  hotspot -c example.config -f "$FLP" -p "$PTRACE" -o "$TTRACE" >/dev/null
)

if [ ! -s "$TTRACE" ]; then
  echo "HotSpot output was not generated: $TTRACE" >&2
  exit 1
fi

cat > "$ROOT_DIR/reports/smoke/${RUN_TAG}_summary.txt" <<EOF
thermal smoke flow completed
config: $CONFIG
make_jobs: $MAKE_JOBS
sim_status: $sim_status
binary: $BINARY
vcd: $VCD
signal_activity: $SIGNAL_CSV
region_activity: $REGION_CSV
floorplan: $FLP
ptrace: $PTRACE
ttrace: $TTRACE
EOF

echo "Smoke flow complete"
echo "  summary: $ROOT_DIR/reports/smoke/${RUN_TAG}_summary.txt"
echo "  vcd    : $VCD"
echo "  csv    : $REGION_CSV"
echo "  ttrace : $TTRACE"
