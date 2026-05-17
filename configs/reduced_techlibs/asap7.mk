# Reduced asap7 technology library from third_party/edahub.
# This is not a complete PDK and is not signoff-ready.

TP_ROOT ?= $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
EDAHUB_HOME ?= $(TP_ROOT)/third_party/edahub
EDAHUB_TECH_ROOT ?= $(EDAHUB_HOME)/edahub/technology

TECHLIB_NAME := asap7
TECHLIB_DISPLAY_NAME := MiniAsap7
TECHLIB_IS_COMPLETE_PDK := 0
TECHLIB_NOTE := Reduced edahub asap7 RVT TT standard-cell library for early synthesis and initial P&R only.
TECHLIB_ROOT := $(EDAHUB_TECH_ROOT)/asap7

TECHLIB_DB_FILES := \
  $(TECHLIB_ROOT)/db/asap7sc7p5t_SIMPLE_RVT_TT_nldm_201020.db \
  $(TECHLIB_ROOT)/db/asap7sc7p5t_SEQ_RVT_TT_nldm_201020.db \
  $(TECHLIB_ROOT)/db/asap7sc7p5t_AO_RVT_TT_nldm_201020.db \
  $(TECHLIB_ROOT)/db/asap7sc7p5t_OA_RVT_TT_nldm_201020.db \
  $(TECHLIB_ROOT)/db/asap7sc7p5t_INVBUF_RVT_TT_nldm_201020.db

TECHLIB_LIB_FILES := \
  $(TECHLIB_ROOT)/lib/asap7sc7p5t_SIMPLE_RVT_TT_nldm_201020.lib \
  $(TECHLIB_ROOT)/lib/asap7sc7p5t_SEQ_RVT_TT_nldm_201020.lib \
  $(TECHLIB_ROOT)/lib/asap7sc7p5t_AO_RVT_TT_nldm_201020.lib \
  $(TECHLIB_ROOT)/lib/asap7sc7p5t_OA_RVT_TT_nldm_201020.lib \
  $(TECHLIB_ROOT)/lib/asap7sc7p5t_INVBUF_RVT_TT_nldm_201020.lib

TECHLIB_SETUP_LIB_FILES := $(TECHLIB_LIB_FILES)
TECHLIB_HOLD_LIB_FILES := $(TECHLIB_LIB_FILES)

TECHLIB_TECH_LEF := $(TECHLIB_ROOT)/lef/asap7_tech_4x_201209.lef
TECHLIB_SC_LEF := $(TECHLIB_ROOT)/lef/asap7sc7p5t_27_R_4x_201211.lef
TECHLIB_LEF_FILES := $(TECHLIB_TECH_LEF) $(TECHLIB_SC_LEF)

TECHLIB_QRC_TECH_FILES := $(TECHLIB_ROOT)/qrc/qrcTechFile_typ03_scaled4xV06
TECHLIB_DONT_USE_CELLS := \
  */ICGx*DC* */AND4x1* */SDFLx2* */AO21x1* */XOR2x2* \
  */OAI31xp33* */OAI221xp5* */SDFLx3* */SDFLx1* */AOI211xp5* \
  */OAI322xp33* */OR2x6* */A2O1A1O1Ixp25* */XNOR2x1* \
  */OAI32xp33* */FAx1* */OAI21x1* */OAI31xp67* */OAI33xp33* \
  */AO21x2* */AOI32xp33*
