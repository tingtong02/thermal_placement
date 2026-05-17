# Small GEMM Thermal Validation Report

## 范围

这是一个最小 Gemmini GEMM 验证流程，用于对齐验证计划中的 Phase B/C/D/H 工具闭环：运行一个 16x16 output-stationary GEMM，导出 VCD，提取活动率，用简单 activity-weighted proxy 生成 HotSpot 输入并完成 steady-state 热仿真。该报告不是 signoff 级功耗报告，也尚未包含 ORFS placement。

## 运行配置

- workload: `small_gemm`
- config: `GemminiRocketConfig`
- matrix: `DIM x DIM` GEMM，当前为 `16 x 16 x 16`
- dataflow: `OUTPUT_STATIONARY`
- max_cycles: `800000`
- sim_status: `0`
- make_jobs: `128`
- functional_ok_seen: `True`
- functional_fail_seen: `False`

## 产物

- binary: `sim/binaries/GemminiRocketConfig/small_gemm-baremetal`
- stdout log: `sim/logs/GemminiRocketConfig/small_gemm.log`
- stderr log: `sim/logs/GemminiRocketConfig/small_gemm.err`
- VCD: `sim/waves/GemminiRocketConfig/small_gemm.vcd` (1704226598 bytes)
- region activity: `sim/activity/small_gemm_region_activity.csv`
- HotSpot floorplan: `thermal/floorplans/small_gemm.flp`
- HotSpot power trace: `thermal/power/small_gemm.ptrace`
- HotSpot steady output: `thermal/steady/small_gemm.ttrace`

## 区域活动率

| region | signals | toggles | avg_normalized_activity |
| --- | ---: | ---: | ---: |
| `tl_soc_glue` | 4533 | 39306858 | 3.793091e-04 |
| `pe_array` | 3394 | 13567362 | 2.200771e-04 |
| `non_gemmini_context` | 2133 | 13120949 | 3.468698e-04 |
| `controller` | 521 | 1148836 | 7.797956e-05 |
| `accumulator` | 0 | 0 | 0.000000e+00 |
| `gemmini_other` | 0 | 0 | 0.000000e+00 |
| `load_store_dma` | 30 | 0 | 0.000000e+00 |
| `scratchpad` | 0 | 0 | 0.000000e+00 |

## HotSpot Steady-State

- Tmax: `318.36 K`
- Tavg: `318.36 K`
- Tmin: `318.35 K`
- max_gradient_proxy: `0.01 K`

| hottest_block | temperature_K |
| --- | ---: |
| `gemmini_other` | 318.36 |
| `load_store_dma` | 318.36 |
| `non_gemmini_context` | 318.36 |
| `pe_array` | 318.36 |
| `accumulator` | 318.35 |

## 初步解读

本流程确认了本地 RISC-V 工具链、Gemmini bare-metal 程序、Verilator debug 仿真器、VCD 活动率提取、activity-to-power proxy 和 HotSpot 调用可以形成一条可复现路径。当前功耗数值仍是相对 proxy；下一步应补 PE 子区域/bank 级映射，并进入 ORFS macro placement 对照实验。
