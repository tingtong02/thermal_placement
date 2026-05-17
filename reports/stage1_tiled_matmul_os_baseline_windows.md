# Stage 1 Tiled Matmul OS Baseline Windows

## Inputs

- workload: `stage1_tiled_matmul_os_baseline_20260423`
- waveform: `sim/waves/GemminiRocketConfig/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_baseline_20260423.vcd`
- region_activity: `sim/activity/stage1_tiled_matmul_os_baseline_20260423_region_activity.csv`
- simulator_log: `sim/logs/GemminiRocketConfig/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_baseline_20260423.log`
- time_steps: `20606655`
- last_time_ps: `10303285500`
- cpu_marker_seen: `True`
- gemmini_marker_seen: `True`
- cycle_markers: `[2967084, 3779]`

## Selected Windows

| window | start_ps | end_ps | selection |
| --- | ---: | ---: | --- |
| `cold_start` | 0 | 1030328550 | initial boot/program setup portion |
| `cpu_gold_reference` | 1030328550 | 9272956950 | official tiled_matmul_os CPU reference phase before Gemmini marker |
| `steady_high_load` | 9272956950 | 10303285500 | tail interval containing Starting gemmini matmul and accelerator completion |

## Region Toggle Summary

| region | signals | toggles | avg_normalized_activity |
| --- | ---: | ---: | ---: |
| `non_gemmini_context` | 9396 | 2233458166 | 8.637783e-04 |
| `tl_soc_glue` | 5337 | 1593316235 | 3.115504e-03 |
| `scratchpad` | 6837 | 104515396 | 2.380717e-05 |
| `controller` | 142 | 37074715 | 5.073546e-05 |
| `gemmini_other` | 3939 | 10543973 | 6.403923e-06 |
| `pe_array` | 6558 | 2390594 | 2.608938e-06 |
| `load_store_dma` | 393 | 20424 | 4.749315e-07 |
| `accumulator` | 0 | 0 | 0.000000e+00 |

## Method Note

The full VCD is already parsed once for aggregate activity. To avoid repeated 41 GiB scans, this window report uses simulator phase markers and aggregate activity. The `steady_high_load` interval is therefore a coarse marker window, not yet a target-scoped PE-array active window. Stage 3 must refine the exact Gemmini accelerator-active interval before building grid power, or label the output as a proxy.
