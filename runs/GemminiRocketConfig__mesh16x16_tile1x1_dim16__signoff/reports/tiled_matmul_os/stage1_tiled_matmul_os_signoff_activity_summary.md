# Stage 1 tiled_matmul_os Activity Summary

## Scope

- stage: `1`
- workload: `tiled_matmul_os`
- run_tag: `stage1_tiled_matmul_os_signoff_20260429_r1`
- config: `GemminiRocketConfig`
- role: `output-stationary GEMM compute baseline`
- dataflow_or_behavior: `output-stationary via tiled_matmul_auto(..., OS)`
- input_shape: `MAT_DIM_I=64, MAT_DIM_K=64, MAT_DIM_J=64 in bare-metal tiled_matmul_os.c`

## Functional Run

- sim_status: `0`
- verilator_finish_seen: `True`
- cpu_matmul_marker_seen: `True`
- gemmini_matmul_marker_seen: `True`
- failure_marker_seen: `False`
- cycles_line_1: `Cycles taken: 2967084`
- cycles_line_2: `Cycles taken: 3779`

## Artifacts

- binary: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/workloads/tiled_matmul_os/tiled_matmul_os-baremetal` (19.87 KiB)
- stdout log: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/tiled_matmul_os/logs/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_signoff_20260429_r1.log` (501.00 B)
- disassembly/out log: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/tiled_matmul_os/logs/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_signoff_20260429_r1.out` (327.30 MiB)
- waveform: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/tiled_matmul_os/waves/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_signoff_20260429_r1.vcd` (40.93 GiB)
- signal activity CSV: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_os/stage1_tiled_matmul_os_signoff_20260429_r1_signal_activity.csv` (7.21 MiB)
- region activity CSV: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_os/stage1_tiled_matmul_os_signoff_20260429_r1_region_activity.csv` (976.00 B)
- window CSV: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/activity/tiled_matmul_os/stage1_tiled_matmul_os_signoff_20260429_r1_window_activity.csv` (554.00 B)
- window report: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/reports/tiled_matmul_os/stage1_tiled_matmul_os_signoff_windows.md`

## Activity Parse

- parsed_time_steps: `20606655`
- last_time_ps: `10303285500`
- total_region_toggles: `3980952281`
- gemmini_target_region_toggles: `154545102`
- gemmini_target_region_toggle_share: `3.882114%`

## Region Activity

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

## Research Boundary Check

- The Stage 1 trace is a full `GemminiRocketConfig` SoC/TestHarness waveform, so whole-trace top toggles are expected to include Rocket core, cache, and TileLink context.
- For the active research target, the relevant check is whether Gemmini PE/control/datapath buckets required for this workload are non-zero and internally plausible.
- PE array: `signals=6558` `toggles=2390594`
- Gemmini controller: `signals=142` `toggles=37074715`
- Load/store DMA: `signals=393` `toggles=20424`
- Scratchpad-side datapath/context: `signals=6837` `toggles=104515396`
- Other Gemmini datapath/control: `signals=3939` `toggles=10543973`
- `accumulator` remains zero in the current bucket summary, which is acceptable for this stage because memory arrays are not the detailed thermal target in the active plan.

## Targeted Gemmini Region Highlights

### PE array

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 3874 | 2065 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh.fire_counter[3:0]` |
| 2 | 3873 | 2065 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh.transposer.counter[3:0]` |
| 3 | 2715 | 1697 | `...testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh_cntl_signals_q.enq_ptr_value[2:0]` |
| 4 | 2715 | 1697 | `...testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh_cntl_signals_q.deq_ptr_value[2:0]` |
| 5 | 1994 | 353 | `...tHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.mesh_cntl_signals_q.ram_ext.W0_data[87:0]` |

### Gemmini controller

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 9222 | 289 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.mod.cmd_q.ram_ext.W0_data[273:0]` |
| 2 | 9212 | 289 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.mod.cmd_q.ram_ext.R0_data[273:0]` |
| 3 | 9196 | 289 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.mod_1.cmd_q.ram_ext.W0_data[273:0]` |
| 4 | 9074 | 288 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.mod_1.cmd_q.ram_ext.R0_data[273:0]` |
| 5 | 4373 | 258 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.mod.cmd_q.io_deq_bits_cmd_rs1[63:0]` |

### Load/store DMA

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 1718 | 34 | `...Driver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.store_controller.cmd_q.ram_ext.W0_data[273:0]` |
| 2 | 1449 | 22 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.load_controller.cmd_q.ram_ext.R0_data[245:0]` |
| 3 | 1024 | 256 | `...ver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.load_controller.io_dma_resp_bits_bytesRead[15:0]` |
| 4 | 882 | 26 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.load_controller.cmd_q.ram_ext.W0_data[245:0]` |
| 5 | 768 | 256 | `...op0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.load_controller.cmd_tracker.io_request_returned_bits_bytes_read[10:0]` |

### Scratchpad-side datapath/context

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 27515 | 518 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.vsm_in_q_1.ram_ext.W0_data[624:0]` |
| 2 | 20906 | 533 | `...ver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_2.nodeOut_a_q.ram_ext.W0_data[191:0]` |
| 3 | 13796 | 494 | `...ver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_2.nodeOut_a_q.ram_ext.R0_data[191:0]` |
| 4 | 13762 | 518 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.reader.io_resp_bits_data[511:0]` |
| 5 | 13176 | 337 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.io_srams_write_0_data[127:0]` |

### Other Gemmini datapath/control

| rank | toggles | changes | signal |
| ---: | ---: | ---: | --- |
| 1 | 10302502 | 5151252 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.reservation_station.cntr_value[20:0]` |
| 2 | 9282 | 1079 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.ex_controller.dataA_unpadded[127:0]` |
| 3 | 9153 | 289 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.unrolled_cmd_q.ram_ext.W0_data[273:0]` |
| 4 | 9045 | 288 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.raw_cmd_q.ram_ext.W0_data[273:0]` |
| 5 | 9004 | 285 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.unrolled_cmd_q.ram_ext.R0_data[273:0]` |

## Global Top Toggle Signals (Full Trace Context)

| rank | region | toggles | changes | signal |
| ---: | --- | ---: | ---: | --- |
| 1 | `tl_soc_glue` | 41208870 | 2066147 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_4[31:0]` |
| 2 | `controller` | 36971881 | 2292853 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.cmdRouter.cmd_q.ram_ext.W0_data[264:0]` |
| 3 | `tl_soc_glue` | 36485360 | 2066223 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_5[31:0]` |
| 4 | `tl_soc_glue` | 36150842 | 2075808 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_1[31:0]` |
| 5 | `tl_soc_glue` | 35244441 | 2066123 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_7[31:0]` |
| 6 | `tl_soc_glue` | 34810966 | 2066194 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_6[31:0]` |
| 7 | `tl_soc_glue` | 34655895 | 2070863 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_3[31:0]` |
| 8 | `tl_soc_glue` | 34192942 | 2066319 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.frontend.icache.s2_dout_0[31:0]` |
| 9 | `tl_soc_glue` | 32099242 | 569589 | `....testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.dcache.data.rockettile_dcache_data_arrays_0.RW0_wmask[63:0]` |
| 10 | `non_gemmini_context` | 29156652 | 2344543 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.core.ibuf.io_inst_0_bits_raw[31:0]` |

## Stage 1 Conclusion

The run reached the Gemmini tiled matmul section and produced parseable RTL activity data. This is accepted for Stage 1 because Gemmini PE/control/datapath buckets required for the GEMM workload are non-zero. Selected windows are documented in the Stage 1 window report. Interpret global whole-trace rankings only as SoC context, not as the Stage 2 implementation boundary.
