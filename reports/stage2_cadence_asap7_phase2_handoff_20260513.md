# Stage 2 Cadence ASAP7 Phase2 Handoff - 2026-05-13

## Status

Stage 2 is complete for the current research target only as a degraded Cadence/full-ASAP7 thermal-proxy handoff:

```text
PG-open / DRC-open / routed-SDF-waived thermal proxy
```

This is not PG-clean, DRC-clean, routed-SDF-complete, timing-signoff, IR/EM-clean, LVS-clean, or foundry/signoff-clean.

## Selected Run

Accepted degraded export run and artifact folder:

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/
```

Do not delete or rename this folder because its parent path contains `__signoff`; that suffix is a historical path label from before the current downgrade, not a current quality claim.

Source checkpoints:

- CTS source: `.../physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260512_r17_pgopen_resume_floorplan/innovus/data/cts.enc`
- Routed source: `.../physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r20_route_from_cts_single_droute8/innovus/data/routing.enc`
- Export checkpoint: `.../r28_export_from_routing_sdf_waived/innovus/data/export_routing.enc`

## Flow Source

Nested `runs/cadence_startup` source commit for the SDF-waiver gate repair:

```text
14741e1 Accept routed SDF waiver in stage2 gates
```

## Artifact Gate

Authoritative acceptance manifest:

```text
.../r28_export_from_routing_sdf_waived/startup/innovus_export_from_routing_manifest.json
```

Gate result:

```text
ok: true
missing: []
```

Required artifacts present:

- `innovus/data/Gemmini.routed.def` - 508,540,521 bytes
- `innovus/data/Gemmini.routed.v` - 97,095,778 bytes
- `innovus/data/Gemmini.routed.spef` - 489,835,435 bytes
- `innovus/data/Gemmini.gds` - 556,307,892 bytes
- `innovus/data/routing.enc`
- `innovus/data/cts.enc`
- `innovus/data/export_routing.enc`
- `innovus/reports/postRoute_timing/`
- `innovus/reports/postRoute_area.rpt`
- `innovus/reports/postRoute_power.rpt`
- `innovus/reports/postRoute_drc.rpt`
- `innovus/reports/postRoute_connectivity.rpt`
- `innovus/reports/routed_sdf_waiver.md`

## Timing Evidence

The post-route timing report was copied from the r20 routed checkpoint. r20 reported setup WNS 0.067 ns and TNS 0.000 ns at 5.000 ns / 200 MHz. This is static timing evidence only; it is not SDF timing simulation.

## Known Limitations

- Routed SDF is intentionally waived after repeated Innovus `write_sdf` internal crashes. The r28 flow uses `TP_STAGE2_EXPORT_SDF=false` and records `routed_sdf_waiver.md`.
- DRC remains open: `verify_drc` stopped at the 1000 violation report limit. The reported layer/type totals were 623 Rect, 217 MinStp, 114 WidTbl, and 46 OffGrd violations.
- Connectivity remains open: `verifyConnectivity -type all` stopped at 1000 total issues, including 158 special-wire connectivity problems and 842 dangling-wire problems.
- ASAP7 M10 IMPTR-2101/2104/2108 messages are classified as ASAP7 tech-collateral issues, not routed M2-M8 signal-route DRC evidence.
- GDS streamOut warns that fake SRAM master cells `mem_0_ext` and `mem_ext` are not found in merged stdcell GDS collateral. The GDS is usable as standard-cell geometry context, not as complete fake-SRAM geometry signoff.

## Downstream Use

Stage 3/4 may consume this implementation for placement/activity/power-driven thermal trend research. All downstream reports must carry the `PG-open / DRC-open / routed-SDF-waived thermal proxy` label and must not claim signoff-quality physical verification or SDF timing simulation.
