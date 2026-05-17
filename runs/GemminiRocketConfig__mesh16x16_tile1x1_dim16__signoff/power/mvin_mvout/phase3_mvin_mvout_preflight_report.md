# Phase3 mvin_mvout Preflight Report

- status: `pass_with_warnings`
- generated at UTC: `2026-05-16T11:31:20.294083+00:00`
- workload: `mvin_mvout`
- output root: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout`
- non-signoff label: `PG-open / DRC-open / routed-SDF-waived thermal proxy; Phase1b SAIF is Verilator zero-delay activity`
- Cadence launched: `no`
- running Phase1b replays interrupted: `no`

## Accepted Input

- mainline mvin SAIF: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/gate_activity/phase1b_gate_saif_r28_20260515/mvin_mvout/mvin_mvout.gate.saif`
- SAIF bytes: `457660905`
- phase3 consumable: `True`
- replay return code: `0`
- trace enabled cycles: `267502`

## r28 Physical Handoff

- routed_def: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/Gemmini.routed.def` exists=`True` bytes=`508540521`
- routed_verilog: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/Gemmini.routed.v` exists=`True` bytes=`97095778`
- spef: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/Gemmini.routed.spef` exists=`True` bytes=`489835435`
- gds: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/Gemmini.gds` exists=`True` bytes=`556307892`
- cts_checkpoint: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/cts.enc` exists=`True` bytes=`772`
- routing_checkpoint: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/routing.enc` exists=`True` bytes=`790`
- export_checkpoint: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/data/export_routing.enc` exists=`True` bytes=`812`
- postroute_power_report: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/reports/postRoute_power.rpt` exists=`True` bytes=`41741`
- postroute_area_report: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/reports/postRoute_area.rpt` exists=`True` bytes=`61266`
- postroute_drc_report: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/reports/postRoute_drc.rpt` exists=`True` bytes=`105883`
- postroute_connectivity_report: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/reports/postRoute_connectivity.rpt` exists=`True` bytes=`77440`
- postroute_timing_report: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/reports/postRoute_timing/timing.rpt` exists=`True` bytes=`89199`
- routed_sdf_waiver: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/innovus/reports/routed_sdf_waiver.md` exists=`True` bytes=`950`

## Excluded Inputs

- smoke: saif_bytes=`None` summary_exists=`True` manifest_exists=`True` phase3_consumable=`False`
- mainline_tiled_matmul_ws: saif_bytes=`0` summary_exists=`False` manifest_exists=`False` phase3_consumable=`None`
- mainline_tiled_matmul_os: saif_bytes=`0` summary_exists=`False` manifest_exists=`False` phase3_consumable=`None`
- accelerated_mvin_mvout: saif_bytes=`0` summary_exists=`False` manifest_exists=`False` phase3_consumable=`None`
- accelerated_tiled_matmul_ws: saif_bytes=`0` summary_exists=`False` manifest_exists=`False` phase3_consumable=`None`
- accelerated_tiled_matmul_os: saif_bytes=`0` summary_exists=`False` manifest_exists=`False` phase3_consumable=`None`
- old_r2_compare_validation: historical r2 compare validation only; not a Phase3 activity handoff

## Warnings

- global Phase1b handoff manifest has no formal_workloads; using per-workload mvin_mvout manifest for preflight

## Expected Outputs

- preflight_manifest: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_preflight_manifest.json`
- preflight_report: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_preflight_report.md`
- activity_handoff_manifest: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_activity_handoff_manifest.json`
- cadence_power_dir: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/cadence`
- saif_annotation_coverage_report: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/reports/phase3_mvin_mvout_saif_annotation_coverage.rpt`
- instance_power_report: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/reports/phase3_mvin_mvout_instance_power.rpt`
- instance_to_grid_map: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_instance_to_grid_map.csv`
- grid_power_csv: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_grid_power.csv`
- transient_power_trace: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_transient_power_trace.csv`
- top_power_instances: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_top_power_instances.csv`
- region_power_summary: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_region_power_summary.csv`
- method_report: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/power/mvin_mvout/phase3_mvin_mvout_method_report.md`

## Next Step

Develop Cadence read_saif scope mapping and annotation coverage under the same output root.
