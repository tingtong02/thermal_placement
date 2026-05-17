# Phase1b r28 Gate SAIF Method Report

- status: `smoke-complete`
- generated at UTC: `2026-05-15T09:02:16.799183+00:00`
- gate netlist: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/Gemmini.routed.v`
- output root: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515`
- method: Verilator zero-delay Gemmini boundary replay with direct SAIF tracing
- compare: disabled for formal Phase1b
- timing: no SDF; not commercial gate simulation or timing signoff
- trace depth: `9`
- Verilator threads: `16`
- Verilator frontend jobs: `192`
- make jobs: `192`
- output split: `200`
- output split cfuncs: `20`
- output split ctrace: `20`

## Smoke

- workload: `mvin_mvout`
- SAIF: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/smoke_mvin_mvout_100cyc/mvin_mvout.gate.saif`
- trace cycles: `100`
- SAIF bytes: `445600062`
- Phase3 handoff: excluded

## Formal Handoff

## Phase3 Requirement

These SAIF files are rooted at the Verilated `Gemmini` top. Stage 3 must perform Cadence `read_saif` scope/instance mapping to the r28 physical design and report annotation coverage before using activity for power.

Historical old compare results under `phase1b_mvin_mvout_boundary_replay_20260513_t1_j64_split1k_cfunc50_clang_notiming_refcells_udp_full/` remain validation evidence only and are excluded from this handoff.
