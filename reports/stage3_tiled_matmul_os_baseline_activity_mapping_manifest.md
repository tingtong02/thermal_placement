# Stage 3 Activity Mapping Manifest

## Mapping Strategy

- RTL source activity: Stage 1 target-scoped Gemmini VCD window refinement.
- Physical source: Stage 2 proxy `6_final.def`.
- Gate/physical mapping: DEF instance-name prefix classification.
- Grid: `64 x 64`.
- Filler, tap, decap, and tie cells are excluded from active standard-cell proxy power.
- Unmatched standard cells are kept as `unmapped_standard_cell` context and assigned low background proxy activity.

## Physical Mapping Counts

- raw_components: `4565776`
- active_components_written: `1333998`
- skipped_physical_fill_tap_decap_tie: `3231778`
- mapped_non_unmapped_components: `1181030`
- mapped_ratio: `0.885331`

| region | instances | activity_signals | activity_toggles |
| --- | ---: | ---: | ---: |
| `pe_array` | 462375 | 5698 | 2080970 |
| `scratchpad` | 317024 | 2350 | 1377625 |
| `gemmini_other` | 291752 | 550 | 1258688 |
| `unmapped_standard_cell` | 152968 | 0 | 0 |
| `controller` | 56261 | 78 | 84347 |
| `load_store_dma` | 30420 | 212 | 17226 |
| `clock_tree` | 23198 | 0 | 0 |

## Blackbox / Proxy Boundary

Memory macro bodies remain proxy/blackbox context from Stage 2 and are not modeled as detailed SRAM thermal sources.
