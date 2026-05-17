# Stage 3 Input Manifest

## Inputs

- target_activity_csv: `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_activity.csv` size_bytes=`2658495`
- def: `physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.def` size_bytes=`2498823083`
- netlist: `physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.v` size_bytes=`343483229`
- sdc: `physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.sdc` size_bytes=`136668`
- spef: `physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.spef` size_bytes=`2120927954`

## Stage 2 Caveats

- Phase 2 input is `proxy / non-signoff`.
- No SDF is available; Stage 3 records SDC/SPEF/netlist/DEF instead.
- Residual DRC and memory blackbox/proxy caveats remain inherited from Stage 2.
- ORFS final report JSON/log remain in the logs tree and were not moved.

## DEF Sanity

- diearea_dbu: `(0, 0, 13495456, 13495456)`
- raw_components: `4565776`
- skipped_physical_fill_tap_decap_tie: `3231778`
