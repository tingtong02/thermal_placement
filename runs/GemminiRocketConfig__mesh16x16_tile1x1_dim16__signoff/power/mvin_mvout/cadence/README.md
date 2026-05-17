# Phase3 mvin_mvout Cadence Script-Only Plan

Generated: 2026-05-16T11:42:45.689567+00:00

This directory contains generated Cadence collateral for the user-confirmed single-workload `mvin_mvout` Phase3 bring-up. It has not launched Innovus.

Quality labels:

- NON-SIGNOFF downstream result.
- Stage2 r28 input is `PG-open / DRC-open / routed-SDF-waived thermal proxy`.
- Phase1b SAIF input is Verilator zero-delay activity, not SDF timing simulation and not commercial gate simulation.

Key input decisions:

- SAIF: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/mvin_mvout/mvin_mvout.gate.saif`
- SAIF root scope detected from file: `TOP`
- Cadence activity command: `read_activity_file -format SAIF -scope TOP`
- Checkpoint restore input: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/export_routing.enc.dat`

Generated files:

- `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/scripts/phase3_mvin_mvout_read_activity_power.tcl`
- `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/scripts/run_phase3_mvin_mvout_innovus_no_gui.sh`
- `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence/phase3_mvin_mvout_cadence_script_manifest.json`

The runner is intentionally generated but not executed. Before using reports for grid or thermal work, inspect the activity summary and unannotated-net reports produced by the Tcl.
