# Stage 1 mvin_mvout Windows

## Inputs

- workload: `stage1_mvin_mvout_signoff_20260429_r1`
- workload_base: `mvin_mvout`
- waveform: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/mvin_mvout/waves/mvin_mvout-baremetal.stage1_mvin_mvout_signoff_20260429_r1.vcd`
- region_activity: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/mvin_mvout/stage1_mvin_mvout_signoff_20260429_r1_region_activity.csv`
- simulator_log: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/mvin_mvout/logs/mvin_mvout-baremetal.stage1_mvin_mvout_signoff_20260429_r1.log`
- time_steps: `1337595`
- last_time_ps: `668755500`
- cpu_marker_seen: `False`
- gemmini_marker_seen: `False`

## Selected Windows

| window | start_ps | end_ps | selection |
| --- | ---: | ---: | --- |
| `cold_start` | 0 | 66875550 | initial boot/program setup portion |
| `data_movement_active` | 66875550 | 601879950 | central interval for mvin/mvout data movement and control activity |
| `program_completion` | 601879950 | 668755500 | final program completion tail |

## Region Toggle Summary

| region | signals | toggles | avg_normalized_activity |
| --- | ---: | ---: | ---: |
| `non_gemmini_context` | 9396 | 93531378 | 4.308248e-04 |
| `tl_soc_glue` | 5337 | 21088777 | 4.877942e-04 |
| `scratchpad` | 6837 | 7395149 | 2.992237e-05 |
| `gemmini_other` | 3939 | 686635 | 6.557725e-06 |
| `controller` | 142 | 528322 | 1.407800e-05 |
| `pe_array` | 6558 | 272826 | 3.096180e-06 |
| `load_store_dma` | 393 | 13309 | 4.400634e-06 |
| `accumulator` | 0 | 0 | 0.000000e+00 |

## Method Note

The full VCD is already parsed once for aggregate activity. To avoid repeated large VCD scans, this window report uses simulator phase markers and aggregate activity. For mvin_mvout, no matmul marker is expected; the coarse movement window covers the central active program interval.
