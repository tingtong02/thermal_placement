# Stage 4 HotSpot Coarse Comparison Report: tiled_matmul_os Baseline

Date: 2026-05-03

## Scope

HotSpot is used only as a coarse block-level trend comparison. It is not the fine-grained result. Power is aggregated into the five coarse blocks: `pe_array`, `controller_execute`, `load_store_datapath`, `scratchpad_accumulator_context`, and `other_context`.

## Results

- HotSpot rows: `64`
- Final max block: `other_context`
- Final max temperature: `318.210` K
- Peak max temperature: `318.230` K

HotSpot block coordinates are hand-authored coarse regions and are not a placed-standard-cell physical distribution. Use corrected PACT artifacts for fine-grid physical-coordinate inspection.

## Artifacts

- `artifacts/stage4/hotspot_transient_stats.csv`
- `artifacts/stage4/hotspot_block_rank.csv`
- `artifacts/stage4/hotspot_block_final.png`
- `artifacts/stage4/thermal_trace_pact_vs_hotspot.png`
