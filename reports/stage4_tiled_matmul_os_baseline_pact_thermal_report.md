# Stage 4 PACT Thermal Report: tiled_matmul_os Baseline

Date: 2026-05-03

## Scope

This report covers the PACT mainline thermal result for `tiled_matmul_os_baseline`. Inputs are derived from Stage 3 normalized proxy grid power, so the result remains a thermal-flow prototype and not signoff thermal analysis.

## Coordinate Correction

**Important:** PACT raw grid result files are not in DEF physical `grid_y` order. PACT raw row `0` corresponds to the physical top of the die, while Stage 3 DEF/grid artifacts use `grid_y=0` at the physical bottom. All user-facing PACT artifacts in `artifacts/stage4/` now apply:

```text
physical_grid_y = 64 - 1 - pact_raw_row_y
```

Raw PACT row-order CSVs are retained only as audit artifacts with `_pact_raw_order` in the filename. The main PACT grid/rank/heatmap files are the corrected physical-coordinate versions.

## Inputs

- Stage 3 grid: `64 x 64`
- Die side: `0.003373864 m`
- Time rows: `64`
- Peak proxy power: `1.000000 W` at Stage 3 time index `59`
- PACT steady solver: SuperLU
- PACT transient solver: generated PACT SPICE transient netlist solved by serial Xyce with `number_of_core = 1`

## Compatibility Notes

The local PACT transient path required two compatibility repairs recorded in `docs/gemmini_thermal_issue_log.md` items 69 and 70. The coordinate correction recorded here is a post-processing orientation fix only; it does not change the PACT solver inputs or vendored PACT source.

## Results, DEF Physical Coordinates

- Steady layer0 min/mean/max: `322.050` / `327.003` / `333.720` K
- Steady layer1 min/mean/max: `322.050` / `326.935` / `333.500` K
- Steady layer0 hotspot: physical grid `(22, 16)`, raw PACT row-order location `(22, 47)`
- Transient layer0 final max: `318.180` K
- Transient layer0 peak max: `318.180` K
- Transient solved rows: `64`

## Artifacts

- `artifacts/stage4/pact_coordinate_fix_manifest.json`
- `artifacts/stage4/pact_coordinate_fix_manifest.csv`
- `artifacts/stage4/pact_steady_layer0_grid.csv`
- `artifacts/stage4/pact_steady_layer0_grid_pact_raw_order.csv`
- `artifacts/stage4/heatmap_steady_pact_layer0.png`
- `artifacts/stage4/heatmap_transient_final_pact_layer0.png`
- `artifacts/stage4/thermal_trace_pact_vs_hotspot.png`
- `artifacts/stage4/pact_transient_stats.csv`
- `artifacts/stage4/pact_hotspot_rank.csv`
