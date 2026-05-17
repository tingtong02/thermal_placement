# Gemmini Flow Reference

## 文档定位

注意：本文件只是参考资料，不保证其中历史流程、命令、路径或结论可以在新的开发中直接复用。使用前必须对照 `docs/phase0tophase4_signoff_multiworkload_plan.md` 和当前仓库状态重新确认。

本文件从已归档的 Gemmini 热验证路线中提炼出仍然可复用的流程信息，服务于当前 [phase0tophase4_signoff_multiworkload_plan.md](/home/lisihang/thermal_placement/docs/phase0tophase4_signoff_multiworkload_plan.md)。旧 `phase0tophase4_plan.md` 只作为历史参考。

它不是旧计划的继续执行文档，也不把旧结果当成当前主线结论。它的作用是回答：

- 仓库里现成有哪些 Gemmini 相关脚本可以直接复用
- 历史上哪些最小闭环已经跑通过
- 哪些经验可以直接迁移到当前阶段 0–4
- 哪些内容必须重新生成，而不能继续沿用归档产物

原始历史快照见：

- [docs/archive/gemmini_thermal_validation_2026-04-23/gemmini_thermal_handoff.md](/home/lisihang/thermal_placement/docs/archive/gemmini_thermal_validation_2026-04-23/gemmini_thermal_handoff.md)
- [docs/archive/gemmini_thermal_validation_2026-04-23/repository_handoff_2026-04-23.md](/home/lisihang/thermal_placement/docs/archive/gemmini_thermal_validation_2026-04-23/repository_handoff_2026-04-23.md)

## 1. 可直接复用的入口

统一环境入口：

```bash
cd /home/lisihang/thermal_placement
source tools/env_gemmini_thermal.sh
```

建议首先执行的环境自检：

```bash
scripts/check_environment.sh
```

这条自检目前会检查：

- Chipyard/Gemmini 所需路径
- Python/VCD 解析环境
- sbt / Verilator / Yosys / OpenSTA / OpenROAD / ORFS / HotSpot
- Xyce / OpenMPI / slang / sv2v / yosys-slang / PACT

## 2. 可复用的 Gemmini 脚本

### 2.1 RTL 与层级

- [scripts/run_gemmini_rtl_generation.sh](/home/lisihang/thermal_placement/scripts/run_gemmini_rtl_generation.sh)
  生成 `GemminiRocketConfig` RTL，并调用层级清点脚本。当前 signoff run 应设置 `RUN_ROOT=runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff`，使 RTL 和 hierarchy 产物进入 run 根目录。
- [scripts/inspect_gemmini_hierarchy.py](/home/lisihang/thermal_placement/scripts/inspect_gemmini_hierarchy.py)
  从导出 RTL 和 hierarchy JSON 中生成模块清单与 `hierarchy_map.yaml`。

当前路线下需要注意：

- 旧 `hierarchy_map.yaml` 已归档，不在 active `configs/gemmini/` 下长期保留。
- 如果当前阶段 1 还要做 Gemmini 波形活动统计，应重新运行 RTL 导出流程生成新的 active 映射。

### 2.2 Workload 构建与仿真

- [scripts/build_gemmini_workloads.sh](/home/lisihang/thermal_placement/scripts/build_gemmini_workloads.sh)
  构建 `gemmini-rocc-tests` bare-metal workload。设置 `RUN_ROOT` 后，binary 按 workload 写入 `RUN_ROOT/workloads/<workload>/`。
- [scripts/run_gemmini_workload.sh](/home/lisihang/thermal_placement/scripts/run_gemmini_workload.sh)
  运行指定 bare-metal workload，并导出日志、波形、activity 和报告。设置 `RUN_ROOT` 后，产物按 workload 写入 `sim/`、`activity/`、`reports/`、`artifacts/` 对应子目录。
- [scripts/build_thermal_smoke_binary.sh](/home/lisihang/thermal_placement/scripts/build_thermal_smoke_binary.sh)
  构建极小 smoke 程序。
- [scripts/build_small_gemm_binary.sh](/home/lisihang/thermal_placement/scripts/build_small_gemm_binary.sh)
  构建本地 `small_gemm` bare-metal 程序。

### 2.3 当前 active 配置快照

当前 Stage 1 使用的不是 Gemmini-only 顶层，而是完整 Chipyard/Rocket SoC 配置 `GemminiRocketConfig`：

- Scala 配置来源：`third_party/chipyard/generators/gemmini/chipyard/GemminiConfigs.scala`
- 组合方式：`DefaultGemminiConfig + WithNHugeCores(1) + WithSystemBusWidth(128) + AbstractConfig`
- 含义：当前 Verilator 波形是完整 `TestHarness/ChipTop/system/.../gemmini` 上下文，不是只含 PE array 的独立 Gemmini 顶层

当前 Gemmini 参数快照：

- `tileRows=1`、`tileColumns=1`、`meshRows=16`、`meshColumns=16`
- 软件头文件参数：`DIM=16`、`BANK_NUM=4`、`BANK_ROWS=4096`、`ACC_ROWS=1024`、`MAX_BYTES=64`
- 数据类型：`elem_t=int8_t`、`acc_t=int32_t`
- 容量与 bank：`sp_capacity=256 KiB`、`acc_capacity=64 KiB`、`sp_banks=4`、`acc_banks=2`
- DMA：`dma_maxbytes=64`、`dma_buswidth=128`
- 数据流：硬件默认 `Dataflow.BOTH`。当前 signoff workload 集合固定为 `tiled_matmul_os`、`tiled_matmul_ws`、`mvin_mvout`，分别覆盖 output-stationary GEMM、weight-stationary GEMM、memory/control movement 对照。

### 2.4 活动率与热输入导出

- [scripts/extract_vcd_activity.py](/home/lisihang/thermal_placement/scripts/extract_vcd_activity.py)
  从 VCD 提取信号与区域级活动率。
- [scripts/export_smoke_hotspot_inputs.py](/home/lisihang/thermal_placement/scripts/export_smoke_hotspot_inputs.py)
  从区域活动率生成最小 HotSpot `.flp` / `.ptrace`。
- [scripts/report_small_gemm_flow.py](/home/lisihang/thermal_placement/scripts/report_small_gemm_flow.py)
  把一次 small GEMM run 汇总成报告。

## 3. 历史上已跑通的最小链路

### 3.1 最小 smoke 链路

脚本：

- [scripts/run_thermal_smoke_flow.sh](/home/lisihang/thermal_placement/scripts/run_thermal_smoke_flow.sh)

历史上已验证通过的闭环：

```text
bare-metal compile
-> Verilator debug simulation
-> VCD dump
-> activity extraction
-> HotSpot input export
-> HotSpot steady-state run
```

迁移到当前计划时的意义：

- 它适合做阶段 1 的工具连通性检查
- 它不适合作为阶段 0–4 唯一研究 baseline，因为负载过小

### 3.2 small GEMM 链路

脚本：

- [scripts/run_small_gemm_thermal_flow.sh](/home/lisihang/thermal_placement/scripts/run_small_gemm_thermal_flow.sh)

历史上已验证：

- `small-gemm-start`
- `small-gemm-ok`
- 完整 VCD 导出
- 活动率 CSV 导出
- HotSpot steady-state 输出

迁移到当前计划时的意义：

- 它证明了真实 Gemmini GEMM 工作负载可以在本仓库里跑通
- 它是当前“持续高负载 GEMM baseline”选择时的重要参考样例
- 但它本身不必然就是新计划最终选定的 baseline

## 4. 可直接拿来回答阶段 0 问题的历史信息

以下内容可以作为新计划阶段 0 的输入参考：

- Gemmini 当前已知可跑配置：`GemminiRocketConfig`
- 历史目标边界曾聚焦：
  - `pe_array`
  - `controller`
  - `load_store_dma`
  - `scratchpad`
  - `accumulator`
- 历史活动率提取已使用 `hierarchy_map.yaml` 做 bucket 聚合
- 历史热代理链路是：
  `VCD -> activity CSV -> proxy power -> HotSpot`

这些都可以复用为当前阶段 0–1 的骨架，但需要按新计划改成：

- 主研究对象是“PE array + 控制 + 紧邻数据通路”
- ASAP7 标准单元实现是主线
- PACT 是主热仿真主线，HotSpot 只是粗对照
- 新产物必须进入 `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/`，旧 proxy 产物仅供参考

## 5. 需要显式修正的旧路线信息

旧归档里有几类内容不能直接照抄：

- 旧计划把 OpenROAD/HotSpot macro 级对比当成主线，而新计划主线是标准单元级热仿真
- 旧 `hierarchy_map.yaml`、旧活动率 CSV、旧导出 RTL、旧波形都只是历史样本，不应直接当作当前 active 输入
- 旧文档里的很多绝对路径指向归档前的 active 目录，现在如果要复用结果，应从 `archive/gemmini_thermal_validation_2026-04-23/` 读取

## 6. 当前建议的复用方式

推荐把旧 Gemmini 资料按下面方式复用：

1. 用本文件回答“仓库里有什么 Gemmini 流程脚本、哪些闭环曾跑通”。
2. 用 [tool_environment_inventory.md](/home/lisihang/thermal_placement/docs/tool_environment_inventory.md) 和 [gemmini_thermal_environment_setup.md](/home/lisihang/thermal_placement/docs/gemmini_thermal_environment_setup.md) 回答工具与环境问题。
3. 如果阶段 1 决定继续沿用 Gemmini 路线，重新生成新的 active RTL / hierarchy map / 波形 / 活动率。
4. 如果只是参考历史结果，去读归档目录，不要直接修改归档文件。
