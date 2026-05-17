# OpenROAD-flow-scripts overlay for edahub's reduced asap7 library.
# This is not a complete PDK and is intended for early synthesis/P&R only.

include $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../../reduced_techlibs/asap7.mk)

export PLATFORM = asap7
export PROCESS = 7
export EDAHUB_REDUCED_TECHLIB = 1
export ORFS_PLATFORM_DIR ?= $(TP_ROOT)/third_party/OpenROAD-flow-scripts/flow/platforms/asap7

export TECH_LEF = $(TECHLIB_TECH_LEF)
export SC_LEF = $(TECHLIB_SC_LEF)
export LIB_FILES = $(TECHLIB_LIB_FILES) $(ADDITIONAL_LIBS)
export DB_FILES = $(TECHLIB_DB_FILES)
export GDS_FILES = $(ADDITIONAL_GDS)
export DONT_USE_CELLS = $(TECHLIB_DONT_USE_CELLS)

export PLATFORM_TCL = $(ORFS_PLATFORM_DIR)/liberty_suppressions.tcl
export SYNTH_MINIMUM_KEEP_SIZE ?= 1000
export ABC_LOAD_IN_FF = 3.898

export TIEHI_CELL_AND_PORT ?= TIEHIx1_ASAP7_75t_R H
export TIELO_CELL_AND_PORT ?= TIELOx1_ASAP7_75t_R L
export MIN_BUF_CELL_AND_PORTS ?= BUFx2_ASAP7_75t_R A Y
export HOLD_BUF_CELL ?= BUFx2_ASAP7_75t_R
export ABC_DRIVER_CELL ?= BUFx2_ASAP7_75t_R

export LATCH_MAP_FILE ?= $(ORFS_PLATFORM_DIR)/yoSys/cells_latch_R.v
export CLKGATE_MAP_FILE ?= $(ORFS_PLATFORM_DIR)/yoSys/cells_clkgate_R.v
export ADDER_MAP_FILE ?= $(ORFS_PLATFORM_DIR)/yoSys/cells_adders_R.v

export PLACE_SITE ?= asap7sc7p5t
export MAKE_TRACKS ?= $(ORFS_PLATFORM_DIR)/openRoad/make_tracks.tcl
export PDN_TCL ?= $(ORFS_PLATFORM_DIR)/openRoad/pdn/grid_strategy-M1-M2-M5-M6.tcl
export TAPCELL_TCL ?= $(ORFS_PLATFORM_DIR)/openRoad/tapcell.tcl
export TAP_CELL_NAME ?= TAPCELL_ASAP7_75t_R
export FILL_CELLS ?= FILLERxp5_ASAP7_75t_R FILLER_ASAP7_75t_R DECAPx1_ASAP7_75t_R DECAPx2_ASAP7_75t_R DECAPx4_ASAP7_75t_R DECAPx6_ASAP7_75t_R DECAPx10_ASAP7_75t_R

export IO_PLACER_H ?= M4
export IO_PLACER_V ?= M5
export MACRO_PLACE_HALO ?= 10 10
export MACRO_ROWS_HALO_X ?= 2
export MACRO_ROWS_HALO_Y ?= 2
export PLACE_DENSITY ?= 0.60

export MIN_ROUTING_LAYER ?= M2
export MIN_CLK_ROUTING_LAYER ?= M4
export MAX_ROUTING_LAYER ?= M7
export FASTROUTE_TCL ?= $(ORFS_PLATFORM_DIR)/fastroute.tcl
export SET_RC_TCL ?= $(ORFS_PLATFORM_DIR)/setRC.tcl
export RCX_RULES ?= $(ORFS_PLATFORM_DIR)/rcx_patterns.rules

export KLAYOUT_TECH_FILE ?= $(ORFS_PLATFORM_DIR)/KLayout/asap7.lyt
export KLAYOUT_DRC_FILE ?= $(ORFS_PLATFORM_DIR)/drc/asap7.lydrc
export GDS_ALLOW_EMPTY ?= .*
export PWR_NETS_VOLTAGES ?= VDD 0.70
export GND_NETS_VOLTAGES ?= VSS 0.0
export IR_DROP_LAYER ?= M1
export REMOVE_CELLS_FOR_LEC ?= TAPCELL*
