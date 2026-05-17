# Stage 1 tiled_matmul_ws Windows

## Inputs

- workload: `stage1_tiled_matmul_ws_signoff_20260429_r1`
- workload_base: `tiled_matmul_ws`
- waveform: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/tiled_matmul_ws/waves/tiled_matmul_ws-baremetal.stage1_tiled_matmul_ws_signoff_20260429_r1.vcd`
- region_activity: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_ws/stage1_tiled_matmul_ws_signoff_20260429_r1_region_activity.csv`
- simulator_log: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/tiled_matmul_ws/logs/tiled_matmul_ws-baremetal.stage1_tiled_matmul_ws_signoff_20260429_r1.log`
- time_steps: `21447935`
- last_time_ps: `10723925500`
- cpu_marker_seen: `True`
- gemmini_marker_seen: `True`
- cycle_markers: `[2279, 2967054]`

## Selected Windows

| window | start_ps | end_ps | selection |
| --- | ---: | ---: | --- |
| `cold_start` | 0 | 1072392550 | initial boot/program setup portion |
| `steady_high_load` | 1072392550 | 3753373925 | early post-boot interval containing WS Gemmini matmul before CPU reference |
| `cpu_gold_reference` | 3753373925 | 10723925500 | CPU reference/check phase after WS Gemmini marker |

## Region Toggle Summary

| region | signals | toggles | avg_normalized_activity |
| --- | ---: | ---: | ---: |
| `non_gemmini_context` | 9396 | 2337833454 | 8.828765e-04 |
| `tl_soc_glue` | 5337 | 1621898617 | 3.036685e-03 |
| `scratchpad` | 6837 | 109144543 | 2.398032e-05 |
| `controller` | 142 | 37829875 | 4.732434e-05 |
| `gemmini_other` | 3939 | 10880229 | 6.303224e-06 |
| `pe_array` | 6558 | 2191819 | 1.594334e-06 |
| `load_store_dma` | 393 | 14998 | 3.578215e-07 |
| `accumulator` | 0 | 0 | 0.000000e+00 |

## Method Note

The full VCD is already parsed once for aggregate activity. To avoid repeated large VCD scans, this window report uses simulator phase markers and aggregate activity. For WS, Gemmini execution occurs before the CPU reference phase, so the coarse high-load window is the early post-boot portion of the trace.
