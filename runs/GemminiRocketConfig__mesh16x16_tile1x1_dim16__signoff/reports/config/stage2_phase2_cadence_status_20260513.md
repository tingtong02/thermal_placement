# Stage 2 Cadence ASAP7 Status - 2026-05-13/14

## Status

Stage 2 is complete for the current research target only as a degraded handoff:

```text
PG-open / DRC-open / routed-SDF-waived thermal proxy
```

This is not PG-clean, DRC-clean, routed-SDF-complete, timing-signoff, IR/EM-clean, LVS-clean, or foundry/signoff-clean.

## Accepted Run

- Accepted degraded export: `physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/`
- CTS source: `physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260512_r17_pgopen_resume_floorplan/innovus/data/cts.enc`
- Routed source: `physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r20_route_from_cts_single_droute8/innovus/data/routing.enc`

## Acceptance Manifest

```text
physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/startup/innovus_export_from_routing_manifest.json
```

Result:

```text
ok: true
missing: []
```

## Artifacts Present

- `innovus/data/export_routing.enc`
- `innovus/data/routing.enc`
- `innovus/data/cts.enc`
- `innovus/data/Gemmini.routed.def`
- `innovus/data/Gemmini.routed.v`
- `innovus/data/Gemmini.routed.spef`
- `innovus/data/Gemmini.gds`
- `innovus/reports/routed_sdf_waiver.md`
- `innovus/reports/postRoute_timing/`
- `innovus/reports/postRoute_area.rpt`
- `innovus/reports/postRoute_power.rpt`
- `innovus/reports/postRoute_drc.rpt`
- `innovus/reports/postRoute_connectivity.rpt`

## Key Evidence

- r20 detailed route used `TP_STAGE2_DROUTE_END_ITERATION=8` and saved `routing.enc` after `routeDesign`.
- r20 post-route timing reported setup WNS 0.067 ns and TNS 0.000 ns at 5.000 ns / 200 MHz.
- r28 exported routed DEF, routed Verilog, SPEF, GDS, DRC/connectivity reports, waiver report, and `export_routing.enc` from r20 without rerunning route.
- r28 DRC remains open: `verify_drc` hit the 1000 violation report limit.
- r28 connectivity remains open: 158 special-wire connectivity problems and 842 dangling-wire problems were reported before hitting the 1000 issue limit.
- GDS streamout warned that fake SRAM masters `mem_0_ext` and `mem_ext` are not present in merged stdcell GDS collateral.

## Routed SDF Waiver

Innovus `write_sdf` crashes internally during delay calculation on the routed fake-SRAM Gemmini database. Failed modes include normal routed SDF, `-interconn none -base_delay -view setup_view`, and `-celltiming none -interconn none -view setup_view`. The 2026-05-13 user decision waived routed SDF for this research target. r28 records the waiver in `innovus/reports/routed_sdf_waiver.md`.

## Downstream Use

Stage 3/4 may consume r28 only as Cadence/full-ASAP7 thermal-proxy evidence. Downstream conclusions must be limited to placement/activity/power-driven thermal trends and must retain the `PG-open / DRC-open / routed-SDF-waived` label.
