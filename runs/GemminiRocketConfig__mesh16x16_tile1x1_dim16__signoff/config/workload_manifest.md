# Workload Manifest

Date: 2026-04-29
Run root: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/`

## Fixed Workload Set

| Workload | Source | Size / behavior | Role | Check |
| --- | --- | --- | --- | --- |
| `tiled_matmul_os` | `third_party/chipyard/generators/gemmini/software/gemmini-rocc-tests/bareMetalC/tiled_matmul_os.c` | `MAT_DIM_I=64`, `MAT_DIM_K=64`, `MAT_DIM_J=64`, `NO_BIAS=1` | output-stationary GEMM compute baseline | `CHECK_RESULT=1` |
| `tiled_matmul_ws` | `third_party/chipyard/generators/gemmini/software/gemmini-rocc-tests/bareMetalC/tiled_matmul_ws.c` | `MAT_DIM_I=64`, `MAT_DIM_K=64`, `MAT_DIM_J=64`, `NO_BIAS=1` | weight-stationary GEMM dataflow contrast | `CHECK_RESULT=1` |
| `mvin_mvout` | `third_party/chipyard/generators/gemmini/software/gemmini-rocc-tests/bareMetalC/mvin_mvout.c` | `N=8`; 8 x `DIM x DIM` matrices, here 8 x 16x16 | memory/control movement contrast | program pass/fail output |

## Workload Policy

- Do not add a fourth workload to this run.
- Do not reduce matrix sizes or substitute smaller tests to make the flow pass.
- Do not describe `mvin_mvout` as PE compute-heavy; it is a data movement and control-path contrast.
- Old `small_gemm` and `thermal_smoke` results are references only, not signoff workload evidence.
