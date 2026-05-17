# Stage 1 Target-Scoped Window Refinement For Stage 3

## Inputs

- workload: `stage1_tiled_matmul_os_baseline_20260423`
- source_vcd: `sim/waves/GemminiRocketConfig/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_baseline_20260423.vcd`
- candidate_window_ps: `0` to `1030328550`
- workers: `1`
- target_signal_count_from_header: `17812`

## Refined Window

- refined_start_ps: `0`
- refined_end_ps: `128791068`
- active_target_signal_count: `9455`
- time_steps_seen_in_candidate: `4014`
- active_bin_threshold_toggles: `17093`
- max_bin_toggles: `341873`

## Region Toggle Summary

| region | active_signals | toggles | value_changes |
| --- | ---: | ---: | ---: |
| `pe_array` | 5799 | 272826 | 46452 |
| `scratchpad` | 2811 | 60765 | 10158 |
| `gemmini_other` | 671 | 6608 | 1334 |
| `controller` | 47 | 901 | 47 |
| `load_store_dma` | 127 | 773 | 127 |

## Top Target Signals

| rank | region | toggles | changes | signal |
| ---: | --- | ---: | ---: | --- |
| 1 | `scratchpad` | 1801 | 7 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.writer.io_req_bits_data[511:0]` |
| 2 | `scratchpad` | 1544 | 6 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.fullAccWriteData[511:0]` |
| 3 | `scratchpad` | 1269 | 32 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.io_srams_write_0_data[127:0]` |
| 4 | `scratchpad` | 1195 | 591 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_1.monitor.watchdog[31:0]` |
| 5 | `scratchpad` | 1193 | 591 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.xbar.monitor_1.watchdog_1[31:0]` |
| 6 | `scratchpad` | 1192 | 591 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.xbar.monitor.watchdog_1[31:0]` |
| 7 | `scratchpad` | 1191 | 591 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_2.monitor.watchdog[31:0]` |
| 8 | `scratchpad` | 1191 | 591 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.xbar.monitor.watchdog[31:0]` |
| 9 | `scratchpad` | 1190 | 591 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer.monitor.watchdog[31:0]` |
| 10 | `scratchpad` | 1190 | 591 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.xbar.monitor_1.watchdog[31:0]` |
| 11 | `scratchpad` | 1189 | 591 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_2.monitor.watchdog_1[31:0]` |
| 12 | `gemmini_other` | 1187 | 591 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.reservation_station.cntr_value[20:0]` |
| 13 | `scratchpad` | 1187 | 591 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_1.monitor.watchdog_1[31:0]` |
| 14 | `scratchpad` | 1186 | 591 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer.monitor.watchdog_1[31:0]` |
| 15 | `scratchpad` | 521 | 2 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.acc_mems_0.mem.mem.W0_data[511:0]` |
| 16 | `scratchpad` | 511 | 31 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.io_acc_write_0_bits_data_1_0[31:0]` |
| 17 | `scratchpad` | 480 | 29 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.io_acc_write_0_bits_data_0_0[31:0]` |
| 18 | `scratchpad` | 480 | 28 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.io_acc_write_0_bits_data_7_0[31:0]` |
| 19 | `scratchpad` | 417 | 26 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.io_acc_write_0_bits_data_13_0[31:0]` |
| 20 | `scratchpad` | 401 | 27 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.io_acc_write_0_bits_data_5_0[31:0]` |

## Bin Totals

| bin | start_ps | end_ps | total_target_toggles | pe_array | controller | scratchpad | load_store_dma | gemmini_other |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 128791068 | 341873 | 272826 | 901 | 60765 | 773 | 6608 |
| 1 | 128791068 | 257582137 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2 | 257582137 | 386373206 | 0 | 0 | 0 | 0 | 0 | 0 |
| 3 | 386373206 | 515164275 | 0 | 0 | 0 | 0 | 0 | 0 |
| 4 | 515164275 | 643955343 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5 | 643955343 | 772746412 | 0 | 0 | 0 | 0 | 0 | 0 |
| 6 | 772746412 | 901537481 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | 901537481 | 1030328550 | 0 | 0 | 0 | 0 | 0 | 0 |

## Method Note

This refinement scans the full-SoC VCD source but counts only Gemmini target scopes in the coarse steady_high_load candidate interval. It is target-scoped RTL activity for the Stage 3 proxy power model, not gate-level SAIF signoff activity.
