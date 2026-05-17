# Stage 2 Genus synthesis skeleton for the active Cadence/full-ASAP7 route.

set tp_root [expr {[info exists ::env(TP_ROOT)] ? $::env(TP_ROOT) : "/home/lisihang/thermal_placement"}]
set run_root $::env(RUN_ROOT)
set out_root $::env(GENUS_OUT_ROOT)
set top $::env(STAGE2_TOP_MODULE)
set filelist $::env(STAGE2_RTL_FILELIST)
set cpus [expr {[info exists ::env(TP_CADENCE_GENUS_CPUS)] ? $::env(TP_CADENCE_GENUS_CPUS) : 8}]

source [file join $tp_root configs asap7_full asap7_full.tcl]
source [file join $tp_root configs fake_sram asap7_fake_sram.tcl]

tp_asap7_require_full_pdk
tp_asap7_require_liberty_cache
set fake_sram_design [expr {[info exists ::env(FAKE_SRAM_DESIGN)] ? $::env(FAKE_SRAM_DESIGN) : "Gemmini"}]
tp_fake_sram_require_design $fake_sram_design

set_db max_cpus_per_server $cpus
set_db information_level 5

set asap7_libs [tp_asap7_liberty_files]
set fake_sram_libs [tp_fake_sram_files $fake_sram_design lib]
read_libs [concat $asap7_libs $fake_sram_libs]

set rtl_files {}
set fh [open $filelist r]
while {[gets $fh line] >= 0} {
  set line [string trim $line]
  if {$line eq "" || [string match "#*" $line]} {
    continue
  }
  if {[regexp {\.(sv|v)$} $line] && [file exists $line]} {
    lappend rtl_files $line
  }
}
close $fh

foreach stub [tp_fake_sram_files $fake_sram_design verilog] {
  lappend rtl_files $stub
}

if {[llength $rtl_files] == 0} {
  error "no Verilog/SystemVerilog files found in $filelist"
}

read_hdl -sv $rtl_files
elaborate $top
check_design -unresolved

read_sdc [file join $run_root physical cadence config constraint.sdc]

syn_generic
syn_map
syn_opt

report_qor > [file join $out_root reports genus_qor.rpt]
report_timing > [file join $out_root reports genus_timing.rpt]
report_area > [file join $out_root reports genus_area.rpt]
report_power > [file join $out_root reports genus_power.rpt]

write_hdl > [file join $out_root results ${top}.mapped.v]
write_sdc > [file join $out_root results ${top}.mapped.sdc]
write_db [file join $out_root db ${top}.genus.db]

puts "TP_STAGE2_GENUS_DONE top=$top out=$out_root"
exit 0
