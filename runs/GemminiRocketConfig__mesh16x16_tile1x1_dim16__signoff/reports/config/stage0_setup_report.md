# Stage 0 Setup Report

Date: 2026-04-29
Run root: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/`

## Status

Stage 0 setup is in progress. This report records the initial frozen configuration, workload set, directory structure, and environment snapshot. No Stage 1-4 signoff runs have started.

2026-05-05 update: the active plan has changed to `docs/phase0tophase4_cadence_asap7_plan.md`. The original OpenROAD/reduced-ASAP7 plans referenced below are now legacy references under `docs/references/legacy_openroad_proxy/`.

## Completed

- Active-run RTL/hierarchy export completed; hierarchy map has 1326 lines and module inventory has 898 lines.
- Three workload binaries were built/exported under `workloads/<workload>/`.
- Active plan created: `docs/phase0tophase4_signoff_multiworkload_plan.md`.
- Old plan marked as reference only: `docs/phase0tophase4_plan.md`.
- Agent and helper docs updated to point to the new active plan.
- Run root created: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/`.
- Directory structure created according to the active plan.
- Initial run README created.
- Initial configuration, workload, environment, and JSON manifests created.
- Stage 1 RTL/workload scripts updated to support `RUN_ROOT` while preserving historical default paths when `RUN_ROOT` is unset.

## Frozen Hardware Configuration

`GemminiRocketConfig` / `DefaultGemminiConfig` with `meshRows=16`, `meshColumns=16`, `tileRows=1`, `tileColumns=1`, effective `DIM=16`.

Full parameter details are in `config/gemmini_config_snapshot.md` and `config/run_manifest.json`.

## Frozen Workload Set

- `tiled_matmul_os`: 64x64x64 output-stationary GEMM, `CHECK_RESULT=1`.
- `tiled_matmul_ws`: 64x64x64 weight-stationary GEMM, `CHECK_RESULT=1`.
- `mvin_mvout`: 8 x 16x16 matrix movement/control-path contrast.

Full workload details are in `config/workload_manifest.md`.

## Immediate Next Work

Before Stage 1 heavy runs:

1. Run `bash -n` and lightweight command-path validation for the updated scripts.
2. Generate active-run RTL and hierarchy map with `RUN_ROOT` set.
3. Build the three fixed workload binaries into the active run root.
4. Start the three complete Stage 1 workload runs only after output paths and failure-stop behavior are confirmed.

## Validation

- `bash -n` passed for `scripts/build_gemmini_workloads.sh`, `scripts/run_gemmini_workload.sh`, and `scripts/run_gemmini_rtl_generation.sh`.
- `python -m json.tool` passed for `config/run_manifest.json`.
- `source tools/env_gemmini_thermal.sh && scripts/check_environment.sh` passed on 2026-04-29.

## Known Constraints

- No proxy fallback is allowed for this run.
- Old proxy outputs may be read for method reference only.
- Any Stage 1-4 failure must be documented before retry or route change.

## Stage 1 Parameter Decision Before Retry

Date: 2026-04-29

The interrupted `tiled_matmul_os` attempt used `MAKE_JOBS=4`, `VERILATOR_THREADS=16`, `VCD_PARSER_WORKERS=128`, and `NUMACTL=1`. After re-checking the historical threading records:

- `MAKE_JOBS` controls outer make/build parallelism. It is useful when building the Verilator debug simulator, but it is not the simulation thread count. Since the debug simulator now exists, Stage 1 workload reruns should use `BUILD_DEBUG_SIM=0`; `MAKE_JOBS` is then not performance-critical and will be kept conservative.
- `VERILATOR_THREADS=16` remains the best supported simulator-thread choice on this host from the historical `mvin_mvout` VCD smoke trend. Larger values `32/64/128` were slower in that test and should not be used as defaults.
- `VCD_PARSER_WORKERS=128` remains the best supported parser setting on this host: the historical parser tests showed identical CSV output across worker counts and fastest runtime at 128 workers for the measured `mvin_mvout` VCD; the old 40.83 GiB `tiled_matmul_os` VCD was also parsed successfully with 128 workers.
- `NUMACTL=1` is not valid on this host right now because `numactl` is absent. The next Stage 1 runs will use `NUMACTL=0`.

The interrupted partial `tiled_matmul_os` output under Chipyard simulator output is not accepted as Stage 1 evidence and will not be used downstream. The next run will use a new run tag.
