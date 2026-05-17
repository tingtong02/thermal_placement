# OpenROAD-flow-scripts overlay for edahub's reduced Nangate45 library.
# This is not a complete PDK and is intended for early synthesis/P&R only.

include $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../../reduced_techlibs/nangate45.mk)

export PLATFORM = nangate45
export PROCESS = 45
export EDAHUB_REDUCED_TECHLIB = 1
export ORFS_PLATFORM_DIR ?= $(TP_ROOT)/third_party/OpenROAD-flow-scripts/flow/platforms/nangate45

export TECH_LEF = $(TECHLIB_TECH_LEF)
export SC_LEF = $(TECHLIB_SC_LEF)
export LIB_FILES = $(TECHLIB_LIB_FILES) $(ADDITIONAL_LIBS)
export DB_FILES = $(TECHLIB_DB_FILES)
export GDS_FILES = $(ADDITIONAL_GDS)
export DONT_USE_CELLS = $(TECHLIB_DONT_USE_CELLS)

export SYNTH_MINIMUM_KEEP_SIZE ?= 10000
export TIEHI_CELL_AND_PORT = LOGIC1_X1 Z
export TIELO_CELL_AND_PORT = LOGIC0_X1 Z
export MIN_BUF_CELL_AND_PORTS = BUF_X1 A Z
export ABC_DRIVER_CELL = BUF_X1
export ABC_LOAD_IN_FF = 3.898

export LATCH_MAP_FILE = $(ORFS_PLATFORM_DIR)/cells_latch.v
export CLKGATE_MAP_FILE = $(ORFS_PLATFORM_DIR)/cells_clkgate.v
export ADDER_MAP_FILE ?= $(ORFS_PLATFORM_DIR)/cells_adders.v

export PLACE_SITE = FreePDK45_38x28_10R_NP_162NW_34O
export IO_PLACER_H ?= metal5
export IO_PLACER_V ?= metal6
export PDN_TCL ?= $(ORFS_PLATFORM_DIR)/grid_strategy-M1-M4-M7.tcl
export TAPCELL_TCL ?= $(ORFS_PLATFORM_DIR)/tapcell.tcl
export TAP_CELL_NAME = TAPCELL_X1
export FILL_CELLS ?= FILLCELL_X1 FILLCELL_X2 FILLCELL_X4 FILLCELL_X8 FILLCELL_X16 FILLCELL_X32
export MACRO_PLACE_HALO ?= 22.4 15.12
export PLACE_DENSITY ?= 0.30

export MIN_ROUTING_LAYER = metal2
export MIN_CLK_ROUTING_LAYER = metal4
export MAX_ROUTING_LAYER = metal10
export FASTROUTE_TCL ?= $(ORFS_PLATFORM_DIR)/fastroute.tcl
export SET_RC_TCL ?= $(ORFS_PLATFORM_DIR)/setRC.tcl
export RCX_RULES ?= $(ORFS_PLATFORM_DIR)/rcx_patterns.rules

export KLAYOUT_TECH_FILE ?= $(ORFS_PLATFORM_DIR)/FreePDK45.lyt
export KLAYOUT_DRC_FILE ?= $(ORFS_PLATFORM_DIR)/drc/FreePDK45.lydrc
export KLAYOUT_LVS_FILE ?= $(ORFS_PLATFORM_DIR)/lvs/FreePDK45.lylvs
export CDL_FILE ?= $(ORFS_PLATFORM_DIR)/cdl/NangateOpenCellLibrary.cdl
export TEMPLATE_PGA_CFG ?= $(ORFS_PLATFORM_DIR)/template_pga.cfg
export GDS_ALLOW_EMPTY ?= .*
export PWR_NETS_VOLTAGES ?= VDD 1.1
export GND_NETS_VOLTAGES ?= VSS 0.0
export IR_DROP_LAYER ?= metal1
