# Stage 1 Target-Scoped Window Refinement For Stage 3

## Inputs

- workload: `stage1_tiled_matmul_os_baseline_20260423`
- source_vcd: `sim/waves/GemminiRocketConfig/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_baseline_20260423.vcd`
- candidate_window_ps: `9272956950` to `10303285500`
- workers: `16`
- target_signal_count_from_header: `17502`

## Refined Window

- refined_start_ps: `10222791082`
- refined_end_ps: `10238889965`
- active_target_signal_count: `8888`
- time_steps_seen_in_candidate: `2060658`
- active_bin_threshold_toggles: `190231`
- max_bin_toggles: `3804629`

## Region Toggle Summary

| region | active_signals | toggles | value_changes |
| --- | ---: | ---: | ---: |
| `pe_array` | 5698 | 2080970 | 1465281 |
| `scratchpad` | 2350 | 1377625 | 454130 |
| `gemmini_other` | 550 | 1258688 | 588902 |
| `controller` | 78 | 84347 | 11186 |
| `load_store_dma` | 212 | 17226 | 6222 |

## Top Target Signals

| rank | region | toggles | changes | signal |
| ---: | --- | ---: | ---: | --- |
| 1 | `gemmini_other` | 1030328 | 515162 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.reservation_station.cntr_value[20:0]` |
| 2 | `scratchpad` | 27283 | 517 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.vsm_in_q_1.ram_ext.W0_data[624:0]` |
| 3 | `scratchpad` | 20881 | 532 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_2.nodeOut_a_q.ram_ext.W0_data[191:0]` |
| 4 | `scratchpad` | 13618 | 492 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_2.nodeOut_a_q.ram_ext.R0_data[191:0]` |
| 5 | `scratchpad` | 13556 | 517 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.reader.io_resp_bits_data[511:0]` |
| 6 | `scratchpad` | 12823 | 307 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_1.nodeOut_a_q.ram_ext.R0_data[190:0]` |
| 7 | `scratchpad` | 11872 | 307 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.writer.tlb_arb.io_in_2_bits_tl_a_data[127:0]` |
| 8 | `scratchpad` | 11872 | 307 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.writer.tlb_arb.io_out_bits_tl_a_data[127:0]` |
| 9 | `scratchpad` | 11872 | 307 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_2.auto_in_a_bits_data[127:0]` |
| 10 | `scratchpad` | 11856 | 304 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.io_srams_write_0_data[127:0]` |
| 11 | `scratchpad` | 11562 | 308 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.auto_spad_id_out_a_bits_data[127:0]` |
| 12 | `scratchpad` | 11518 | 307 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_1.auto_out_a_bits_data[127:0]` |
| 13 | `scratchpad` | 10651 | 255 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.writer.tlb_q.ram[335:0]` |
| 14 | `scratchpad` | 10651 | 255 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.buffer_1.nodeOut_a_q.ram_ext.W0_data[190:0]` |
| 15 | `scratchpad` | 10651 | 255 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.writer.translate_q.ram[335:0]` |
| 16 | `scratchpad` | 10248 | 271 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.acc_mems_0.mem.mem.W0_data[511:0]` |
| 17 | `scratchpad` | 9752 | 259 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.norm_unit_passthru_q.ram_ext.R0_data[549:0]` |
| 18 | `scratchpad` | 9681 | 256 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.writer.io_req_bits_data[511:0]` |
| 19 | `scratchpad` | 9669 | 256 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.norm_unit_passthru_q.ram_ext.W0_data[549:0]` |
| 20 | `scratchpad` | 9659 | 256 | `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini.spad.acc_mems_0.mem.mem.R0_data[511:0]` |

## Bin Totals

| bin | start_ps | end_ps | total_target_toggles | pe_array | controller | scratchpad | load_store_dma | gemmini_other |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 9272956950 | 9289055833 | 16102 | 0 | 0 | 0 | 0 | 16102 |
| 1 | 9289055833 | 9305154717 | 16091 | 0 | 0 | 0 | 0 | 16091 |
| 2 | 9305154717 | 9321253600 | 16104 | 0 | 0 | 0 | 0 | 16104 |
| 3 | 9321253600 | 9337352484 | 16096 | 0 | 0 | 0 | 0 | 16096 |
| 4 | 9337352484 | 9353451367 | 16099 | 0 | 0 | 0 | 0 | 16099 |
| 5 | 9353451367 | 9369550251 | 16097 | 0 | 0 | 0 | 0 | 16097 |
| 6 | 9369550251 | 9385649135 | 16104 | 0 | 0 | 0 | 0 | 16104 |
| 7 | 9385649135 | 9401748018 | 16099 | 0 | 0 | 0 | 0 | 16099 |
| 8 | 9401748018 | 9417846902 | 16092 | 0 | 0 | 0 | 0 | 16092 |
| 9 | 9417846902 | 9433945785 | 16101 | 0 | 0 | 0 | 0 | 16101 |
| 10 | 9433945785 | 9450044669 | 16100 | 0 | 0 | 0 | 0 | 16100 |
| 11 | 9450044669 | 9466143553 | 16102 | 0 | 0 | 0 | 0 | 16102 |
| 12 | 9466143553 | 9482242436 | 16094 | 0 | 0 | 0 | 0 | 16094 |
| 13 | 9482242436 | 9498341320 | 16099 | 0 | 0 | 0 | 0 | 16099 |
| 14 | 9498341320 | 9514440203 | 16101 | 0 | 0 | 0 | 0 | 16101 |
| 15 | 9514440203 | 9530539087 | 16097 | 0 | 0 | 0 | 0 | 16097 |
| 16 | 9530539087 | 9546637971 | 16097 | 0 | 0 | 0 | 0 | 16097 |
| 17 | 9546637971 | 9562736854 | 16101 | 0 | 0 | 0 | 0 | 16101 |
| 18 | 9562736854 | 9578835738 | 16105 | 0 | 0 | 0 | 0 | 16105 |
| 19 | 9578835738 | 9594934621 | 16095 | 0 | 0 | 0 | 0 | 16095 |
| 20 | 9594934621 | 9611033505 | 16102 | 0 | 0 | 0 | 0 | 16102 |
| 21 | 9611033505 | 9627132389 | 16095 | 0 | 0 | 0 | 0 | 16095 |
| 22 | 9627132389 | 9643231272 | 16100 | 0 | 0 | 0 | 0 | 16100 |
| 23 | 9643231272 | 9659330156 | 16097 | 0 | 0 | 0 | 0 | 16097 |
| 24 | 9659330156 | 9675429039 | 16100 | 0 | 0 | 0 | 0 | 16100 |
| 25 | 9675429039 | 9691527923 | 16098 | 0 | 0 | 0 | 0 | 16098 |
| 26 | 9691527923 | 9707626807 | 16099 | 0 | 0 | 0 | 0 | 16099 |
| 27 | 9707626807 | 9723725690 | 16099 | 0 | 0 | 0 | 0 | 16099 |
| 28 | 9723725690 | 9739824574 | 16102 | 0 | 0 | 0 | 0 | 16102 |
| 29 | 9739824574 | 9755923457 | 16100 | 0 | 0 | 0 | 0 | 16100 |
| 30 | 9755923457 | 9772022341 | 16094 | 0 | 0 | 0 | 0 | 16094 |
| 31 | 9772022341 | 9788121225 | 16100 | 0 | 0 | 0 | 0 | 16100 |
| 32 | 9788121225 | 9804220108 | 16094 | 0 | 0 | 0 | 0 | 16094 |
| 33 | 9804220108 | 9820318992 | 16096 | 0 | 0 | 0 | 0 | 16096 |
| 34 | 9820318992 | 9836417875 | 16104 | 0 | 0 | 0 | 0 | 16104 |
| 35 | 9836417875 | 9852516759 | 16098 | 0 | 0 | 0 | 0 | 16098 |
| 36 | 9852516759 | 9868615642 | 16101 | 0 | 0 | 0 | 0 | 16101 |
| 37 | 9868615642 | 9884714526 | 16092 | 0 | 0 | 0 | 0 | 16092 |
| 38 | 9884714526 | 9900813410 | 16096 | 0 | 0 | 0 | 0 | 16096 |
| 39 | 9900813410 | 9916912293 | 16104 | 0 | 0 | 0 | 0 | 16104 |
| 40 | 9916912293 | 9933011177 | 16098 | 0 | 0 | 0 | 0 | 16098 |
| 41 | 9933011177 | 9949110060 | 16098 | 0 | 0 | 0 | 0 | 16098 |
| 42 | 9949110060 | 9965208944 | 16099 | 0 | 0 | 0 | 0 | 16099 |
| 43 | 9965208944 | 9981307828 | 16101 | 0 | 0 | 0 | 0 | 16101 |
| 44 | 9981307828 | 9997406711 | 16095 | 0 | 0 | 0 | 0 | 16095 |
| 45 | 9997406711 | 10013505595 | 16102 | 0 | 0 | 0 | 0 | 16102 |
| 46 | 10013505595 | 10029604478 | 16098 | 0 | 0 | 0 | 0 | 16098 |
| 47 | 10029604478 | 10045703362 | 16098 | 0 | 0 | 0 | 0 | 16098 |
| 48 | 10045703362 | 10061802246 | 16098 | 0 | 0 | 0 | 0 | 16098 |
| 49 | 10061802246 | 10077901129 | 16099 | 0 | 0 | 0 | 0 | 16099 |
| 50 | 10077901129 | 10094000013 | 16102 | 0 | 0 | 0 | 0 | 16102 |
| 51 | 10094000013 | 10110098896 | 16101 | 0 | 0 | 0 | 0 | 16101 |
| 52 | 10110098896 | 10126197780 | 16098 | 0 | 0 | 0 | 0 | 16098 |
| 53 | 10126197780 | 10142296664 | 16100 | 0 | 0 | 0 | 0 | 16100 |
| 54 | 10142296664 | 10158395547 | 16099 | 0 | 0 | 0 | 0 | 16099 |
| 55 | 10158395547 | 10174494431 | 16098 | 0 | 0 | 0 | 0 | 16098 |
| 56 | 10174494431 | 10190593314 | 16098 | 0 | 0 | 0 | 0 | 16098 |
| 57 | 10190593314 | 10206692198 | 16100 | 0 | 0 | 0 | 0 | 16100 |
| 58 | 10206692198 | 10222791082 | 16097 | 0 | 0 | 0 | 0 | 16097 |
| 59 | 10222791082 | 10238889965 | 3804629 | 2080970 | 84347 | 1377625 | 17226 | 244461 |
| 60 | 10238889965 | 10254988849 | 16096 | 0 | 0 | 0 | 0 | 16096 |
| 61 | 10254988849 | 10271087732 | 16104 | 0 | 0 | 0 | 0 | 16104 |
| 62 | 10271087732 | 10287186616 | 16096 | 0 | 0 | 0 | 0 | 16096 |
| 63 | 10287186616 | 10303285500 | 16101 | 0 | 0 | 0 | 0 | 16101 |

## Method Note

This refinement scans the full-SoC VCD source but counts only Gemmini target scopes in the coarse steady_high_load candidate interval. It is target-scoped RTL activity for the Stage 3 proxy power model, not gate-level SAIF signoff activity.
