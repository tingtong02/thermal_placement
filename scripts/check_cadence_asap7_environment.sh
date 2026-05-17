#!/usr/bin/env bash
set -euo pipefail

TP_ROOT="${TP_ROOT:-/home/lisihang/thermal_placement}"
ASAP7_HOME="${ASAP7_HOME:-/home/lisihang/asap7}"
ASAP7_STDCELL_VERSION="${ASAP7_STDCELL_VERSION:-asap7sc7p5t_28}"
ASAP7_ROOT="$ASAP7_HOME/$ASAP7_STDCELL_VERSION"

require_path() {
  local path="$1"
  if [ ! -e "$path" ]; then
    echo "missing path: $path" >&2
    return 1
  fi
}

echo "TP_ROOT=$TP_ROOT"
echo "ASAP7_HOME=$ASAP7_HOME"
echo "ASAP7_STDCELL_VERSION=$ASAP7_STDCELL_VERSION"

command -v python
python --version

command -v genus
timeout 60 genus -version | sed -n '1,8p'

command -v innovus
timeout 60 innovus -version | sed -n '1,8p'

require_path "$ASAP7_ROOT/techlef_misc/asap7_tech_1x_201209.lef"
require_path "$ASAP7_ROOT/LEF/asap7sc7p5t_28_R_1x_220121a.lef"
require_path "$ASAP7_ROOT/LEF/asap7sc7p5t_28_L_1x_220121a.lef"
require_path "$ASAP7_ROOT/LEF/asap7sc7p5t_28_SL_1x_220121a.lef"
require_path "$ASAP7_ROOT/qrc/qrcTechFile_typ03_unscaledV02"
require_path "$ASAP7_ROOT/LIB/NLDM"

python "$TP_ROOT/scripts/prepare_asap7_liberty_cache.py" --check-only || true
python "$TP_ROOT/scripts/prepare_gemmini_fake_sram_collateral.py" --design "${FAKE_SRAM_DESIGN:-Gemmini}"

echo "cadence/asap7 environment preflight completed"
