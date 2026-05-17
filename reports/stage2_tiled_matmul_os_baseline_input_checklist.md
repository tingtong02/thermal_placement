# Stage 2 Tiled Matmul OS Baseline Input Checklist

> Legacy note: this file documents the old OpenROAD/reduced-ASAP7 proxy route. It is not the current active Stage 2 handoff and must not be read as the current acceptance standard. The current accepted Stage 2 folder is:
>
> `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/`
>
> Current quality label: `PG-open / DRC-open / routed-SDF-waived thermal proxy`. The `__signoff` text in path names is historical and should not be interpreted as signoff quality.


## 目标

本清单只服务当前 active route 的 Stage 2：
将 Gemmini 阵列相关逻辑收缩到 ASAP7 reduced 标准单元实现输入，不扩展到全 SoC。

## 已确认可直接作为 Stage 2 输入的文件

### 1. Phase 0 / Stage 1 结论文件

- [stage0_tiled_matmul_os_baseline_closure.md](/home/lisihang/thermal_placement/reports/stage0_tiled_matmul_os_baseline_closure.md)
- [stage1_tiled_matmul_os_baseline_stage_report.md](/home/lisihang/thermal_placement/reports/stage1_tiled_matmul_os_baseline_stage_report.md)
- [stage1_tiled_matmul_os_baseline_activity_summary.md](/home/lisihang/thermal_placement/reports/stage1_tiled_matmul_os_baseline_activity_summary.md)
- [stage1_tiled_matmul_os_baseline_windows.md](/home/lisihang/thermal_placement/reports/stage1_tiled_matmul_os_baseline_windows.md)

这些文件回答了 Stage 2 之前必须固定的事：

- workload 只有一个：`tiled_matmul_os`
- dataflow 固定：`output-stationary`
- Stage 1 已通过
- 后续实现目标不是全 SoC，而是 Gemmini PE array + 控制 + 邻近 datapath

### 2. Stage 1 原始活动输入

- waveform:
  - [tiled_matmul_os VCD](/home/lisihang/thermal_placement/sim/waves/GemminiRocketConfig/tiled_matmul_os-baremetal.stage1_tiled_matmul_os_baseline_20260423.vcd)
- activity CSV:
  - [signal activity](/home/lisihang/thermal_placement/sim/activity/stage1_tiled_matmul_os_baseline_20260423_signal_activity.csv)
  - [region activity](/home/lisihang/thermal_placement/sim/activity/stage1_tiled_matmul_os_baseline_20260423_region_activity.csv)
  - [window activity](/home/lisihang/thermal_placement/sim/activity/stage1_tiled_matmul_os_baseline_20260423_window_activity.csv)
- manifest:
  - [stage1_tiled_matmul_os_baseline_manifest.txt](/home/lisihang/thermal_placement/reports/stage1_tiled_matmul_os_baseline_manifest.txt)

这些文件在 Stage 2 的作用：

- 记录当前 baseline 的唯一活动来源
- 给 Stage 3 的窗口和后续 power mapping 保留锚点
- 在缩实现边界时回看哪些 Gemmini bucket 真正有活动

### 3. RTL / hierarchy 边界输入

- `configs/gemmini/hierarchy_map.yaml`
- [notes/gemmini_module_inventory.md](/home/lisihang/thermal_placement/reports/notes/gemmini_module_inventory.md)
- `rtl_exports/generated-verilog/GemminiRocketConfig/`

其中最关键的是：

- `pe_array`
- `controller`
- `load_store_dma`
- `scratchpad`
- `gemmini_other`

Stage 2 需要先据此确定一个“可综合、但不扩展到全 SoC”的最小实现 top。

### 4. 工艺和实现环境输入

- ASAP7 reduced techlib
- OpenROAD / ORFS
- OpenSTA
- 环境入口：`source tools/env_gemmini_thermal.sh`

对应参考文档：

- [docs/tool_environment_inventory.md](/home/lisihang/thermal_placement/docs/tool_environment_inventory.md)
- [docs/gemmini_thermal_environment_setup.md](/home/lisihang/thermal_placement/docs/gemmini_thermal_environment_setup.md)
- [docs/phase0tophase4_plan.md](/home/lisihang/thermal_placement/docs/phase0tophase4_plan.md)

## Stage 2 开始前必须先检查的事项

### A. RTL 导出是否完整

先检查：

```bash
find rtl_exports/generated-verilog/GemminiRocketConfig -maxdepth 2 -type f | head
```

如果不完整，先补跑：

```bash
source tools/env_gemmini_thermal.sh
scripts/run_gemmini_rtl_generation.sh
```

### B. hierarchy map 是否与当前 RTL 对齐

先检查：

```bash
sed -n '1,220p' configs/gemmini/hierarchy_map.yaml
sed -n '1,120p' reports/notes/gemmini_module_inventory.md
```

如果 RTL 重导出后层级有变化，必须同步刷新 map / inventory，再进入 Stage 2。

### C. Stage 2 top 是否已经明确

当前还不能直接开跑 ORFS，先要回答：

- 最小实现 top 是什么
- 它包含哪些 Gemmini 子模块
- 哪些 scratchpad / accumulator 阵列要 blackbox 或只保留上下文
- 如何避免退化成整颗 `GemminiRocketConfig` SoC 实现

### D. 输出目录是否固定

Stage 2 主输出目录按计划应为：

- `physical/stage2_tiled_matmul_os_baseline_asap7/`

在运行前先把 Stage 2 config、脚本入口和输出树固定下来。

## 当前状态说明

本文件是进入 Stage 2 前的输入检查记录。当前 Stage 2 已经完成 proxy closeout；最新状态以以下文件为准：

- `reports/stage2_tiled_matmul_os_baseline_impl_manifest.md`
- `reports/stage2_tiled_matmul_os_baseline_impl_summary.md`
- `reports/stage3_tiled_matmul_os_baseline_preflight_plan.md`

## 已完成的 Stage 2 路径摘要

1. 默认 adder mapping 路径曾卡在 `EXTRACT_FA` 附近。
2. `FLOW_VARIANT=noaddermap` 路径生成 mapped netlist，并推进到 floorplan/place/CTS/route。
3. `PIN_THICKNESS=0.096` memory macro LEF 清除了 full-design memory `pin_access` blocker。
4. `PLACE_PINS_ARGS='-min_distance 0.54'` 清除了此前 left-boundary global-route congestion。
5. capped detail route 生成 `5_route.odb`，finish/export 生成 `6_final.def`、`6_final.v`、`6_final.sdc`、`6_final.spef`、`6_final.odb`、`6_final.gds`。
6. 当前验收等级是 `proxy / non-signoff`，不是 strict P&R。

## 当前 Stage 3 前置关注点

- 当前 `steady_high_load` 仍是 coarse marker window，Stage 3 正式功耗前必须补 target-scoped Gemmini window refinement。
- Stage 2 无 SDF，Stage 3 使用 `6_final.v + 6_final.def + 6_final.sdc + 6_final.spef` 作为 proxy timing/parasitic package。
- `6_report.log` 和 `6_report.json` 是 ORFS final-report artifacts，实际在 logs tree；不需要移动。
- VDD/VSS IR 数值不能作为功耗或热输入。

## 多线程使用建议

- ORFS/后端单 baseline：`MAKE_JOBS=1`，单任务 `NUM_CORES` 可在 smoke 后最高用到 `128`。
- 多个独立任务：`MAKE_JOBS` 最大 `4`；`MAKE_JOBS=2` 时每个任务 `NUM_CORES<=128`，`MAKE_JOBS=3/4` 时每个任务 `NUM_CORES<=64`。
- Stage 3 大 VCD/window refinement：优先用 parser 或 windowed/scoped extractor 的 workers；不要重跑仿真来解决报告问题。
- Verilator 仿真线程数不能固定写成 `128`；只有在确实需要重跑仿真时，才重新做最小 smoke 选择 `VERILATOR_THREADS`。
