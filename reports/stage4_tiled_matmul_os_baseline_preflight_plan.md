# Stage 4 tiled_matmul_os Baseline Preflight Plan

Date: 2026-04-26

## Status

Phase 3 is accepted as a `proxy / thermal-flow prototype` input for Phase 4 preparation. Phase 4 thermal simulation has not started yet; formal execution should begin only after user confirmation.

This preflight covers only the active route:

```text
Stage 3 grid-level power waveform -> Stage 4 PACT thermal simulation + HotSpot coarse comparison
```

It does not expand scope to thermal-aware optimization, RTL/placement optimization, additional workloads, SRAM macro detailed thermal modeling, package modeling, or multi-configuration sweeps.

## Phase 3 Handoff Accepted

Current Phase 3 handoff artifacts are present and usable for Phase 4 input generation:

| Artifact | Path / value | Phase 4 use |
| --- | --- | --- |
| Grid power | `power/stage3_tiled_matmul_os_baseline_grid_power.csv` | PACT grid power source |
| Transient ptrace | `power/stage3_tiled_matmul_os_baseline_transient_ptrace.csv` | PACT transient power source |
| Metadata | `power/stage3_tiled_matmul_os_baseline_metadata.json` | Grid dimensions and normalization metadata |
| Region summary | `power/stage3_tiled_matmul_os_baseline_region_power_summary.csv` | HotSpot coarse-block aggregation aid |
| Instance-grid map | `power/stage3_tiled_matmul_os_baseline_instance_grid_map.csv` | Hotspot traceback aid |
| Method report | `reports/stage3_tiled_matmul_os_baseline_power_trace_method.md` | Proxy method/caveat source |
| Stage report | `reports/stage3_tiled_matmul_os_baseline_stage_report.md` | Acceptance and handoff source |

Observed handoff facts:

- Stage 3 grid is `64 x 64`.
- Stage 3 transient power has `64` time rows.
- `power/stage3_tiled_matmul_os_baseline_grid_power.csv` has `262144` data rows, covering all bins for all time rows.
- Peak target-bin total proxy power is normalized to `1.0 W`; this is a flow normalization, not measured signoff power.
- Stage 2 DEF records `UNITS DISTANCE MICRONS 4000` and `DIEAREA ( 0 0 ) ( 13495456 13495456 )`, giving a die side length of `3373.864 um` or `0.003373864 m` for Phase 4 floorplan/input generation.

## Tool Preflight Results

All checks below were light smoke checks and wrote only to `/tmp`.

| Check | Result | Notes |
| --- | --- | --- |
| PACT entry | Passed | `python "$PACT_ENTRY" --help` prints the expected positional inputs and `--init`, `--steady`, `--gridSteadyFile` options. |
| PACT SuperLU smoke | Passed | Example 10 mm SuperLU steady run generated `/tmp/tp_phase4_pact_smoke/superlu_10mm.grid.steady.layer0` and `.layer1`; each layer had `1600` numeric entries. |
| HotSpot smoke | Passed | Tiny two-block `hotspot -c ... -f ... -p ... -o ...` run generated a valid `.ttrace`. |
| Xyce | Available | `Xyce -v` reports `Xyce Release 7.4.0-opensource`. Current local Xyce is serial. |
| OpenMPI | Available | `mpirun -np 2 /bin/hostname` works, but this does not make PACT parallel mode accepted because Xyce is serial. |

Current Phase 4 threading rule:

- PACT SuperLU steady runs as a Python/SuperLU path and is treated as serial for this project.
- PACT SPICE steady/transient uses `number_of_core` in the modelParams file. PACT source calls `Xyce` directly when `number_of_core <= 1` and `mpirun -np <number_of_core> Xyce ...` when `number_of_core > 1`.
- Because the current Xyce build is serial, Phase 4 must set `number_of_core = 1` for formal PACT SPICE runs.
- HotSpot has no confirmed project-level thread parameter; treat the coarse comparison as a single-process run.

## Planned Phase 4 Inputs

The Phase 4 implementation should create generated inputs under stable, stage-specific directories:

| Directory | Planned files |
| --- | --- |
| `thermal/pact/stage4_tiled_matmul_os_baseline/` | `flp_stage4_tiled_matmul_os_baseline.csv`, `ptrace_stage4_tiled_matmul_os_baseline.csv`, `lcf_stage4_tiled_matmul_os_baseline.csv`, `config_stage4_tiled_matmul_os_baseline.config`, `modelParams_stage4_tiled_matmul_os_baseline_steady_superlu.config`, `modelParams_stage4_tiled_matmul_os_baseline_transient_spice_serial.config`, PACT temperature outputs |
| `thermal/hotspot/stage4_tiled_matmul_os_baseline/` | `stage4_tiled_matmul_os_baseline.flp`, `stage4_tiled_matmul_os_baseline.ptrace`, `stage4_tiled_matmul_os_baseline.config`, `stage4_tiled_matmul_os_baseline.ttrace` |
| `artifacts/stage4/` | steady heatmaps, transient curves, hotspot ranking CSVs, comparison tables |
| `reports/` | `stage4_tiled_matmul_os_baseline_pact_thermal_report.md`, `stage4_tiled_matmul_os_baseline_hotspot_report.md`, `stage4_tiled_matmul_os_baseline_summary.md` |

PACT input format to generate:

- LCF CSV columns follow the PACT examples: `Layer,FloorplanFile,Thickness (m),PtraceFile,LateralHeatFlow`.
- Floorplan CSV columns follow the PACT examples: `UnitName,X,Y,Length (m),Width (m),ConfigFile,Label`.
- Ptrace CSV columns follow the PACT examples: steady uses `UnitName,Power`; transient must use `UnitName,Power,Power1,...` because the local PACT transient path still hard-accesses the first column as `Power` before collecting all `Power*` columns.
- Config/modelParams should be generated from local templates and must record that example material/boundary values are baseline assumptions, not package-level validation.

HotSpot input format to generate:

- `.flp` rows use block name, width, height, left x, and bottom y in meters.
- `.ptrace` header uses the same coarse block names as the `.flp`.
- Coarse blocks remain: `pe_array`, `controller_execute`, `load_store_datapath`, `scratchpad_accumulator_context`, and `other_context`.

## Phase 4 Development Steps

1. Re-read `AGENTS.md`, `docs/phase0tophase4_plan.md`, and this preflight report; confirm `git status --short` before editing.
2. Implement the smallest Stage 4 input-generation script, likely `scripts/build_stage4_thermal_inputs.py`, consuming Stage 3 grid power, transient ptrace, metadata, and region power summary.
3. Validate generated input geometry and units before running solvers: die side `0.003373864 m`, `64 x 64` grid coverage, non-negative finite power, consistent block names, and expected row counts.
4. Run PACT steady SuperLU first, with outputs isolated under `thermal/pact/stage4_tiled_matmul_os_baseline/`.
5. Run PACT transient SPICE serial with `number_of_core = 1`. If runtime or solver behavior requires a route change, update active docs before retrying.
6. Run HotSpot coarse comparison using the five documented coarse blocks.
7. Generate heatmaps, thermal curves, hotspot ranking CSVs, and PACT-vs-HotSpot comparison tables under `artifacts/stage4/`.
8. Write the required Stage 4 PACT, HotSpot, and summary reports.
9. Re-read changed docs/reports and run `git status --short` before closeout.

## Known Caveats

- Phase 3 power is a normalized proxy grid, not signoff power.
- Stage 2 remains `proxy / non-signoff`, with residual DRC and no SDF.
- SPEF is recorded as an input but was not consumed by the first Stage 3 proxy power model.
- SRAM macro bodies are not detailed thermal sources in this route.
- PACT parallel mode is not accepted with the current serial Xyce build.
- HotSpot is only a coarse trend comparison and must not be presented as the fine-grained result.

## Current Blockers

No tool-availability blocker was found in the Phase 4 preflight. User confirmation was later received and Phase 4 execution completed.

## Completion Update

Phase 4 was started and completed on 2026-04-26 after user confirmation. Final reports are:

- `reports/stage4_tiled_matmul_os_baseline_pact_thermal_report.md`
- `reports/stage4_tiled_matmul_os_baseline_hotspot_report.md`
- `reports/stage4_tiled_matmul_os_baseline_summary.md`

Generated artifacts are under `thermal/pact/stage4_tiled_matmul_os_baseline/`, `thermal/hotspot/stage4_tiled_matmul_os_baseline/`, and `artifacts/stage4/`.
