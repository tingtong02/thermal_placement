# Stage 1 mvin_mvout Activity Summary

## Scope

- stage: `1`
- workload: `mvin_mvout`
- run_tag: `stage1_mvin_mvout_signoff_20260429_r1`
- config: `GemminiRocketConfig`
- role: `memory/control movement contrast, not a PE compute-heavy GEMM`
- dataflow_or_behavior: `Gemmini mvin/mvout data movement; no tiled_matmul_auto dataflow marker expected`
- input_shape: `N=8 DIM x DIM matrices; effective matrix shape is 16 x 16 for this config`

## Functional Run

- sim_status: `0`
- verilator_finish_seen: `True`
- cpu_matmul_marker_seen: `False`
- gemmini_matmul_marker_seen: `False`
- failure_marker_seen: `False`

## Artifacts

- binary: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/workloads/mvin_mvout/mvin_mvout-baremetal` (17.45 KiB)
- stdout log: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/mvin_mvout/logs/mvin_mvout-baremetal.stage1_mvin_mvout_signoff_20260429_r1.log` (408.00 B)
- disassembly/out log: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/mvin_mvout/logs/mvin_mvout-baremetal.stage1_mvin_mvout_signoff_20260429_r1.out` (3.21 MiB)
- waveform: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/mvin_mvout/waves/mvin_mvout-baremetal.stage1_mvin_mvout_signoff_20260429_r1.vcd` (1.75 GiB)
- signal activity CSV: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/mvin_mvout/stage1_mvin_mvout_signoff_20260429_r1_signal_activity.csv` (6.90 MiB)
- region activity CSV: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/mvin_mvout/stage1_mvin_mvout_signoff_20260429_r1_region_activity.csv` (901.00 B)
- window CSV: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/mvin_mvout/stage1_mvin_mvout_signoff_20260429_r1_window_activity.csv` (512.00 B)
- window report: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/mvin_mvout/stage1_mvin_mvout_signoff_windows.md`

## Activity Parse

- parsed_time_steps: `1337595`
- last_time_ps: `668755500`
- total_region_toggles: `123516396`
- gemmini_target_region_toggles: `8896241`
- gemmini_target_region_toggle_share: `7.202478%`

## Region Activity

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

## Research Boundary Check

- The Stage 1 trace is a full `GemminiRocketConfig` SoC/TestHarness waveform, so whole-trace top toggles are expected to include Rocket core, cache, and TileLink context.
- For the active research target, the relevant check is whether Gemmini PE/control/datapath buckets required for this workload are non-zero and internally plausible.
- PE array: `signals=6558` `toggles=272826`
- Gemmini controller: `signals=142` `toggles=528322`
- Load/store DMA: `signals=393` `toggles=13309`
- Scratchpad-side datapath/context: `signals=6837` `toggles=7395149`
- Other Gemmini datapath/control: `signals=3939` `toggles=686635`
- `accumulator` remains zero in the current bucket summary, which is acceptable for this stage because memory arrays are not the detailed thermal target in the active plan.

## Targeted Gemmini Region Highlights

### PE array

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 331 | 31 | `...river.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh.io_resp_bits_data_1_0[19:0]` |
| 2 | 320 | 30 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh.RegShifted_r_656_0[19:0]` |
| 3 | 315 | 18 | `...iptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh.mesh.mesh_14_15.tile_0_0.mac_unit.io_in_c[31:0]` |
| 4 | 315 | 15 | `...iptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh.mesh.mesh_12_10.tile_0_0.mac_unit.io_in_c[31:0]` |
| 5 | 308 | 29 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh.RegShifted_r_655_0[19:0]` |

### Gemmini controller

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 739 | 31 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.mod.cmd_q.ram_ext.W0_data[273:0]` |
| 2 | 731 | 30 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.mod.cmd_q.ram_ext.R0_data[273:0]` |
| 3 | 715 | 30 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.mod_1.cmd_q.ram_ext.W0_data[273:0]` |
| 4 | 583 | 28 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.mod_1.cmd_q.ram_ext.R0_data[273:0]` |
| 5 | 338 | 11 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.mod.cmd_q.ram_ext.Memory[0][273:0]` |

### Load/store DMA

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 1080 | 180 | `...ver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.load_controller.io_dma_resp_bits_bytesRead[15:0]` |
| 2 | 900 | 180 | `...op0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.load_controller.cmd_tracker.io_request_returned_bits_bytes_read[10:0]` |
| 3 | 842 | 18 | `...Driver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.store_controller.cmd_q.ram_ext.W0_data[273:0]` |
| 4 | 661 | 19 | `...Driver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.store_controller.cmd_q.ram_ext.R0_data[273:0]` |
| 5 | 594 | 18 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.load_controller.cmd_q.ram_ext.W0_data[245:0]` |

### Scratchpad-side datapath/context

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 48487 | 218 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.vsm_in_q_1.ram_ext.W0_data[624:0]` |
| 2 | 44969 | 218 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.reader.io_resp_bits_data[511:0]` |
| 3 | 16231 | 218 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.vsm_in_q.ram_ext.W0_data[256:0]` |
| 4 | 14500 | 294 | `...ver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_2.nodeOut_a_q.ram_ext.W0_data[191:0]` |
| 5 | 13999 | 322 | `...iver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_2.nodeIn_d_q.ram_ext.R0_data[147:0]` |

### Other Gemmini datapath/control

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 667977 | 333987 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.reservation_station.cntr_value[20:0]` |
| 2 | 830 | 418 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.pipeline_stall_counter[31:0]` |
| 3 | 712 | 375 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.reservation_station.cycles_since_issue[15:0]` |
| 4 | 662 | 29 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.unrolled_cmd_q.ram_ext.W0_data[273:0]` |
| 5 | 562 | 30 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.raw_cmd_q.ram_ext.W0_data[273:0]` |

## Global Top Toggle Signals (Full Trace Context)

| rank | region | toggles | changes | signal |
| ---: | --- | ---: | ---: | --- |
| 1 | `non_gemmini_context` | 1337504 | 668756 | `TestDriver.trace_count[63:0]` |
| 2 | `tl_soc_glue` | 1092040 | 4381 | `...testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.dcache.data.rockettile_dcache_data_arrays_0.RW0_wdata[511:0]` |
| 3 | `tl_soc_glue` | 1091816 | 4381 | `...testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.dcache.data.rockettile_dcache_data_arrays_1.RW0_wdata[511:0]` |
| 4 | `non_gemmini_context` | 667988 | 333987 | `TestDriver.testHarness.chiptop0.system.chipyard_prcictrl_domain.reset_setter.monitor.watchdog[31:0]` |
| 5 | `non_gemmini_context` | 667987 | 333987 | `TestDriver.testHarness.chiptop0.system.coh_wrapper.l2.ctrls.monitor.watchdog[31:0]` |
| 6 | `non_gemmini_context` | 667985 | 333987 | `TestDriver.testHarness.chiptop0.system.plic_domain.plic.monitor.watchdog[31:0]` |
| 7 | `non_gemmini_context` | 667985 | 333987 | `TestDriver.testHarness.chiptop0.system.coh_wrapper.l2.ctrls.monitor.watchdog_1[31:0]` |
| 8 | `non_gemmini_context` | 667985 | 333987 | `TestDriver.testHarness.chiptop0.system.chipyard_prcictrl_domain.clock_gater.monitor.watchdog[31:0]` |
| 9 | `non_gemmini_context` | 667985 | 333987 | `TestDriver.testHarness.chiptop0.system.cbus.coupler_to_plic.fragmenter.monitor.watchdog_1[31:0]` |
| 10 | `non_gemmini_context` | 667985 | 333987 | `TestDriver.testHarness.chiptop0.system.bank.ram.monitor.watchdog[31:0]` |

## Stage 1 Conclusion

The run completed normally and produced parseable RTL activity for the mvin/mvout data movement workload. This is accepted as the Stage 1 memory/control movement contrast because controller, load/store DMA, scratchpad, and other Gemmini datapath buckets are non-zero. Selected windows are documented in the Stage 1 window report. Interpret global whole-trace rankings only as SoC context, not as the Stage 2 implementation boundary.
