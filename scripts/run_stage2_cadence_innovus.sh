#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/run_stage2_cadence_innovus.sh [--dry-run]

Runs or preflights the active Stage 2 Innovus implementation entry point.
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
GENUS_OUT_ROOT="${GENUS_OUT_ROOT:-$RUN_ROOT_ABS/physical/cadence/genus}"
INNOVUS_OUT_ROOT="$RUN_ROOT_ABS/physical/cadence/innovus"
NETLIST="${STAGE2_GENUS_NETLIST:-$GENUS_OUT_ROOT/results/${STAGE2_TOP_MODULE:-Gemmini}.mapped.v}"
SDC="${STAGE2_GENUS_SDC:-$GENUS_OUT_ROOT/results/${STAGE2_TOP_MODULE:-Gemmini}.mapped.sdc}"
TCL="$TP_ROOT/flows/cadence/innovus/stage2_innovus.tcl"

mkdir -p "$INNOVUS_OUT_ROOT"/{logs,reports,results,db}

if [ ! -f "$TCL" ]; then
  echo "missing Innovus Tcl: $TCL" >&2
  exit 1
fi

echo "RUN_ROOT=$RUN_ROOT_ABS"
echo "INNOVUS_OUT_ROOT=$INNOVUS_OUT_ROOT"
echo "STAGE2_GENUS_NETLIST=$NETLIST"
echo "STAGE2_GENUS_SDC=$SDC"
echo "TP_CADENCE_INNOVUS_CPUS=${TP_CADENCE_INNOVUS_CPUS:-8}"

python "$TP_ROOT/scripts/prepare_asap7_liberty_cache.py" --check-only
python "$TP_ROOT/scripts/prepare_gemmini_fake_sram_collateral.py" \
  --filelist "$RUN_ROOT_ABS/rtl/generated/chipyard.harness.TestHarness.GemminiRocketConfig.top.f" \
  --top "${STAGE2_TOP_MODULE:-Gemmini}" \
  --design "${FAKE_SRAM_DESIGN:-Gemmini}"

if [ ! -f "$NETLIST" ]; then
  echo "missing Genus netlist: $NETLIST" >&2
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "dry-run stops here because Genus output is not present yet"
    exit 0
  fi
  exit 1
fi
if [ ! -f "$SDC" ]; then
  echo "missing Genus SDC: $SDC" >&2
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "dry-run stops here because Genus SDC is not present yet"
    exit 0
  fi
  exit 1
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo "dry-run complete; Innovus was not launched"
  exit 0
fi

export RUN_ROOT="$RUN_ROOT_ABS"
export INNOVUS_OUT_ROOT="$INNOVUS_OUT_ROOT"
export STAGE2_GENUS_NETLIST="$NETLIST"
export STAGE2_GENUS_SDC="$SDC"

exec innovus -no_gui -batch -cpus "${TP_CADENCE_INNOVUS_CPUS:-8}" -abort_on_error -overwrite \
  -files "$TCL" \
  -log "$INNOVUS_OUT_ROOT/logs/innovus_stage2"
