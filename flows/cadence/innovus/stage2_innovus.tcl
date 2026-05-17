# Stage 2 Innovus implementation skeleton for the active Cadence/full-ASAP7 route.

set tp_root [expr {[info exists ::env(TP_ROOT)] ? $::env(TP_ROOT) : "/home/lisihang/thermal_placement"}]
set out_root $::env(INNOVUS_OUT_ROOT)
set netlist $::env(STAGE2_GENUS_NETLIST)
set sdc $::env(STAGE2_GENUS_SDC)
set cpus [expr {[info exists ::env(TP_CADENCE_INNOVUS_CPUS)] ? $::env(TP_CADENCE_INNOVUS_CPUS) : 8}]
set fake_sram_design [expr {[info exists ::env(FAKE_SRAM_DESIGN)] ? $::env(FAKE_SRAM_DESIGN) : "Gemmini"}]

source [file join $tp_root configs asap7_full asap7_full.tcl]
source [file join $tp_root configs fake_sram asap7_fake_sram.tcl]

tp_asap7_require_full_pdk
tp_asap7_require_liberty_cache
tp_fake_sram_require_design $fake_sram_design

setMultiCpuUsage -localCpu $cpus

set asap7_lefs [tp_asap7_lef_files]
set fake_sram_lefs [tp_fake_sram_files $fake_sram_design lef]
read_physical -lef [concat $asap7_lefs $fake_sram_lefs]

set init_verilog $netlist
set init_top_cell [expr {[info exists ::env(STAGE2_TOP_MODULE)] ? $::env(STAGE2_TOP_MODULE) : "Gemmini"}]
set init_lef_file [concat $asap7_lefs $fake_sram_lefs]
set init_pwr_net VDD
set init_gnd_net VSS
init_design

read_sdc $sdc

floorPlan -site asap7sc7p5t -r 1.0 0.70 2.0 2.0 2.0 2.0
place_design
ccopt_design
routeDesign
extractRC

timeDesign -postRoute -outDir [file join $out_root reports timing_postroute]
report_area > [file join $out_root reports innovus_area.rpt]
report_power > [file join $out_root reports innovus_power.rpt]
verify_drc -report [file join $out_root reports innovus_drc.rpt]

write_def [file join $out_root results ${init_top_cell}.route.def]
write_verilog [file join $out_root results ${init_top_cell}.route.v]
write_sdf [file join $out_root results ${init_top_cell}.route.sdf]
write_spef [file join $out_root results ${init_top_cell}.route.spef]
streamOut [file join $out_root results ${init_top_cell}.route.gds] -mapFile "" -libName DesignLib -units 1000 -mode ALL
saveDesign [file join $out_root db ${init_top_cell}.route.enc]

puts "TP_STAGE2_INNOVUS_DONE top=$init_top_cell out=$out_root"
exit 0
