# Phase1b Boundary Vector Extraction

- workload: `tiled_matmul_os`
- RTL VCD: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/tiled_matmul_os/waves/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_signoff_20260429_r1.vcd`
- gate netlist: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/Gemmini.routed.v`
- RTL scope: `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini`
- cycles written: `5151643`
- output: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/tiled_matmul_os/boundary_vectors.csv`
- vectors inputs only: `True`
- vector ports: `138`
- unmatched ports: `0`
- unknown-bearing ports: `0`

Sampling note: vectors are sampled on RTL VCD clock posedges after processing timestamp updates. The formal SAIF replay harness applies the previous sampled input vector before the next rising edge. The historical compare harness also compares against the current sampled output vector when output columns are present.
