# Reduced sky130hd technology library from third_party/edahub.
# This is not a complete PDK and is not signoff-ready.

if {[info exists ::env(TP_ROOT)]} {
  set tp_root [file normalize $::env(TP_ROOT)]
} elseif {[info script] ne ""} {
  set tp_root [file normalize [file join [file dirname [info script]] ../..]]
} else {
  set tp_root [pwd]
}
set edahub_tech_root [file join $tp_root third_party edahub edahub technology]
set techlib_root [file join $edahub_tech_root sky130hd]

set TECHLIB(NAME) sky130hd
set TECHLIB(DISPLAY_NAME) sky130hd
set TECHLIB(IS_COMPLETE_PDK) 0
set TECHLIB(NOTE) "Reduced edahub sky130hd standard-cell library for early synthesis and initial P&R only."
set TECHLIB(ROOT) $techlib_root
set TECHLIB(DB_FILES) [list [file join $techlib_root db sky130_fd_sc_hd__tt_025C_1v80.db]]
set TECHLIB(LIB_FILES) [list [file join $techlib_root lib sky130_fd_sc_hd__tt_025C_1v80.lib]]
set TECHLIB(SETUP_LIB_FILES) [list [file join $techlib_root lib sky130_fd_sc_hd__ff_n40C_1v95.lib]]
set TECHLIB(HOLD_LIB_FILES) [list [file join $techlib_root lib sky130_fd_sc_hd__ss_n40C_1v40.lib]]
set TECHLIB(TECH_LEF) [file join $techlib_root lef sky130hd.tlef]
set TECHLIB(SC_LEF) [file join $techlib_root lef sky130_fd_sc_hd_merged.lef]
set TECHLIB(LEF_FILES) [list $TECHLIB(TECH_LEF) $TECHLIB(SC_LEF)]
set TECHLIB(QRC_TECH_FILES) [list]
set TECHLIB(DONT_USE_CELLS) [list \
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
  */sky130_fd_sc_hd__sdfxtp_4]
