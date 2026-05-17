# Reduced Nangate45 technology library from third_party/edahub.
# This is not a complete PDK and is not signoff-ready.

if {[info exists ::env(TP_ROOT)]} {
  set tp_root [file normalize $::env(TP_ROOT)]
} elseif {[info script] ne ""} {
  set tp_root [file normalize [file join [file dirname [info script]] ../..]]
} else {
  set tp_root [pwd]
}
set edahub_tech_root [file join $tp_root third_party edahub edahub technology]
set techlib_root [file join $edahub_tech_root nangate45]

set TECHLIB(NAME) nangate45
set TECHLIB(DISPLAY_NAME) Nangate45
set TECHLIB(IS_COMPLETE_PDK) 0
set TECHLIB(NOTE) "Reduced edahub Nangate45 standard-cell library for early synthesis and initial P&R only."
set TECHLIB(ROOT) $techlib_root
set TECHLIB(DB_FILES) [list [file join $techlib_root db NangateOpenCellLibrary.db]]
set TECHLIB(LIB_FILES) [list [file join $techlib_root lib Nangate45_typ.lib]]
set TECHLIB(SETUP_LIB_FILES) [list [file join $techlib_root lib Nangate45_slow.lib]]
set TECHLIB(HOLD_LIB_FILES) [list [file join $techlib_root lib Nangate45_fast.lib]]
set TECHLIB(TECH_LEF) [file join $techlib_root lef Nangate45_tech.lef]
set TECHLIB(SC_LEF) [file join $techlib_root lef Nangate45_stdcell.lef]
set TECHLIB(LEF_FILES) [list $TECHLIB(TECH_LEF) $TECHLIB(SC_LEF)]
set TECHLIB(QRC_TECH_FILES) [list]
set TECHLIB(DONT_USE_CELLS) [list TAPCELL_X1 FILLCELL_X1 AOI211_X1 OAI211_X1]
