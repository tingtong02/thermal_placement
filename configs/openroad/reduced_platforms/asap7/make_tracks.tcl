# Wrapper for ORFS asap7 track generation used by the reduced edahub overlay.
if {[info exists ::env(TP_ROOT)]} {
  set tp_root [file normalize $::env(TP_ROOT)]
} elseif {[info script] ne ""} {
  set tp_root [file normalize [file join [file dirname [info script]] ../../../..]]
} else {
  set tp_root [pwd]
}
source [file join $tp_root third_party OpenROAD-flow-scripts flow platforms asap7 openRoad make_tracks.tcl]
