export DESIGN_HOME := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
export TP_ROOT ?= $(abspath $(DESIGN_HOME)/../..)
export WORK_HOME := $(DESIGN_HOME)

export PLATFORM = asap7
export DESIGN_NAME = Gemmini
export DESIGN_NICKNAME = stage2_tiled_matmul_os_baseline_asap7

export VERILOG_FILES = $(DESIGN_HOME)/src/gemmini_stage2_memory_blackboxes.sv
export SYNTH_SLANG_ARGS = -f $(DESIGN_HOME)/src/gemmini_stage2_sources_reduced.f
export LEC_AUX_VERILOG_FILES = $(DESIGN_HOME)/src/gemmini_stage2_memory_blackboxes.sv
export SYNTH_BLACKBOXES = mem_ext mem_0_ext mem_1_ext
export SYNTH_HDL_FRONTEND = slang
export SYNTH_HIERARCHICAL = 1
export SDC_FILE = $(DESIGN_HOME)/constraint.sdc
export ADDITIONAL_LEFS = $(DESIGN_HOME)/lef/gemmini_stage2_memory_macros.lef
export SYNTH_MINIMUM_KEEP_SIZE =

# Formal Stage 2 runs keep full synthesis/P&R quality settings.
# Debug-only speed knobs such as -noshare and SKIP_LAST_GASP must not be
# committed into the default implementation config.

export CORE_UTILIZATION = 25
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 10
export MACRO_PLACEMENT_TCL = $(DESIGN_HOME)/macro_placement.tcl
export PDN_TCL = $(DESIGN_HOME)/pdn_stage2.tcl
export PLACE_DENSITY = 0.35
export MAX_PLACE_STEP_COEF = 1.01
export TNS_END_PERCENT = 5
