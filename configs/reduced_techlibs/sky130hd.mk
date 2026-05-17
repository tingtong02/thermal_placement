# Reduced sky130hd technology library from third_party/edahub.
# This is not a complete PDK and is not signoff-ready.

TP_ROOT ?= $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
EDAHUB_HOME ?= $(TP_ROOT)/third_party/edahub
EDAHUB_TECH_ROOT ?= $(EDAHUB_HOME)/edahub/technology

TECHLIB_NAME := sky130hd
TECHLIB_DISPLAY_NAME := sky130hd
TECHLIB_IS_COMPLETE_PDK := 0
TECHLIB_NOTE := Reduced edahub sky130hd standard-cell library for early synthesis and initial P&R only.
TECHLIB_ROOT := $(EDAHUB_TECH_ROOT)/sky130hd

TECHLIB_DB_FILES := $(TECHLIB_ROOT)/db/sky130_fd_sc_hd__tt_025C_1v80.db
TECHLIB_LIB_FILES := $(TECHLIB_ROOT)/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
TECHLIB_SETUP_LIB_FILES := $(TECHLIB_ROOT)/lib/sky130_fd_sc_hd__ff_n40C_1v95.lib
TECHLIB_HOLD_LIB_FILES := $(TECHLIB_ROOT)/lib/sky130_fd_sc_hd__ss_n40C_1v40.lib

TECHLIB_TECH_LEF := $(TECHLIB_ROOT)/lef/sky130hd.tlef
TECHLIB_SC_LEF := $(TECHLIB_ROOT)/lef/sky130_fd_sc_hd_merged.lef
TECHLIB_LEF_FILES := $(TECHLIB_TECH_LEF) $(TECHLIB_SC_LEF)

TECHLIB_QRC_TECH_FILES :=
TECHLIB_DONT_USE_CELLS := \
  */sky130_fd_sc_hd__probec_p_8 \
  */sky130_fd_sc_hd__lpflow_bleeder_1 \
  */sky130_fd_sc_hd__lpflow_clkbufkapwr_1 \
  */sky130_fd_sc_hd__lpflow_clkbufkapwr_16 \
  */sky130_fd_sc_hd__lpflow_clkbufkapwr_2 \
  */sky130_fd_sc_hd__lpflow_clkbufkapwr_4 \
  */sky130_fd_sc_hd__lpflow_clkbufkapwr_8 \
  */sky130_fd_sc_hd__lpflow_clkinvkapwr_1 \
  */sky130_fd_sc_hd__lpflow_clkinvkapwr_16 \
  */sky130_fd_sc_hd__lpflow_clkinvkapwr_2 \
  */sky130_fd_sc_hd__lpflow_clkinvkapwr_4 \
  */sky130_fd_sc_hd__lpflow_clkinvkapwr_8 \
  */sky130_fd_sc_hd__lpflow_decapkapwr_12 \
  */sky130_fd_sc_hd__lpflow_decapkapwr_3 \
  */sky130_fd_sc_hd__lpflow_decapkapwr_4 \
  */sky130_fd_sc_hd__lpflow_decapkapwr_6 \
  */sky130_fd_sc_hd__lpflow_decapkapwr_8 \
  */sky130_fd_sc_hd__lpflow_inputiso0n_1 \
  */sky130_fd_sc_hd__lpflow_inputiso0p_1 \
  */sky130_fd_sc_hd__lpflow_inputiso1n_1 \
  */sky130_fd_sc_hd__lpflow_inputiso1p_1 \
  */sky130_fd_sc_hd__lpflow_inputisolatch_1 \
  */sky130_fd_sc_hd__lpflow_isobufsrc_1 \
  */sky130_fd_sc_hd__lpflow_isobufsrc_16 \
  */sky130_fd_sc_hd__lpflow_isobufsrc_2 \
  */sky130_fd_sc_hd__lpflow_isobufsrc_4 \
  */sky130_fd_sc_hd__lpflow_isobufsrc_8 \
  */sky130_fd_sc_hd__lpflow_isobufsrckapwr_16 \
  */sky130_fd_sc_hd__lpflow_lsbuf_lh_hl_isowell_tap_1 \
  */sky130_fd_sc_hd__lpflow_lsbuf_lh_hl_isowell_tap_2 \
  */sky130_fd_sc_hd__lpflow_lsbuf_lh_hl_isowell_tap_4 \
  */sky130_fd_sc_hd__lpflow_lsbuf_lh_isowell_4 \
  */sky130_fd_sc_hd__lpflow_lsbuf_lh_isowell_tap_1 \
  */sky130_fd_sc_hd__lpflow_lsbuf_lh_isowell_tap_2 \
  */sky130_fd_sc_hd__lpflow_lsbuf_lh_isowell_tap_4 \
  */sky130_fd_sc_hd__sdfbbn_1 \
  */sky130_fd_sc_hd__sdfbbn_2 \
  */sky130_fd_sc_hd__sdfbbp_1 \
  */sky130_fd_sc_hd__sdfrbp_1 \
  */sky130_fd_sc_hd__sdfrbp_2 \
  */sky130_fd_sc_hd__sdfrtn_1 \
  */sky130_fd_sc_hd__sdfrtp_1 \
  */sky130_fd_sc_hd__sdfrtp_2 \
  */sky130_fd_sc_hd__sdfrtp_4 \
  */sky130_fd_sc_hd__sdfsbp_1 \
  */sky130_fd_sc_hd__sdfsbp_2 \
  */sky130_fd_sc_hd__sdfstp_1 \
  */sky130_fd_sc_hd__sdfstp_2 \
  */sky130_fd_sc_hd__sdfstp_4 \
  */sky130_fd_sc_hd__sdfxbp_1 \
  */sky130_fd_sc_hd__sdfxbp_2 \
  */sky130_fd_sc_hd__sdfxtp_1 \
  */sky130_fd_sc_hd__sdfxtp_2 \
  */sky130_fd_sc_hd__sdfxtp_4
