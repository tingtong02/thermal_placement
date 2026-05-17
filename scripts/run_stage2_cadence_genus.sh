#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/run_stage2_cadence_genus.sh [--dry-run]

Runs or preflights the active Stage 2 Genus synthesis entry point.
Set RUN_ROOT to the active run directory. Default:
  runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff
EOF
}

DRY_RUN=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

TP_ROOT="${TP_ROOT:-/home/lisihang/thermal_placement}"
RUN_ROOT="${RUN_ROOT:-runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff}"
RUN_ROOT_ABS="$(cd "$TP_ROOT" && mkdir -p "$RUN_ROOT" && cd "$RUN_ROOT" && pwd)"
OUT_ROOT="$RUN_ROOT_ABS/physical/cadence/genus"
TOP_MODULE="${STAGE2_TOP_MODULE:-Gemmini}"
FILELIST="${STAGE2_RTL_FILELIST:-$RUN_ROOT_ABS/rtl/generated/chipyard.harness.TestHarness.GemminiRocketConfig.top.f}"
TCL="$TP_ROOT/flows/cadence/genus/stage2_genus.tcl"

mkdir -p "$OUT_ROOT"/{logs,reports,results,db}

if [ ! -f "$FILELIST" ]; then
  echo "missing RTL filelist: $FILELIST" >&2
  exit 1
fi
if [ ! -f "$TCL" ]; then
  echo "missing Genus Tcl: $TCL" >&2
  exit 1
fi

echo "RUN_ROOT=$RUN_ROOT_ABS"
echo "GENUS_OUT_ROOT=$OUT_ROOT"
echo "STAGE2_TOP_MODULE=$TOP_MODULE"
echo "STAGE2_RTL_FILELIST=$FILELIST"
echo "TP_CADENCE_GENUS_CPUS=${TP_CADENCE_GENUS_CPUS:-8}"

python "$TP_ROOT/scripts/prepare_asap7_liberty_cache.py" --check-only
python "$TP_ROOT/scripts/prepare_gemmini_fake_sram_collateral.py" \
  --filelist "$FILELIST" \
  --top "$TOP_MODULE" \
  --design "${FAKE_SRAM_DESIGN:-Gemmini}"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "dry-run complete; Genus was not launched"
  exit 0
fi

export RUN_ROOT="$RUN_ROOT_ABS"
export GENUS_OUT_ROOT="$OUT_ROOT"
export STAGE2_TOP_MODULE="$TOP_MODULE"
export STAGE2_RTL_FILELIST="$FILELIST"

exec genus -no_gui -abort_on_error -overwrite \
  -files "$TCL" \
  -log "$OUT_ROOT/logs/genus_stage2"
