# Stage 3 Tiled Matmul OS Baseline Stage Report

## Status

- Date: 2026-04-26
- Stage: 3 grid-level power waveform
- Baseline: `tiled_matmul_os_baseline`
- Acceptance: `proxy / thermal-flow prototype`
- Stage 4 readiness: ready for PACT/HotSpot input preparation with caveats

## Inputs

Stage 1 activity:

- VCD: `sim/waves/GemminiRocketConfig/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_baseline_20260423.vcd`
- Coarse window CSV: `sim/activity/stage1_tiled_matmul_os_baseline_20260423_window_activity.csv`
- Target-window activity: `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_activity.csv`
- Target-window bins: `sim/activity/stage1_tiled_matmul_os_baseline_20260423_target_window_bins.csv`
- Target-window report: `reports/stage1_tiled_matmul_os_baseline_target_windows.md`

Stage 2 proxy physical package:

- DEF: `physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.def`
- Netlist: `physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.v`
- SDC: `physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.sdc`
- SPEF: `physical/stage2_tiled_matmul_os_baseline_asap7/results/asap7/stage2_tiled_matmul_os_baseline_asap7/noaddermap/6_final.spef`
- Final-report JSON/log remain under ORFS `logs/.../noaddermap/` and were not moved.

## Execution Summary

1. Refined the coarse Stage 1 `steady_high_load` window using full-SoC VCD data filtered to Gemmini target scopes.
2. Excluded `monitor` / `watchdog` simulator debug paths after the first target extraction showed they dominated Top-N toggles.
3. Generated a target activity CSV and 64-bin target activity profile.
4. Parsed Stage 2 `6_final.def` and ASAP7 Liberty areas.
5. Built a `64 x 64` instance-to-grid map from 1,333,998 active standard-cell components, excluding filler/tap/decap/tie cells.
6. Generated grid power and transient ptrace outputs using a documented proxy power model.
7. Ran lightweight OpenSTA sanity: Liberty/netlist/SDC read and `report_checks` succeeded; SPEF was recorded but not read in this light sanity pass.

## Key Results

- Candidate coarse window: `9272956950` to `10303285500 ps`
- Refined target-active window: `10222791082` to `10238889965 ps`
- Target signals in VCD header after monitor/watchdog exclusion: `17502`
- Active target signals: `8888`
- Grid: `64 x 64`
- Grid time rows: `64`
- Grid rows: `262144`
- Grid coverage: every time row has all `4096` bins
- Negative/non-finite power values: `0`
- Peak total proxy power: `1.0 W` at bin `59`
- Average total proxy power over the 64 candidate bins: about `0.01979 W`

Region proxy power at peak normalization:

| region | instances | proxy_power_w | share |
| --- | ---: | ---: | ---: |
| `gemmini_other` | 291752 | 0.40850387643 | 0.40850388 |
| `pe_array` | 462375 | 0.252617470616 | 0.25261747 |
| `scratchpad` | 317024 | 0.164598979832 | 0.16459898 |
| `unmapped_standard_cell` | 152968 | 0.123314676667 | 0.12331468 |
| `controller` | 56261 | 0.0384145625342 | 0.03841456 |
| `clock_tree` | 23198 | 0.00917649014461 | 0.00917649 |
| `load_store_dma` | 30420 | 0.00337394377624 | 0.00337394 |

## Outputs

Power outputs:

- `power/stage3_tiled_matmul_os_baseline_grid_power.csv`
- `power/stage3_tiled_matmul_os_baseline_transient_ptrace.csv`
- `power/stage3_tiled_matmul_os_baseline_instance_grid_map.csv`
- `power/stage3_tiled_matmul_os_baseline_region_power_summary.csv`
- `power/stage3_tiled_matmul_os_baseline_metadata.json`

Reports:

- `reports/stage3_tiled_matmul_os_baseline_input_manifest.md`
- `reports/stage3_tiled_matmul_os_baseline_activity_mapping_manifest.md`
- `reports/stage3_tiled_matmul_os_baseline_power_trace_method.md`
- `reports/stage3_tiled_matmul_os_baseline_top_power_instances.md`
- `reports/stage3_tiled_matmul_os_baseline_top_toggle_instances.md`
- `reports/stage3_tiled_matmul_os_baseline_hotspot_traceback.md`
- `reports/stage3_tiled_matmul_os_baseline_opensta_sanity.tcl`
- `reports/stage3_tiled_matmul_os_baseline_opensta_sanity.log`

Scripts added:

- `scripts/extract_stage3_target_window_activity.py`
- `scripts/build_stage3_power_grid.py`

## Validation

- Python syntax checks passed for both Stage 3 scripts.
- Target-window VCD smoke extraction passed before the full extraction.
- Full target-window extraction completed with `workers=16`.
- Grid integrity check passed: `262144` rows equals `64 time rows x 64 x 64 grid bins`.
- All grid powers are finite and non-negative.
- OpenSTA lightweight sanity returned status `0` after removing unsupported `report_design_area`.

## Caveats

- Stage 3 is not signoff power. It is a reproducible proxy for Stage 4 thermal-flow prototyping.
- No gate-level SAIF or SDF is available. The method uses target-window RTL activity, DEF placement, Liberty cell area, and region mapping.
- SPEF is recorded as an input but is not consumed in the first proxy power model.
- Stage 2 residual DRC, memory blackbox/proxy handling, relaxed timing, and non-signoff status remain inherited caveats.
- OpenSTA sanity reports a severe timing violation; this is expected under the current Phase 2 proxy and is not treated as timing closure.
- `proxy_total_power_w=1.0` is a normalization for the selected peak target bin, not measured silicon or signoff power.

## Stage 4 Handoff

Stage 4 can proceed by converting `power/stage3_tiled_matmul_os_baseline_grid_power.csv` or `power/stage3_tiled_matmul_os_baseline_transient_ptrace.csv` into PACT and coarse HotSpot inputs. The Stage 4 report must preserve the Stage 2/3 proxy caveats and avoid strict thermal-accuracy claims.
