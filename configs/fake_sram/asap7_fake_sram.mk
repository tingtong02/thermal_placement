# Fake SRAM ASAP7 collateral manifest for Make-based flows.
#
# Source this from a flow Makefile after TP_ROOT is defined, or let TP_ROOT
# default to the repository root relative to this file.

TP_ROOT ?= $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
FAKE_SRAM_HOME ?= /home/lisihang/fake_sram
FAKE_SRAM_ASAP7_ROOT ?= $(FAKE_SRAM_HOME)/results/asap7
FAKE_SRAM_CADENCE_CACHE ?= $(TP_ROOT)/.cache/fake_sram/asap7
FAKE_SRAM_DESIGN ?= Gemmini

FAKE_SRAM_ASAP7_DESIGNS := Gemmini

ifneq ($(wildcard $(FAKE_SRAM_CADENCE_CACHE)/$(FAKE_SRAM_DESIGN)),)
FAKE_SRAM_ASAP7_DESIGN_ROOT := $(FAKE_SRAM_CADENCE_CACHE)/$(FAKE_SRAM_DESIGN)
else
FAKE_SRAM_ASAP7_DESIGN_ROOT := $(FAKE_SRAM_ASAP7_ROOT)/$(FAKE_SRAM_DESIGN)
endif
FAKE_SRAM_ASAP7_LEF_DIR := $(FAKE_SRAM_ASAP7_DESIGN_ROOT)/lef
FAKE_SRAM_ASAP7_LIB_DIR := $(FAKE_SRAM_ASAP7_DESIGN_ROOT)/lib
FAKE_SRAM_ASAP7_DB_DIR := $(FAKE_SRAM_ASAP7_DESIGN_ROOT)/db
FAKE_SRAM_ASAP7_VERILOG_DIR := $(FAKE_SRAM_ASAP7_DESIGN_ROOT)/verilog

FAKE_SRAM_ASAP7_LEFS := $(sort $(wildcard $(FAKE_SRAM_ASAP7_LEF_DIR)/*.lef))
FAKE_SRAM_ASAP7_LIBS := $(sort $(wildcard $(FAKE_SRAM_ASAP7_LIB_DIR)/*.lib))
FAKE_SRAM_ASAP7_DBS := $(sort $(wildcard $(FAKE_SRAM_ASAP7_DB_DIR)/*.db))
FAKE_SRAM_ASAP7_VERILOG := $(sort $(wildcard $(FAKE_SRAM_ASAP7_VERILOG_DIR)/*.sv))

.PHONY: print-fake-sram-asap7
print-fake-sram-asap7:
	@echo "FAKE_SRAM_ASAP7_DESIGN_ROOT=$(FAKE_SRAM_ASAP7_DESIGN_ROOT)"
	@echo "FAKE_SRAM_ASAP7_LEFS=$(FAKE_SRAM_ASAP7_LEFS)"
	@echo "FAKE_SRAM_ASAP7_LIBS=$(FAKE_SRAM_ASAP7_LIBS)"
	@echo "FAKE_SRAM_ASAP7_VERILOG=$(FAKE_SRAM_ASAP7_VERILOG)"
