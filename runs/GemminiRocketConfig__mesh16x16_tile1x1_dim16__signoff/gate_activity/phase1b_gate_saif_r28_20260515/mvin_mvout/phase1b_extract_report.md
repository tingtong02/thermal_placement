# Phase1b Boundary Vector Extraction

- workload: `mvin_mvout`
- RTL VCD: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/sim/mvin_mvout/waves/mvin_mvout-baremetal.stage1_mvin_mvout_signoff_20260429_r1.vcd`
- gate netlist: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/Gemmini.routed.v`
- RTL scope: `TestDriver.testHarness.chiptop0.system.tile_prci_domain.element_reset_domain_rockettile.gemmini`
- cycles written: `300940`
- output: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/mvin_mvout/boundary_vectors.csv`
- vectors inputs only: `True`
- vector ports: `138`
- unmatched ports: `0`
- unknown-bearing ports: `0`

Sampling note: vectors are sampled on RTL VCD clock posedges after processing timestamp updates. The formal SAIF replay harness applies the previous sampled input vector before the next rising edge. The historical compare harness also compares against the current sampled output vector when output columns are present.
