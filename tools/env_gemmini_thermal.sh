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
export PYTA_HOME="$TP_ROOT/third_party/pyta"
export FLOW_HOME="$TP_ROOT/third_party/OpenROAD-flow-scripts/flow"
export CIRCT_HOME="$TP_ROOT/tools/circt"
export PACT_HOME="$TP_ROOT/third_party/PACT"
export CADENCE_HOME="${CADENCE_HOME:-/opt/eda/Cadence_DDI_23.14}"
export CDS_LIC_FILE="${CDS_LIC_FILE:-$CADENCE_HOME/license/license.dat}"
export CDS_SKIP_OS_CHECK_ON_STARTUP="${CDS_SKIP_OS_CHECK_ON_STARTUP:-1}"
export ASAP7_HOME="${ASAP7_HOME:-/home/lisihang/asap7}"
export ASAP7_STDCELL_VERSION="${ASAP7_STDCELL_VERSION:-asap7sc7p5t_28}"
export ASAP7_LIB_CACHE="${ASAP7_LIB_CACHE:-$TP_ROOT/.cache/asap7/$ASAP7_STDCELL_VERSION/NLDM}"
export ASAP7_FULL_CONFIG="${ASAP7_FULL_CONFIG:-$TP_ROOT/configs/asap7_full/asap7_full.tcl}"
export FAKE_SRAM_HOME="${FAKE_SRAM_HOME:-/home/lisihang/fake_sram}"
export FAKE_SRAM_ASAP7_ROOT="${FAKE_SRAM_ASAP7_ROOT:-$FAKE_SRAM_HOME/results/asap7}"
export FAKE_SRAM_CADENCE_CACHE="${FAKE_SRAM_CADENCE_CACHE:-$TP_ROOT/.cache/fake_sram/asap7}"
export FAKE_SRAM_DESIGN="${FAKE_SRAM_DESIGN:-Gemmini}"
export FAKE_SRAM_ASAP7_CONFIG="${FAKE_SRAM_ASAP7_CONFIG:-$TP_ROOT/configs/fake_sram/asap7_fake_sram.tcl}"

export VERILATOR_PREFIX="$TP_ROOT/tools/verilator"
export VERILATOR_ROOT="$VERILATOR_PREFIX/share/verilator"
export OPENSTA_HOME="$TP_ROOT/tools/opensta"
export OSS_CAD_SUITE="$TP_ROOT/tools/oss-cad-suite/oss-cad-suite"
export OPENROAD_PREBUILT_ROOT="$TP_ROOT/tools/openroad-prebuilt/root"
export SBT_HOME="$TP_ROOT/tools/sbt/sbt"
export SLANG_HOME="$TP_ROOT/tools/slang"
export SV2V_HOME="$TP_ROOT/tools/sv2v"
export LIBTOOL_HOME="$TP_ROOT/tools/libtool"
export OPENMPI_HOME="$TP_ROOT/tools/openmpi-3.1.4"
export XYCE_HOME="$TP_ROOT/tools/xyce-7.4-build/install"
export TP_APT_SYSROOT="$TP_ROOT/tools/apt-sysroot"

export OPENROAD_EXE="$OPENROAD_PREBUILT_ROOT/usr/bin/openroad"
export OPENSTA_EXE="$OPENSTA_HOME/bin/sta"
export YOSYS_EXE="$OSS_CAD_SUITE/bin/yosys"
export YOSYS_SLANG_PLUGIN="$OSS_CAD_SUITE/share/yosys/plugins/slang.so"
export FIRTOOL_BIN="$CIRCT_HOME/bin/firtool"
export PACT_ENTRY="$PACT_HOME/src/PACT.py"
export XYCE_EXE="$XYCE_HOME/bin/Xyce"
export TCLLIBPATH="$OPENROAD_PREBUILT_ROOT/usr/lib/tcltk/x86_64-linux-gnu${TCLLIBPATH:+ $TCLLIBPATH}"

export MPLCONFIGDIR="$TP_CACHE_ROOT/matplotlib"
export SBT_GLOBAL_BASE="$TP_CACHE_ROOT/sbt/global"
export SBT_BOOT_DIR="$TP_CACHE_ROOT/sbt/boot"
export SBT_IVY_HOME="$TP_CACHE_ROOT/ivy2"
export COURSIER_CACHE="$TP_CACHE_ROOT/coursier"
export COURSIER_CONFIG_DIR="$TP_CACHE_ROOT/coursier"
export SBT_OPTS="${SBT_OPTS:-} -Dsbt.global.base=$SBT_GLOBAL_BASE -Dsbt.boot.directory=$SBT_BOOT_DIR -Dsbt.ivy.home=$SBT_IVY_HOME -Dsbt.coursier.home=$COURSIER_CACHE -Dsbt.supershell=false"

if [ -d "$PYTA_HOME/pyta" ]; then
  case ":${PYTHONPATH:-}:" in
    *":$PYTA_HOME:"*) ;;
    *) export PYTHONPATH="$PYTA_HOME${PYTHONPATH:+:$PYTHONPATH}" ;;
  esac
fi

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

if [ -z "${NUM_CORES:-}" ]; then
  export NUM_CORES="$MAKE_JOBS"
elif ! [[ "$NUM_CORES" =~ ^[0-9]+$ ]] || [ "$NUM_CORES" -lt 1 ]; then
  export NUM_CORES=1
fi
if [ "$NUM_CORES" -gt "$TP_MAX_JOBS" ]; then
  export NUM_CORES="$TP_MAX_JOBS"
fi

export GHCRTS="${GHCRTS:--N$MAKE_JOBS}"

export TP_CADENCE_GENUS_CPUS="${TP_CADENCE_GENUS_CPUS:-8}"
export TP_CADENCE_INNOVUS_CPUS="${TP_CADENCE_INNOVUS_CPUS:-8}"

for riscv_candidate in \
  "${RISCV:-}" \
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

export PATH="$TP_TOOLS_BIN:$LIBTOOL_HOME/bin:$OPENMPI_HOME/bin:$XYCE_HOME/bin:$SLANG_HOME/bin:$SV2V_HOME/bin:$CIRCT_HOME/bin:$SBT_HOME/bin:$VERILATOR_PREFIX/bin:$OPENSTA_HOME/bin:$HOTSPOT_HOME:$OSS_CAD_SUITE/bin:$OPENROAD_PREBUILT_ROOT/usr/bin:$CADENCE_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$XYCE_HOME/lib:$OPENMPI_HOME/lib:$LIBTOOL_HOME/lib:$TP_APT_SYSROOT/usr/lib/x86_64-linux-gnu:$TP_APT_SYSROOT/usr/lib/x86_64-linux-gnu/lapack:$OPENROAD_PREBUILT_ROOT/usr/lib/x86_64-linux-gnu:$OPENROAD_PREBUILT_ROOT/opt/or-tools/lib:$CADENCE_HOME/INNOVUS231/tools.lnx86/lib/64bit/RHEL/RHEL9:${LD_LIBRARY_PATH:-}"
