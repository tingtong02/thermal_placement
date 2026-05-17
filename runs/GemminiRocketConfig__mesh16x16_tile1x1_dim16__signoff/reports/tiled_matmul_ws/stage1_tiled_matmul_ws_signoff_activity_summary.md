# Stage 1 tiled_matmul_ws Activity Summary

## Scope

- stage: `1`
- workload: `tiled_matmul_ws`
- run_tag: `stage1_tiled_matmul_ws_signoff_20260429_r1`
- config: `GemminiRocketConfig`
- role: `weight-stationary GEMM dataflow contrast`
- dataflow_or_behavior: `weight-stationary via tiled_matmul_auto(..., WS)`
- input_shape: `MAT_DIM_I=64, MAT_DIM_K=64, MAT_DIM_J=64 in bare-metal tiled_matmul_ws.c`

## Functional Run

- sim_status: `0`
- verilator_finish_seen: `True`
- cpu_matmul_marker_seen: `True`
- gemmini_matmul_marker_seen: `True`
- failure_marker_seen: `False`
- cycles_line_1: `Cycles taken: 2279`
- cycles_line_2: `Cycles taken: 2967054`

## Artifacts

- binary: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/workloads/tiled_matmul_ws/tiled_matmul_ws-baremetal` (20.06 KiB)
- stdout log: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/tiled_matmul_ws/logs/tiled_matmul_ws-baremetal.stage1_tiled_matmul_ws_signoff_20260429_r1.log` (542.00 B)
- disassembly/out log: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/tiled_matmul_ws/logs/tiled_matmul_ws-baremetal.stage1_tiled_matmul_ws_signoff_20260429_r1.out` (338.63 MiB)
- waveform: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/tiled_matmul_ws/waves/tiled_matmul_ws-baremetal.stage1_tiled_matmul_ws_signoff_20260429_r1.vcd` (42.42 GiB)
- signal activity CSV: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_ws/stage1_tiled_matmul_ws_signoff_20260429_r1_signal_activity.csv` (7.22 MiB)
- region activity CSV: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_ws/stage1_tiled_matmul_ws_signoff_20260429_r1_region_activity.csv` (973.00 B)
- window CSV: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_ws/stage1_tiled_matmul_ws_signoff_20260429_r1_window_activity.csv` (564.00 B)
- window report: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/tiled_matmul_ws/stage1_tiled_matmul_ws_signoff_windows.md`

## Activity Parse

- parsed_time_steps: `21447935`
- last_time_ps: `10723925500`
- total_region_toggles: `4119793535`
- gemmini_target_region_toggles: `160061464`
- gemmini_target_region_toggle_share: `3.885182%`

## Region Activity

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

## Research Boundary Check

- The Stage 1 trace is a full `GemminiRocketConfig` SoC/TestHarness waveform, so whole-trace top toggles are expected to include Rocket core, cache, and TileLink context.
- For the active research target, the relevant check is whether Gemmini PE/control/datapath buckets required for this workload are non-zero and internally plausible.
- PE array: `signals=6558` `toggles=2191819`
- Gemmini controller: `signals=142` `toggles=37829875`
- Load/store DMA: `signals=393` `toggles=14998`
- Scratchpad-side datapath/context: `signals=6837` `toggles=109144543`
- Other Gemmini datapath/control: `signals=3939` `toggles=10880229`
- `accumulator` remains zero in the current bucket summary, which is acceptable for this stage because memory arrays are not the detailed thermal target in the active plan.

## Targeted Gemmini Region Highlights

### PE array

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 2070 | 1294 | `...testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh_cntl_signals_q.enq_ptr_value[2:0]` |
| 2 | 2070 | 1294 | `...testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh_cntl_signals_q.deq_ptr_value[2:0]` |
| 3 | 1960 | 1045 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh.fire_counter[3:0]` |
| 4 | 1921 | 879 | `...river.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh.io_resp_bits_data_1_0[19:0]` |
| 5 | 1910 | 878 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh.RegShifted_r_656_0[19:0]` |

### Gemmini controller

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 1925 | 132 | `...Driver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.cmd_q.io_enq_bits_cmd_rs2[63:0]` |
| 2 | 1887 | 135 | `...Driver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.cmd_q.io_enq_bits_cmd_rs1[63:0]` |
| 3 | 838 | 24 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.mod.cmd_q.ram_ext.W0_data[273:0]` |
| 4 | 824 | 24 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.mod.cmd_q.ram_ext.R0_data[273:0]` |
| 5 | 808 | 24 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.mod_1.cmd_q.ram_ext.W0_data[273:0]` |

### Load/store DMA

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 1071 | 16 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.load_controller.cmd_q.ram_ext.R0_data[245:0]` |
| 2 | 1024 | 256 | `...ver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.load_controller.io_dma_resp_bits_bytesRead[15:0]` |
| 3 | 768 | 256 | `...op0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.load_controller.cmd_tracker.io_request_returned_bits_bytes_read[10:0]` |
| 4 | 660 | 11 | `...Driver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.store_controller.cmd_q.ram_ext.R0_data[273:0]` |
| 5 | 640 | 256 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.load_controller.io_dma_resp_bits_cmd_id[7:0]` |

### Scratchpad-side datapath/context

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 32187 | 1042 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.acc_mems_0.mem.mem.W0_data[511:0]` |
| 2 | 31684 | 1027 | `...ver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.norm_unit_passthru_q.ram_ext.W0_data[549:0]` |
| 3 | 31360 | 1025 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.acc_mems_0.mem.mem.R0_data[511:0]` |
| 4 | 28905 | 546 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.vsm_in_q_1.ram_ext.W0_data[624:0]` |
| 5 | 25405 | 770 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.acc_mems_1.mem.mem.W0_data[511:0]` |

### Other Gemmini datapath/control

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 10723140 | 5361572 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.reservation_station.cntr_value[20:0]` |
| 2 | 9088 | 1048 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.dataA_unpadded[127:0]` |
| 3 | 7675 | 278 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.unrolled_cmd_q.ram_ext.W0_data[273:0]` |
| 4 | 5212 | 265 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.unrolled_cmd_q.ram_ext.R0_data[273:0]` |
| 5 | 4004 | 2006 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.pipeline_stall_counter[31:0]` |

## Global Top Toggle Signals (Full Trace Context)

| rank | region | toggles | changes | signal |
| ---: | --- | ---: | ---: | --- |
| 1 | `tl_soc_glue` | 42669619 | 2154763 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_4[31:0]` |
| 2 | `tl_soc_glue` | 37996860 | 2165485 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_5[31:0]` |
| 3 | `controller` | 37813467 | 2370291 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.cmdRouter.cmd_q.ram_ext.W0_data[264:0]` |
| 4 | `tl_soc_glue` | 37489707 | 2154702 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_1[31:0]` |
| 5 | `tl_soc_glue` | 36736737 | 2154680 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_7[31:0]` |
| 6 | `tl_soc_glue` | 36313743 | 2154693 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_6[31:0]` |
| 7 | `tl_soc_glue` | 36227576 | 2154883 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_2[31:0]` |
| 8 | `tl_soc_glue` | 35517624 | 2154927 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_0[31:0]` |
| 9 | `tl_soc_glue` | 32115966 | 569917 | `....testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.dcache.data.rockettile_dcache_data_arrays_0.RW0_wmask[63:0]` |
| 10 | `non_gemmini_context` | 30111093 | 2417687 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.core.ibuf.io_inst_0_bits_raw[31:0]` |

## Stage 1 Conclusion

The run reached the Gemmini tiled matmul section and produced parseable RTL activity data. This is accepted for Stage 1 because Gemmini PE/control/datapath buckets required for the GEMM workload are non-zero. Selected windows are documented in the Stage 1 window report. Interpret global whole-trace rankings only as SoC context, not as the Stage 2 implementation boundary.
