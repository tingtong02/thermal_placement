# Gemmini Small GEMM Thermal Validation Report

更新时间：2026-04-20

## 1. 目标

按照 [gemmini_thermal_validation_plan.md](/home/lisihang/thermal_placement/docs/gemmini_thermal_validation_plan.md) 的主线，先实现一个较小 GEMM 测试，验证以下最小闭环是否可运行：

Gemmini bare-metal workload -> Verilator debug simulation -> VCD -> activity CSV -> activity-weighted power proxy -> HotSpot steady-state。

本轮不包含 ORFS placement，也不声明 signoff 级功耗精度。

## 2. Workload

新增 workload：

- [small_gemm.c](/home/lisihang/thermal_placement/workloads/small_gemm/small_gemm.c)

特征：

- GEMM 尺寸：`16 x 16 x 16`
- 数据类型：使用当前 Gemmini 配置的 `elem_t = int8_t`
- 数据流：`OUTPUT_STATIONARY`
- 指令路径：`gemmini_mvin(A)`、`gemmini_mvin(B)`、`gemmini_compute_preloaded()`、`gemmini_mvout(C)`
- 功能检查：CPU 侧计算 gold，与 Gemmini 输出逐元素比较
- 成功标志：stdout 中出现 `small-gemm-ok`

## 3. 执行命令

```bash
GEMM_MAX_CYCLES=800000 GEMM_TIMEOUT_SECS=600 scripts/run_small_gemm_thermal_flow.sh
```

该脚本会自动完成：

1. 构建 [small_gemm-baremetal](/home/lisihang/thermal_placement/sim/binaries/GemminiRocketConfig/small_gemm-baremetal)
2. 运行 `GemminiRocketConfig` Verilator debug simulator
3. 导出 [small_gemm.vcd](/home/lisihang/thermal_placement/sim/waves/GemminiRocketConfig/small_gemm.vcd)
4. 生成 [small_gemm_region_activity.csv](/home/lisihang/thermal_placement/sim/activity/small_gemm_region_activity.csv)
5. 生成 HotSpot 输入 [small_gemm.flp](/home/lisihang/thermal_placement/thermal/floorplans/small_gemm.flp) 与 [small_gemm.ptrace](/home/lisihang/thermal_placement/thermal/power/small_gemm.ptrace)
6. 运行 HotSpot，输出 [small_gemm.ttrace](/home/lisihang/thermal_placement/thermal/steady/small_gemm.ttrace)
7. 生成自动报告 [small_gemm_report.md](/home/lisihang/thermal_placement/reports/small_gemm/small_gemm_report.md)

## 4. 结果摘要

本轮运行结果：

- `CONFIG=GemminiRocketConfig`
- `MAKE_JOBS=128`
- `GEMM_MAX_CYCLES=800000`
- `sim_status=0`
- stdout 捕获到 `small-gemm-start`
- stdout 捕获到 `small-gemm-ok`
- Verilator `$finish` 时间：约 `566us`
- VCD 大小：约 `1.6GB`
- VCD 解析信号数：`32687`
- VCD time steps：`1131735`
- VCD last time：`565825500 ps`

区域活动率前几项：

| region | toggle_count | avg_normalized_activity |
| --- | ---: | ---: |
| `tl_soc_glue` | 39306858 | 3.793091e-04 |
| `pe_array` | 13567362 | 2.200771e-04 |
| `non_gemmini_context` | 13120949 | 3.468698e-04 |
| `controller` | 1148836 | 7.797956e-05 |

HotSpot steady-state：

| 指标 | 值 |
| --- | ---: |
| `Tmax` | 318.36 K |
| `Tavg` | 318.36 K |
| `Tmin` | 318.35 K |
| `max_gradient_proxy` | 0.01 K |

## 5. 结论

本轮已经跑通一个真实 Gemmini GEMM workload 的最小热验证闭环。和之前纯 smoke 相比，这次 workload 确实执行了 Gemmini 指令并完成了功能校验。

当前观察到的主要限制：

- activity 聚合仍是模块名/路径关键词级，`scratchpad`、`accumulator`、`load_store_dma` 还没有被充分拆分到 bank/子模块级。
- HotSpot 输入仍使用简单 activity-weighted proxy，温度差异很小，不能作为物理结论。
- 完整 VCD 较大，单个 16x16 GEMM 已达到约 1.6GB，后续需要考虑 FST、VCD 截窗或更细的 trace 控制。

下一步建议：

1. 改进 hierarchy map，让 scratchpad/accumulator/DMA 在 VCD 路径中更准确命中。
2. 增加 PE array 子区域统计，例如 4x4 super-block。
3. 从当前 bucket power 过渡到 macro power，并生成四组 grouping case。
4. 开始 ORFS placement smoke，再导出 floorplan 到 HotSpot。
