# Reduced Nangate45 technology library from third_party/edahub.
# This is not a complete PDK and is not signoff-ready.

TP_ROOT ?= $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
EDAHUB_HOME ?= $(TP_ROOT)/third_party/edahub
EDAHUB_TECH_ROOT ?= $(EDAHUB_HOME)/edahub/technology

TECHLIB_NAME := nangate45
TECHLIB_DISPLAY_NAME := Nangate45
TECHLIB_IS_COMPLETE_PDK := 0
TECHLIB_NOTE := Reduced edahub Nangate45 standard-cell library for early synthesis and initial P&R only.
TECHLIB_ROOT := $(EDAHUB_TECH_ROOT)/nangate45

TECHLIB_DB_FILES := $(TECHLIB_ROOT)/db/NangateOpenCellLibrary.db
TECHLIB_LIB_FILES := $(TECHLIB_ROOT)/lib/Nangate45_typ.lib
TECHLIB_SETUP_LIB_FILES := $(TECHLIB_ROOT)/lib/Nangate45_slow.lib
TECHLIB_HOLD_LIB_FILES := $(TECHLIB_ROOT)/lib/Nangate45_fast.lib

TECHLIB_TECH_LEF := $(TECHLIB_ROOT)/lef/Nangate45_tech.lef
TECHLIB_SC_LEF := $(TECHLIB_ROOT)/lef/Nangate45_stdcell.lef
TECHLIB_LEF_FILES := $(TECHLIB_TECH_LEF) $(TECHLIB_SC_LEF)

TECHLIB_QRC_TECH_FILES :=
TECHLIB_DONT_USE_CELLS := TAPCELL_X1 FILLCELL_X1 AOI211_X1 OAI211_X1
