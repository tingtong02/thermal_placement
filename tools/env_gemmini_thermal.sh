#!/usr/bin/env bash

export TP_ROOT="${TP_ROOT:-/home/lisihang/thermal_placement}"

source /home/lisihang/miniconda3/etc/profile.d/conda.sh
conda activate thermal_placement

export CHIPYARD_HOME="$TP_ROOT/third_party/chipyard"
export GEMMINI_HOME="$CHIPYARD_HOME/generators/gemmini"
export HOTSPOT_HOME="$TP_ROOT/third_party/HotSpot"
export FLOW_HOME="$TP_ROOT/third_party/OpenROAD-flow-scripts/flow"

export VERILATOR_PREFIX="$TP_ROOT/tools/verilator"
export VERILATOR_ROOT="$VERILATOR_PREFIX/share/verilator"
export OPENSTA_HOME="$TP_ROOT/tools/opensta"
export OSS_CAD_SUITE="$TP_ROOT/tools/oss-cad-suite/oss-cad-suite"
export OPENROAD_PREBUILT_ROOT="$TP_ROOT/tools/openroad-prebuilt/root"
export SBT_HOME="$TP_ROOT/tools/sbt/sbt"

export OPENROAD_EXE="$OPENROAD_PREBUILT_ROOT/usr/bin/openroad"
export YOSYS_EXE="$OSS_CAD_SUITE/bin/yosys"
export TCLLIBPATH="$OPENROAD_PREBUILT_ROOT/usr/lib/tcltk/x86_64-linux-gnu${TCLLIBPATH:+ $TCLLIBPATH}"

export PATH="$SBT_HOME/bin:$VERILATOR_PREFIX/bin:$OPENSTA_HOME/bin:$HOTSPOT_HOME:$OSS_CAD_SUITE/bin:$OPENROAD_PREBUILT_ROOT/usr/bin:$PATH"
export LD_LIBRARY_PATH="$OPENROAD_PREBUILT_ROOT/usr/lib/x86_64-linux-gnu:$OPENROAD_PREBUILT_ROOT/opt/or-tools/lib:${LD_LIBRARY_PATH:-}"
