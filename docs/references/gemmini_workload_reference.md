# Gemmini Workload Reference

## 文档定位

注意：本文件只是参考资料，不保证其中历史流程、命令、路径或结论可以在新的开发中直接复用。使用前必须对照 `docs/phase0tophase4_signoff_multiworkload_plan.md` 和当前仓库状态重新确认。

本文件从归档的旧 Gemmini 验证记录中提炼出仍可复用的 workload 经验，供当前 [phase0tophase4_signoff_multiworkload_plan.md](/home/lisihang/thermal_placement/docs/phase0tophase4_signoff_multiworkload_plan.md) 在阶段 0 冻结 workload 集合、阶段 1 采波形时参考。旧 `phase0tophase4_plan.md` 只作为历史参考。

原始历史文档见：

- [docs/archive/gemmini_thermal_validation_2026-04-23/gemmini_small_gemm_thermal_report.md](/home/lisihang/thermal_placement/docs/archive/gemmini_thermal_validation_2026-04-23/gemmini_small_gemm_thermal_report.md)
- [docs/archive/gemmini_thermal_validation_2026-04-23/gemmini_thermal_handoff.md](/home/lisihang/thermal_placement/docs/archive/gemmini_thermal_validation_2026-04-23/gemmini_thermal_handoff.md)

## 1. 当前仓库里现成的 workload 入口

### 1.1 `thermal_smoke`

源文件：

- [workloads/thermal_smoke/thermal_smoke.c](/home/lisihang/thermal_placement/workloads/thermal_smoke/thermal_smoke.c)

运行入口：

- [scripts/run_thermal_smoke_flow.sh](/home/lisihang/thermal_placement/scripts/run_thermal_smoke_flow.sh)

特点：

- 极轻量
- 主要用于验证编译、Verilator、VCD、活动率提取、HotSpot 输入导出是否连通
- 不适合替代当前计划固定的三 workload signoff 集合

### 1.2 `small_gemm`

源文件：

- [workloads/small_gemm/small_gemm.c](/home/lisihang/thermal_placement/workloads/small_gemm/small_gemm.c)

运行入口：

- [scripts/run_small_gemm_thermal_flow.sh](/home/lisihang/thermal_placement/scripts/run_small_gemm_thermal_flow.sh)

特点：

- 历史上已经验证过功能正确
- 运行路径覆盖 `mvin -> compute -> mvout -> check_result`
- 能生成完整 VCD 和活动率 CSV
- 是当前仓库里最接近“真实 Gemmini GEMM 样例”的现成本地 workload

### 1.3 `gemmini-rocc-tests`

构建入口：

- [scripts/build_gemmini_workloads.sh](/home/lisihang/thermal_placement/scripts/build_gemmini_workloads.sh)
- [scripts/run_gemmini_workload.sh](/home/lisihang/thermal_placement/scripts/run_gemmini_workload.sh)

特点：

- 覆盖更真实的 Gemmini 官方 bare-metal workload
- 包括 `tiled_matmul_os` 这类 GEMM 程序，也包括 `mvin_mvout` 这类基础搬运测试
- 是当前三个固定 workload 的来源
- 其中不同程序的角色不同，不能把所有官方测试都当成正式 signoff workload

### 1.4 当前固定 workload：`tiled_matmul_os`

源文件：

- `third_party/chipyard/generators/gemmini/software/gemmini-rocc-tests/bareMetalC/tiled_matmul_os.c`

当前路线下的定义：

- 这是 Gemmini 官方 bare-metal tiled GEMM 程序，不是本仓库自写 workload
- bare-metal 参数固定为 `MAT_DIM_I=64`、`MAT_DIM_K=64`、`MAT_DIM_J=64`
- 数据流固定为 `OS`，即 output-stationary
- 程序语义是 `C = A x B + D`；当前 bare-metal 配置里 `NO_BIAS=1`，因此 `D` 实际置零
- 数值类型沿当前 Gemmini 参数：`A/B` 为 `elem_t=int8_t`，累加路径为 `acc_t=int32_t`
- 程序先执行 CPU `full_matmul()` 生成 golden result，再调用 `tiled_matmul_auto(..., OS)` 触发 Gemmini 阵列计算，最后做正确性比对

为什么它被选为当前 compute baseline 之一：

- 它是官方程序，来源稳定，不是临时脚本
- `64 x 64 x 64` 在当前 `DIM=16` 下会触发多 tile matmul，比 `small_gemm` 更接近持续高负载阵列活动
- 它虽然运行成本高，但更符合当前研究要的 sustained high-load GEMM

### 1.5 当前固定 workload：`tiled_matmul_ws`

源文件：

- `third_party/chipyard/generators/gemmini/software/gemmini-rocc-tests/bareMetalC/tiled_matmul_ws.c`

当前路线下的定义：

- bare-metal 参数固定为 `MAT_DIM_I=64`、`MAT_DIM_K=64`、`MAT_DIM_J=64`
- `CHECK_RESULT=1`，`NO_BIAS=1`
- 软件侧使用 weight-stationary 路径，作为与 `tiled_matmul_os` 同规模 GEMM 的 dataflow 对照

### 1.6 当前固定 workload：`mvin_mvout`

说明：

- `mvin_mvout` 是 Gemmini 官方基础测试，用于验证搬入/搬出路径和相关控制逻辑
- 当前配置 `DIM=16`，源码 `N=8`，因此移动 8 个 16x16 矩阵
- 它不是 PE 高负载 GEMM，不得被描述为 compute-heavy workload
- 本轮将它作为 memory/control movement 对照 workload 纳入 Stage 1-4，而不是仅作为 smoke

## 2. 历史已验证样例：`small_gemm`

历史执行命令：

```bash
GEMM_MAX_CYCLES=800000 GEMM_TIMEOUT_SECS=600 scripts/run_small_gemm_thermal_flow.sh
```

历史上已记录的现象：

- `sim_status=0`
- stdout 出现 `small-gemm-start`
- stdout 出现 `small-gemm-ok`
- 完整 VCD 约 `1.6 GB`
- `parsed_signals=32687`
- `time_steps=1131735`
- `last_time_ps=565825500`

这说明：

- 仓库现成的 `small_gemm` 可以作为一个“真实已验证样例”
- 它对于阶段 1 波形采集和后续功耗映射脚本调试非常有用
- 但它也提示当前 trace 成本不低，不能把它当成零代价回归测试

## 3. 对新计划的实际参考价值

### 3.1 可直接复用的判断

对当前阶段 0–4，`small_gemm` 有三点直接参考价值：

- 证明本仓库已存在可运行的 GEMM bare-metal 程序骨架
- 提供一条已知可行的 Verilator + VCD + activity 提取路径
- 提供 workload 路线可行性的已知下界，即“至少这个 GEMM 已经能跑通”

### 3.2 不能直接照搬的结论

旧报告里有些结论不能直接当成当前计划结论：

- 旧报告服务于 proxy-power + HotSpot 验证，不是 ASAP7 标准单元级热仿真结论
- 旧 GEMM 尺寸 `16 x 16 x 16` 是否足够“持续高负载”，需要按新计划重新判断
- 旧温度差异很小，不能用于支持当前 PACT 主线热图结论

## 4. 当前 workload 集合

当前 active signoff 计划已固定 workload 集合，不再做选择讨论：

1. `tiled_matmul_os`：64x64x64 output-stationary GEMM，compute-heavy baseline。
2. `tiled_matmul_ws`：64x64x64 weight-stationary GEMM，同规模 dataflow 对照。
3. `mvin_mvout`：8 个 16x16 矩阵搬入/搬出，memory/control movement 对照。

`thermal_smoke` 与 `small_gemm` 仍可作为脚本和工具链参考，但不能替代当前三 workload 的正式 Stage 1-4 验收。

## 5. 推荐记录方式

当前计划要求固定三个 workload。Stage 0 必须分别记录：

- 名称
- 来源脚本或源码
- 选择理由
- 成功标志
- 预期热行为
- 预估波形规模

