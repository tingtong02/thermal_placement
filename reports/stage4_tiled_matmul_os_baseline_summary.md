# Stage 4 Summary: tiled_matmul_os Baseline

Date: 2026-05-03

## Acceptance Status

Stage 4 completed for the historical baseline route as a `proxy / thermal-flow prototype`: PACT steady, PACT transient serial-Xyce, HotSpot coarse comparison, figures, tables, and reports were generated.

## Coordinate Correction

**Important:** PACT raw row order was found to be vertically inverted relative to the Stage 3 DEF physical grid convention. All main PACT artifacts under `artifacts/stage4/` have been regenerated in DEF physical coordinates with `grid_y=0` at the die bottom. Raw PACT row-order grids are retained only with `_pact_raw_order` filenames.

## Key Answers, Corrected Physical Coordinates

1. Hotspot location: PACT steady layer0 peaks at physical grid `(22, 16)` with `333.720` K. The old raw row-order coordinate was `(22, 47)` and must not be used as a physical location.
2. Sustained high-load behavior: PACT steady reaches a peak delta of `15.570` K over ambient under the normalized `1 W` peak proxy-power condition; the short transient window remains near ambient and peaks at `318.180` K.
3. PACT vs HotSpot trend: both flows run successfully on the same Stage 3 proxy power source. HotSpot is only a five-block coarse trend comparison; corrected PACT provides the fine-grid physical hotspot pattern.
4. Standard-cell interpretation: use `standard_cell_context/` after this regeneration because it now overlays standard-cell power/density against corrected PACT physical coordinates.

## Caveats

- Stage 3 power is normalized proxy power, not signoff power.
- Stage 2 remains `proxy / non-signoff`, has residual DRC, and has no SDF.
- SRAM macro bodies are not detailed thermal sources.
- The coordinate fix is a post-processing orientation fix. It does not rerun or alter PACT solver inputs.

## Main Artifacts

- `artifacts/stage4/pact_coordinate_fix_manifest.json`
- `artifacts/stage4/heatmap_steady_pact_layer0.png`
- `artifacts/stage4/heatmap_transient_final_pact_layer0.png`
- `artifacts/stage4/thermal_trace_pact_vs_hotspot.png`
- `artifacts/stage4/temperature_comparison_summary.csv`
