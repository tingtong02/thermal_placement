# Stage 1 Multi-Workload Signoff Summary

## Status

- result: `accepted`
- quality: `project-signoff/high-confidence` for Stage 1 RTL activity; no proxy/fallback waveform or old result was used.
- config: `GemminiRocketConfig` / mesh16x16 tile1x1 DIM16.
- workloads: `tiled_matmul_os`, `tiled_matmul_ws`, `mvin_mvout`.
- run_root: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/`
- next_stage: `Stage 2 ASAP7 standard-cell implementation` is ready to start.

## Execution Parameters

| parameter | value | reason |
| --- | ---: | --- |
| `MAKE_JOBS` | 1 | Debug simulator already existed; avoid unnecessary rebuild parallelism during run. |
| `VERILATOR_THREADS` | 16 | Historical local threading smoke showed 16 was the best accepted simulator thread setting among tested values. |
| `VCD_PARSER_WORKERS` | 128 | Historical parser smoke showed fastest accepted VCD parse among tested worker counts with identical CSV output. |
| `NUMACTL` | 0 | Host lacks `numactl`; disabling Chipyard NUMA wrapper is an environment compatibility setting, not a result downgrade. |
| `USE_FST` | 0 | VCD is the required Stage 1 signoff waveform format in the active plan. |
| `TIMEOUT_CYCLES` | 100000000 | Full functional runs, no timeout hit. |

## Workload Evidence

| workload | role | sim_status | VCD | last_time_ps | target_toggle_share | primary window | key cycles |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `tiled_matmul_os` | output-stationary GEMM compute baseline | 0 | 40.93 GiB | 10303285500 | 3.882% | `steady_high_load` 9272956950..10303285500 ps | Cycles taken: 2967084<br>Cycles taken: 3779 |
| `tiled_matmul_ws` | weight-stationary GEMM dataflow contrast | 0 | 42.42 GiB | 10723925500 | 3.885% | `steady_high_load` 1072392550..3753373925 ps | Cycles taken: 2279<br>Cycles taken: 2967054 |
| `mvin_mvout` | memory/control movement contrast; not a PE compute-heavy GEMM | 0 | 1.75 GiB | 668755500 | 7.202% | `data_movement_active` 66875550..601879950 ps | not applicable |

## Gemmini Region Toggles

| workload | PE array | controller | load/store DMA | scratchpad | other Gemmini | accumulator |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `tiled_matmul_os` | 2390594 | 37074715 | 20424 | 104515396 | 10543973 | 0 |
| `tiled_matmul_ws` | 2191819 | 37829875 | 14998 | 109144543 | 10880229 | 0 |
| `mvin_mvout` | 272826 | 528322 | 13309 | 7395149 | 686635 | 0 |

## Artifact Index

### tiled_matmul_os

- manifest: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/tiled_matmul_os/stage1_tiled_matmul_os_signoff_manifest.txt`
- activity report: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/tiled_matmul_os/stage1_tiled_matmul_os_signoff_activity_summary.md`
- window report: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/tiled_matmul_os/stage1_tiled_matmul_os_signoff_windows.md`
- waveform: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/tiled_matmul_os/waves/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_signoff_20260429_r1.vcd`
- signal activity: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_os/stage1_tiled_matmul_os_signoff_20260429_r1_signal_activity.csv`
- region activity: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_os/stage1_tiled_matmul_os_signoff_20260429_r1_region_activity.csv`
- window activity: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_os/stage1_tiled_matmul_os_signoff_20260429_r1_window_activity.csv`

### tiled_matmul_ws

- manifest: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/tiled_matmul_ws/stage1_tiled_matmul_ws_signoff_manifest.txt`
- activity report: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/tiled_matmul_ws/stage1_tiled_matmul_ws_signoff_activity_summary.md`
- window report: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/tiled_matmul_ws/stage1_tiled_matmul_ws_signoff_windows.md`
- waveform: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/tiled_matmul_ws/waves/tiled_matmul_ws-baremetal.stage1_tiled_matmul_ws_signoff_20260429_r1.vcd`
- signal activity: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_ws/stage1_tiled_matmul_ws_signoff_20260429_r1_signal_activity.csv`
- region activity: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_ws/stage1_tiled_matmul_ws_signoff_20260429_r1_region_activity.csv`
- window activity: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_ws/stage1_tiled_matmul_ws_signoff_20260429_r1_window_activity.csv`

### mvin_mvout

- manifest: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/mvin_mvout/stage1_mvin_mvout_signoff_manifest.txt`
- activity report: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/mvin_mvout/stage1_mvin_mvout_signoff_activity_summary.md`
- window report: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/mvin_mvout/stage1_mvin_mvout_signoff_windows.md`
- waveform: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/mvin_mvout/waves/mvin_mvout-baremetal.stage1_mvin_mvout_signoff_20260429_r1.vcd`
- signal activity: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/mvin_mvout/stage1_mvin_mvout_signoff_20260429_r1_signal_activity.csv`
- region activity: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/mvin_mvout/stage1_mvin_mvout_signoff_20260429_r1_region_activity.csv`
- window activity: `/home/lisihang/thermal_placement/runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/mvin_mvout/stage1_mvin_mvout_signoff_20260429_r1_window_activity.csv`

## Notes

- `mvin_mvout` is accepted as memory/control movement evidence, not as a PE compute-heavy workload. It does not print matmul markers by design.
- Stage 1 reports were regenerated with workload-aware summary/window logic so that OS, WS, and mvin/mvout use correct phase semantics.
- Whole-trace top toggles remain dominated by SoC/Rocket/TileLink context; downstream Stage 2/3 must preserve the active research boundary around Gemmini PE array, control logic, and nearby datapath.
