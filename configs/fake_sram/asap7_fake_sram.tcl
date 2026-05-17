# Fake SRAM ASAP7 collateral manifest for Cadence Tcl flows.
#
# Source this file from Genus or Innovus scripts. It only defines paths and
# helper procs; it does not read any libraries by itself.

set TP_ROOT [file normalize [file join [file dirname [info script]] ../..]]
if {[info exists ::env(TP_ROOT)] && $::env(TP_ROOT) ne ""} {
  set TP_ROOT [file normalize $::env(TP_ROOT)]
}

if {[info exists ::env(FAKE_SRAM_HOME)] && $::env(FAKE_SRAM_HOME) ne ""} {
  set FAKE_SRAM_HOME [file normalize $::env(FAKE_SRAM_HOME)]
} else {
  set FAKE_SRAM_HOME /home/lisihang/fake_sram
}

if {[info exists ::env(FAKE_SRAM_ASAP7_ROOT)] && $::env(FAKE_SRAM_ASAP7_ROOT) ne ""} {
  set FAKE_SRAM_ASAP7_ROOT [file normalize $::env(FAKE_SRAM_ASAP7_ROOT)]
} else {
  set FAKE_SRAM_ASAP7_ROOT [file join $FAKE_SRAM_HOME results asap7]
}

if {[info exists ::env(FAKE_SRAM_CADENCE_CACHE)] && $::env(FAKE_SRAM_CADENCE_CACHE) ne ""} {
  set FAKE_SRAM_CADENCE_CACHE [file normalize $::env(FAKE_SRAM_CADENCE_CACHE)]
} else {
  set FAKE_SRAM_CADENCE_CACHE [file join $TP_ROOT .cache fake_sram asap7]
}

set FAKE_SRAM_ASAP7_DESIGNS {
  Gemmini
}

proc tp_fake_sram_design_root {design} {
  global FAKE_SRAM_ASAP7_ROOT FAKE_SRAM_CADENCE_CACHE
  set cached [file join $FAKE_SRAM_CADENCE_CACHE $design]
  if {[file isdirectory $cached]} {
    return $cached
  }
  return [file join $FAKE_SRAM_ASAP7_ROOT $design]
}

proc tp_fake_sram_files {design kind} {
  set root [tp_fake_sram_design_root $design]
  switch -- $kind {
    lef { set pattern [file join $root lef *.lef] }
    lib { set pattern [file join $root lib *.lib] }
    db  { set pattern [file join $root db *.db] }
    verilog { set pattern [file join $root verilog *.sv] }
    default {
      error "unknown fake SRAM file kind '$kind'; expected lef, lib, db, or verilog"
    }
  }
  return [lsort [glob -nocomplain $pattern]]
}

proc tp_fake_sram_require_design {design} {
  set missing {}
  foreach kind {lef lib} {
    if {[llength [tp_fake_sram_files $design $kind]] == 0} {
      lappend missing $kind
    }
  }
  if {[llength $missing] != 0} {
    error "fake SRAM design '$design' is missing collateral kinds: $missing"
  }
}
