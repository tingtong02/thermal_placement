# Stage 3 Power Trace Method

## Acceptance Level

Stage 3 output is a reproducible proxy grid-power waveform for Stage 4 thermal-flow prototyping. It is not signoff power.

## Inputs

- target_activity_csv: `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_activity.csv`
- target_bin_csv: `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_bins.csv`
- def: `physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.def`
- netlist: `physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.v`
- sdc: `physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.sdc`
- spef: `physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.spef`
- liberty_files: `5`
- SDF: unavailable from Phase 2 proxy flow.

## Window

- candidate_start_ps: `9272956950`
- candidate_end_ps: `10303285500`
- refined_start_ps: `10222791082`
- refined_end_ps: `10238889965`
- time_steps: `2060658`

## Grid And Geometry

- grid: `64 x 64`
- diearea_dbu: `(0, 0, 13495456, 13495456)`
- active_components: `1333998`
- raw_components: `4565776`
- skipped_fill_tap_decap_tie: `3231778`

## Power Model

- proxy_total_power_w: `1.0`
- normalized_output_power_w: `1`
- transient_bin_scaling: `max target bin = proxy_total_power_w`
- default_cell_area_for_missing_liberty_area: `0.1458`
- Model: target-window RTL activity is aggregated by Gemmini region, then distributed over placed standard-cell area in the matching DEF region.
- `clock_tree` and `unmapped_standard_cell` receive low background proxy activity so their placed area remains visible without dominating target regions.
- `6_report.log` / `6_report.json` IR numbers are not used.

| region | instances | proxy_power_w | share |
| --- | ---: | ---: | ---: |
| `gemmini_other` | 291752 | 0.40850387643 | 0.40850388 |
| `pe_array` | 462375 | 0.252617470616 | 0.25261747 |
| `scratchpad` | 317024 | 0.164598979832 | 0.16459898 |
| `unmapped_standard_cell` | 152968 | 0.123314676667 | 0.12331468 |
| `controller` | 56261 | 0.0384145625341 | 0.038414563 |
| `clock_tree` | 23198 | 0.00917649014461 | 0.0091764901 |
| `load_store_dma` | 30420 | 0.00337394377624 | 0.0033739438 |

## Limitations

- No gate-level SAIF or SDF is available, so switching power is a calibrated proxy rather than OpenSTA signoff power.
- SPEF/SDC/netlist are recorded as Stage 2 electrical context, but this first Stage 3 artifact does not solve detailed net capacitance power per gate.
- Memory macro body power is not modeled as detailed SRAM thermal power.
