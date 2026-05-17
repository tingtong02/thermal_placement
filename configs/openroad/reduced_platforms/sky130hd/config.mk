# OpenROAD-flow-scripts overlay for edahub's reduced sky130hd library.
# This is not a complete PDK and is intended for early synthesis/P&R only.

include $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../../reduced_techlibs/sky130hd.mk)

export PLATFORM = sky130hd
export PROCESS = 130
export EDAHUB_REDUCED_TECHLIB = 1
export ORFS_PLATFORM_DIR ?= $(TP_ROOT)/third_party/OpenROAD-flow-scripts/flow/platforms/sky130hd

export TECH_LEF = $(TECHLIB_TECH_LEF)
export SC_LEF = $(TECHLIB_SC_LEF)
export LIB_FILES = $(TECHLIB_LIB_FILES) $(ADDITIONAL_LIBS)
export DB_FILES = $(TECHLIB_DB_FILES)
export GDS_FILES = $(ADDITIONAL_GDS)
export DONT_USE_CELLS = $(TECHLIB_DONT_USE_CELLS)

export TIEHI_CELL_AND_PORT = sky130_fd_sc_hd__conb_1 HI
export TIELO_CELL_AND_PORT = sky130_fd_sc_hd__conb_1 LO
export MIN_BUF_CELL_AND_PORTS = sky130_fd_sc_hd__buf_4 A X
export ABC_DRIVER_CELL = sky130_fd_sc_hd__buf_1
export ABC_LOAD_IN_FF = 5

export LATCH_MAP_FILE = $(ORFS_PLATFORM_DIR)/cells_latch_hd.v
export CLKGATE_MAP_FILE = $(ORFS_PLATFORM_DIR)/cells_clkgate_hd.v
export ADDER_MAP_FILE ?= $(ORFS_PLATFORM_DIR)/cells_adders_hd.v
export MATCH_CELL_FOOTPRINT = 1

export PLACE_SITE = unithd
export IO_PLACER_H ?= met3
export IO_PLACER_V ?= met2
export PDN_TCL ?= $(ORFS_PLATFORM_DIR)/pdn.tcl
export TAPCELL_TCL ?= $(ORFS_PLATFORM_DIR)/tapcell.tcl
export TAP_CELL_NAME = sky130_fd_sc_hd__tapvpwrvgnd_1
export FILL_CELLS ?= sky130_fd_sc_hd__fill_1 sky130_fd_sc_hd__fill_2 sky130_fd_sc_hd__fill_4 sky130_fd_sc_hd__fill_8
export MACRO_PLACE_HALO ?= 40 40
export PLACE_DENSITY ?= 0.60

export MIN_ROUTING_LAYER ?= met1
export MIN_CLK_ROUTING_LAYER ?= met3
export MAX_ROUTING_LAYER ?= met5
export FASTROUTE_TCL ?= $(ORFS_PLATFORM_DIR)/fastroute.tcl
export SET_RC_TCL ?= $(ORFS_PLATFORM_DIR)/setRC.tcl
export RCX_RULES ?= $(ORFS_PLATFORM_DIR)/rcx_patterns.rules

export KLAYOUT_TECH_FILE ?= $(ORFS_PLATFORM_DIR)/sky130hd.lyt
export KLAYOUT_DRC_FILE ?= $(ORFS_PLATFORM_DIR)/drc/sky130hd.lydrc
export KLAYOUT_LVS_FILE ?= $(ORFS_PLATFORM_DIR)/lvs/sky130hd.lylvs
export FILL_CONFIG ?= $(ORFS_PLATFORM_DIR)/fill.json
export TEMPLATE_PGA_CFG ?= $(ORFS_PLATFORM_DIR)/template_pga.cfg
export CDL_FILE ?= $(ORFS_PLATFORM_DIR)/cdl/sky130hd.cdl
export GDS_ALLOW_EMPTY ?= .*
export PWR_NETS_VOLTAGES ?= VDD 1.8
export GND_NETS_VOLTAGES ?= VSS 0.0
export IR_DROP_LAYER ?= met1
export REMOVE_CELLS_FOR_LEC ?= sky130_fd_sc_hd__tapvpwrvgnd*
