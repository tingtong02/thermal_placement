# Reduced asap7 technology library from third_party/edahub.
# This is not a complete PDK and is not signoff-ready.

if {[info exists ::env(TP_ROOT)]} {
  set tp_root [file normalize $::env(TP_ROOT)]
} elseif {[info script] ne ""} {
  set tp_root [file normalize [file join [file dirname [info script]] ../..]]
} else {
  set tp_root [pwd]
}
set edahub_tech_root [file join $tp_root third_party edahub edahub technology]
set techlib_root [file join $edahub_tech_root asap7]

set TECHLIB(NAME) asap7
set TECHLIB(DISPLAY_NAME) MiniAsap7
set TECHLIB(IS_COMPLETE_PDK) 0
set TECHLIB(NOTE) "Reduced edahub asap7 RVT TT standard-cell library for early synthesis and initial P&R only."
set TECHLIB(ROOT) $techlib_root
set TECHLIB(DB_FILES) [list \
  [file join $techlib_root db asap7sc7p5t_SIMPLE_RVT_TT_nldm_201020.db] \
  [file join $techlib_root db asap7sc7p5t_SEQ_RVT_TT_nldm_201020.db] \
  [file join $techlib_root db asap7sc7p5t_AO_RVT_TT_nldm_201020.db] \
  [file join $techlib_root db asap7sc7p5t_OA_RVT_TT_nldm_201020.db] \
  [file join $techlib_root db asap7sc7p5t_INVBUF_RVT_TT_nldm_201020.db]]
set TECHLIB(LIB_FILES) [list \
  [file join $techlib_root lib asap7sc7p5t_SIMPLE_RVT_TT_nldm_201020.lib] \
  [file join $techlib_root lib asap7sc7p5t_SEQ_RVT_TT_nldm_201020.lib] \
  [file join $techlib_root lib asap7sc7p5t_AO_RVT_TT_nldm_201020.lib] \
  [file join $techlib_root lib asap7sc7p5t_OA_RVT_TT_nldm_201020.lib] \
  [file join $techlib_root lib asap7sc7p5t_INVBUF_RVT_TT_nldm_201020.lib]]
set TECHLIB(SETUP_LIB_FILES) $TECHLIB(LIB_FILES)
set TECHLIB(HOLD_LIB_FILES) $TECHLIB(LIB_FILES)
set TECHLIB(TECH_LEF) [file join $techlib_root lef asap7_tech_4x_201209.lef]
set TECHLIB(SC_LEF) [file join $techlib_root lef asap7sc7p5t_27_R_4x_201211.lef]
set TECHLIB(LEF_FILES) [list $TECHLIB(TECH_LEF) $TECHLIB(SC_LEF)]
set TECHLIB(QRC_TECH_FILES) [list [file join $techlib_root qrc qrcTechFile_typ03_scaled4xV06]]
set TECHLIB(DONT_USE_CELLS) [list \
  */ICGx*DC* */AND4x1* */SDFLx2* */AO21x1* */XOR2x2* \
  */OAI31xp33* */OAI221xp5* */SDFLx3* */SDFLx1* */AOI211xp5* \
  */OAI322xp33* */OR2x6* */A2O1A1O1Ixp25* */XNOR2x1* \
  */OAI32xp33* */FAx1* */OAI21x1* */OAI31xp67* */OAI33xp33* \
  */AO21x2* */AOI32xp33*]
