# Stage 1 tiled_matmul_os Windows

## Inputs

- workload: `stage1_tiled_matmul_os_signoff_20260429_r1`
- workload_base: `tiled_matmul_os`
- waveform: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/tiled_matmul_os/waves/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_signoff_20260429_r1.vcd`
- region_activity: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_os/stage1_tiled_matmul_os_signoff_20260429_r1_region_activity.csv`
- simulator_log: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/tiled_matmul_os/logs/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_signoff_20260429_r1.log`
- time_steps: `20606655`
- last_time_ps: `10303285500`
- cpu_marker_seen: `True`
- gemmini_marker_seen: `True`
- cycle_markers: `[2967084, 3779]`

## Selected Windows

| window | start_ps | end_ps | selection |
| --- | ---: | ---: | --- |
| `cold_start` | 0 | 1030328550 | initial boot/program setup portion |
| `cpu_gold_reference` | 1030328550 | 9272956950 | CPU reference phase before OS Gemmini marker |
| `steady_high_load` | 9272956950 | 10303285500 | tail interval containing OS Gemmini matmul and accelerator completion |

## Region Toggle Summary

| region | signals | toggles | avg_normalized_activity |
| --- | ---: | ---: | ---: |
| `non_gemmini_context` | 9396 | 2233090944 | 8.635411e-04 |
| `tl_soc_glue` | 5337 | 1593316235 | 3.115504e-03 |
| `scratchpad` | 6837 | 104515396 | 2.380717e-05 |
| `controller` | 142 | 37074715 | 5.073546e-05 |
| `gemmini_other` | 3939 | 10543973 | 6.403923e-06 |
| `pe_array` | 6558 | 2390594 | 2.608938e-06 |
| `load_store_dma` | 393 | 20424 | 4.749315e-07 |
| `accumulator` | 0 | 0 | 0.000000e+00 |

## Method Note

The full VCD is already parsed once for aggregate activity. To avoid repeated large VCD scans, this window report uses simulator phase markers and aggregate activity. For OS, Gemmini execution occurs after the CPU reference phase, so the coarse high-load window is the tail of the trace.
