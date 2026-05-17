# Full ASAP7 manifest for Cadence Tcl flows.
#
# Source this file from Genus or Innovus scripts. It defines paths and helper
# procs only; it does not read libraries or technology files by itself.

if {[info exists ::env(TP_ROOT)] && $::env(TP_ROOT) ne ""} {
  set TP_ROOT [file normalize $::env(TP_ROOT)]
} else {
  set TP_ROOT /home/lisihang/thermal_placement
}

if {[info exists ::env(ASAP7_HOME)] && $::env(ASAP7_HOME) ne ""} {
  set ASAP7_HOME [file normalize $::env(ASAP7_HOME)]
} else {
  set ASAP7_HOME /home/lisihang/asap7
}

set ASAP7_STDCELL_VERSION [expr {[info exists ::env(ASAP7_STDCELL_VERSION)] && $::env(ASAP7_STDCELL_VERSION) ne "" ? $::env(ASAP7_STDCELL_VERSION) : "asap7sc7p5t_28"}]
set ASAP7_STDCELL_ROOT [file join $ASAP7_HOME $ASAP7_STDCELL_VERSION]

if {[info exists ::env(ASAP7_LIB_CACHE)] && $::env(ASAP7_LIB_CACHE) ne ""} {
  set ASAP7_LIB_CACHE [file normalize $::env(ASAP7_LIB_CACHE)]
} else {
  set ASAP7_LIB_CACHE [file join $TP_ROOT .cache asap7 $ASAP7_STDCELL_VERSION NLDM]
}

set ASAP7_TECH_LEF [file join $ASAP7_STDCELL_ROOT techlef_misc asap7_tech_1x_201209.lef]
set ASAP7_QRC_FILE [file join $ASAP7_STDCELL_ROOT qrc qrcTechFile_typ03_unscaledV02]
set ASAP7_VT_CLASSES {RVT LVT SLVT}
set ASAP7_CORNER TT

proc tp_asap7_require_full_pdk {} {
  global ASAP7_STDCELL_ROOT ASAP7_TECH_LEF ASAP7_QRC_FILE
  set missing {}
  foreach path [list $ASAP7_STDCELL_ROOT $ASAP7_TECH_LEF $ASAP7_QRC_FILE] {
    if {![file exists $path]} {
      lappend missing $path
    }
  }
  if {[llength $missing] != 0} {
    error "missing full ASAP7 paths: $missing"
  }
}

proc tp_asap7_lef_files {} {
  global ASAP7_STDCELL_ROOT ASAP7_TECH_LEF
  set lefs [list $ASAP7_TECH_LEF]
  foreach pattern [list \
    [file join $ASAP7_STDCELL_ROOT LEF *_R_1x_*.lef] \
    [file join $ASAP7_STDCELL_ROOT LEF *_L_1x_*.lef] \
    [file join $ASAP7_STDCELL_ROOT LEF *_SL_1x_*.lef] \
  ] {
    foreach lef [lsort [glob -nocomplain $pattern]] {
      lappend lefs $lef
    }
  }
  return $lefs
}

proc tp_asap7_liberty_files {} {
  global ASAP7_LIB_CACHE ASAP7_VT_CLASSES ASAP7_CORNER
  set libs {}
  foreach vt $ASAP7_VT_CLASSES {
    foreach lib [lsort [glob -nocomplain [file join $ASAP7_LIB_CACHE *_${vt}_${ASAP7_CORNER}_nldm_*.lib]]] {
      lappend libs $lib
    }
  }
  return $libs
}

proc tp_asap7_qrc_file {} {
  global ASAP7_QRC_FILE
  return $ASAP7_QRC_FILE
}

proc tp_asap7_require_liberty_cache {} {
  set libs [tp_asap7_liberty_files]
  if {[llength $libs] == 0} {
    global ASAP7_LIB_CACHE
    error "missing ASAP7 Liberty cache at $ASAP7_LIB_CACHE; run scripts/prepare_asap7_liberty_cache.py"
  }
}
