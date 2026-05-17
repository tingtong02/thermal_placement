# Stage 0 Tiled Matmul OS Baseline Closure

## Scope Locked

- active route: Stage 0 research definition -> Stage 1 RTL activity waveform -> Stage 2 ASAP7 standard-cell implementation -> Stage 3 grid-level power waveform -> Stage 4 PACT thermal simulation + HotSpot coarse comparison
- research target: Gemmini PE array, control logic, and nearby datapath standard cells
- memory policy: scratchpad and accumulator storage arrays are not the detailed thermal target; Stage 2-4 should blackbox, exclude, stub, or treat them as coarse context if they would dominate implementation
- process target: ASAP7 reduced technology setup in this repository
- thermal solvers: PACT mainline, HotSpot coarse comparison

## Baseline Locked

- baseline name: `tiled_matmul_os_baseline`
- workload source: `third_party/chipyard/generators/gemmini/software/gemmini-rocc-tests/bareMetalC/tiled_matmul_os.c`
- workload type: sustained output-stationary tiled GEMM
- matrix size: `MAT_DIM_I/K/J=64`
- dataflow: `tiled_matmul_auto(..., OS)`
- build entry: `scripts/build_gemmini_workloads.sh tiled_matmul_os`
- run entry: `RUN_TAG=stage1_tiled_matmul_os_baseline_20260423 TIMEOUT_CYCLES=100000000 scripts/run_gemmini_workload.sh tiled_matmul_os`

The baseline is fixed for Stage 1-4. Do not add a second workload, shorten the matrix, or replace the workload to manage runtime.

## Phase 0 Exit Check

| Requirement | Status | Evidence |
| --- | --- | --- |
| Single baseline selected | pass | `tiled_matmul_os_baseline` |
| Output-stationary GEMM selected | pass | `tiled_matmul_auto(..., OS)` in the official Gemmini bare-metal test |
| Target module boundary defined | pass | PE array, controllers, load/store/execute nearby datapath; memory arrays excluded from detailed target |
| Stage 1 input and output paths defined | pass | `sim/binaries/`, `sim/waves/`, `sim/logs/`, `sim/activity/`, `reports/stage1_*` |
| Stage 2-4 plan boundaries defined | pass | documented in `docs/phase0tophase4_plan.md` |
| Blocking dependencies separated from planned work | pass | Stage 2-4 missing scripts/configs are planned work; Stage 1 toolchain checks passed before run |

## Transition To Stage 1

Stage 0 is closed for the current route. Stage 1 may proceed with RTL generation, workload build, Verilator debug simulation, VCD capture, activity extraction, and window selection for the fixed baseline only.
