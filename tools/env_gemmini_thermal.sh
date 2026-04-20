#!/usr/bin/env bash

export TP_ROOT="${TP_ROOT:-/home/lisihang/thermal_placement}"
export TP_TOOLS_BIN="$TP_ROOT/tools/bin"

export TP_CACHE_ROOT="${TP_CACHE_ROOT:-$TP_ROOT/.cache}"
mkdir -p \
  "$TP_CACHE_ROOT" \
  "$TP_TOOLS_BIN" \
  "$TP_CACHE_ROOT/matplotlib" \
  "$TP_CACHE_ROOT/sbt/boot" \
  "$TP_CACHE_ROOT/sbt/global" \
  "$TP_CACHE_ROOT/ivy2" \
  "$TP_CACHE_ROOT/coursier"

source /home/lisihang/miniconda3/etc/profile.d/conda.sh
conda activate thermal_placement

export CHIPYARD_HOME="$TP_ROOT/third_party/chipyard"
export GEMMINI_HOME="$CHIPYARD_HOME/generators/gemmini"
export HOTSPOT_HOME="$TP_ROOT/third_party/HotSpot"
export FLOW_HOME="$TP_ROOT/third_party/OpenROAD-flow-scripts/flow"
export CIRCT_HOME="$TP_ROOT/tools/circt"

export VERILATOR_PREFIX="$TP_ROOT/tools/verilator"
export VERILATOR_ROOT="$VERILATOR_PREFIX/share/verilator"
export OPENSTA_HOME="$TP_ROOT/tools/opensta"
export OSS_CAD_SUITE="$TP_ROOT/tools/oss-cad-suite/oss-cad-suite"
export OPENROAD_PREBUILT_ROOT="$TP_ROOT/tools/openroad-prebuilt/root"
export SBT_HOME="$TP_ROOT/tools/sbt/sbt"

export OPENROAD_EXE="$OPENROAD_PREBUILT_ROOT/usr/bin/openroad"
export YOSYS_EXE="$OSS_CAD_SUITE/bin/yosys"
export FIRTOOL_BIN="$CIRCT_HOME/bin/firtool"
export TCLLIBPATH="$OPENROAD_PREBUILT_ROOT/usr/lib/tcltk/x86_64-linux-gnu${TCLLIBPATH:+ $TCLLIBPATH}"

export MPLCONFIGDIR="$TP_CACHE_ROOT/matplotlib"
export SBT_GLOBAL_BASE="$TP_CACHE_ROOT/sbt/global"
export SBT_BOOT_DIR="$TP_CACHE_ROOT/sbt/boot"
export SBT_IVY_HOME="$TP_CACHE_ROOT/ivy2"
export COURSIER_CACHE="$TP_CACHE_ROOT/coursier"
export COURSIER_CONFIG_DIR="$TP_CACHE_ROOT/coursier"
export SBT_OPTS="${SBT_OPTS:-} -Dsbt.global.base=$SBT_GLOBAL_BASE -Dsbt.boot.directory=$SBT_BOOT_DIR -Dsbt.ivy.home=$SBT_IVY_HOME -Dsbt.coursier.home=$COURSIER_CACHE -Dsbt.supershell=false"

export TP_MAX_JOBS="${TP_MAX_JOBS:-128}"
if ! [[ "$TP_MAX_JOBS" =~ ^[0-9]+$ ]] || [ "$TP_MAX_JOBS" -lt 1 ]; then
  export TP_MAX_JOBS=128
fi
if [ "$TP_MAX_JOBS" -gt 128 ]; then
  export TP_MAX_JOBS=128
fi

detected_jobs="$(nproc 2>/dev/null || echo 1)"
if ! [[ "$detected_jobs" =~ ^[0-9]+$ ]] || [ "$detected_jobs" -lt 1 ]; then
  detected_jobs=1
fi
if [ -z "${MAKE_JOBS:-}" ]; then
  export MAKE_JOBS="$detected_jobs"
elif ! [[ "$MAKE_JOBS" =~ ^[0-9]+$ ]] || [ "$MAKE_JOBS" -lt 1 ]; then
  export MAKE_JOBS=1
fi
if [ "$MAKE_JOBS" -gt "$TP_MAX_JOBS" ]; then
  export MAKE_JOBS="$TP_MAX_JOBS"
fi

for riscv_candidate in \
  "$RISCV" \
  "$TP_ROOT/tools/riscv" \
  "$CHIPYARD_HOME/toolchains/riscv-tools/install" \
  "$CHIPYARD_HOME/toolchains/riscv-tools/riscv"
do
  if [ -n "$riscv_candidate" ] && [ -x "$riscv_candidate/bin/riscv64-unknown-elf-gcc" ]; then
    export RISCV="$riscv_candidate"
    export PATH="$RISCV/bin:$PATH"
    break
  fi
done

export PATH="$TP_TOOLS_BIN:$CIRCT_HOME/bin:$SBT_HOME/bin:$VERILATOR_PREFIX/bin:$OPENSTA_HOME/bin:$HOTSPOT_HOME:$OSS_CAD_SUITE/bin:$OPENROAD_PREBUILT_ROOT/usr/bin:$PATH"
export LD_LIBRARY_PATH="$OPENROAD_PREBUILT_ROOT/usr/lib/x86_64-linux-gnu:$OPENROAD_PREBUILT_ROOT/opt/or-tools/lib:${LD_LIBRARY_PATH:-}"
