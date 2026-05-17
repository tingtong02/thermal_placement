# Wrapper for ORFS Nangate45 PDN settings used by the reduced edahub overlay.
if {[info exists ::env(TP_ROOT)]} {
  set tp_root [file normalize $::env(TP_ROOT)]
} elseif {[info script] ne ""} {
  set tp_root [file normalize [file join [file dirname [info script]] ../../../..]]
} else {
  set tp_root [pwd]
}
source [file join $tp_root third_party OpenROAD-flow-scripts flow platforms nangate45 grid_strategy-M1-M4-M7.tcl]
