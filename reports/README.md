# Reports Index

本目录保存当前 active route 的阶段报告、manifest 和辅助说明。

## 当前主线文件

### Stage 0

- [stage0_tiled_matmul_os_baseline_closure.md](/home/lisihang/thermal_placement/reports/stage0_tiled_matmul_os_baseline_closure.md)
  Phase 0 收口结果，固定 baseline、边界和阶段输入输出。

### Stage 1

- [stage1_tiled_matmul_os_baseline_manifest.txt](/home/lisihang/thermal_placement/reports/stage1_tiled_matmul_os_baseline_manifest.txt)
  当前 baseline 的主运行清单，记录 waveform、log、activity CSV 和报告路径。
- [stage1_tiled_matmul_os_baseline_windows.md](/home/lisihang/thermal_placement/reports/stage1_tiled_matmul_os_baseline_windows.md)
  Stage 1 冷启动、CPU reference、steady high-load 窗口说明。
- [stage1_tiled_matmul_os_baseline_activity_summary.md](/home/lisihang/thermal_placement/reports/stage1_tiled_matmul_os_baseline_activity_summary.md)
  Stage 1 活动摘要，包含 Gemmini 目标区域高亮。
- [stage1_tiled_matmul_os_baseline_stage_report.md](/home/lisihang/thermal_placement/reports/stage1_tiled_matmul_os_baseline_stage_report.md)
  按计划模板整理的 Stage 1 验收报告。

### Stage 2

- [stage2_cadence_asap7_phase2_handoff_20260513.md](/home/lisihang/thermal_placement/reports/stage2_cadence_asap7_phase2_handoff_20260513.md)
  Current Cadence/full-ASAP7 Stage 2 handoff report. It selects r28 as the accepted degraded `PG-open / DRC-open / routed-SDF-waived thermal proxy` implementation for Stage 3/4. Artifact folder: `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/physical/gemmini_mesh16x16_tile1x1_dim16_asap7sc7p5t28_fake_sram_200mhz_phase2_full_20260513_r28_export_from_routing_sdf_waived/`.
- [stage2_tiled_matmul_os_baseline_input_checklist.md](/home/lisihang/thermal_placement/reports/stage2_tiled_matmul_os_baseline_input_checklist.md)
  Legacy Stage 2 input checklist from the earlier OpenROAD/proxy route; current Cadence status is in the 2026-05-13 handoff report.
- [stage2_tiled_matmul_os_baseline_impl_manifest.md](/home/lisihang/thermal_placement/reports/stage2_tiled_matmul_os_baseline_impl_manifest.md)
  Legacy OpenROAD/proxy Stage 2 manifest; do not use as active Cadence handoff.
- [stage2_tiled_matmul_os_baseline_impl_summary.md](/home/lisihang/thermal_placement/reports/stage2_tiled_matmul_os_baseline_impl_summary.md)
  Legacy OpenROAD/proxy Stage 2 summary; do not use as active Cadence handoff.

### Stage 3

- [stage3_tiled_matmul_os_baseline_preflight_plan.md](/home/lisihang/thermal_placement/reports/stage3_tiled_matmul_os_baseline_preflight_plan.md)
  Phase 3 正式启动前计划和执行中方法修正记录。
- [stage1_tiled_matmul_os_baseline_target_windows.md](/home/lisihang/thermal_placement/reports/stage1_tiled_matmul_os_baseline_target_windows.md)
  Phase 3 target-scoped Gemmini 窗口精化报告。
- [stage3_tiled_matmul_os_baseline_stage_report.md](/home/lisihang/thermal_placement/reports/stage3_tiled_matmul_os_baseline_stage_report.md)
  Phase 3 验收报告和 Stage 4 handoff 状态。
- [stage3_tiled_matmul_os_baseline_power_trace_method.md](/home/lisihang/thermal_placement/reports/stage3_tiled_matmul_os_baseline_power_trace_method.md)
  Phase 3 grid power / transient ptrace 构建方法和限制。
- [stage3_tiled_matmul_os_baseline_activity_mapping_manifest.md](/home/lisihang/thermal_placement/reports/stage3_tiled_matmul_os_baseline_activity_mapping_manifest.md)
  RTL activity 到 DEF/grid region 的映射规则、统计和 fallback 比例。
- [stage3_tiled_matmul_os_baseline_hotspot_traceback.md](/home/lisihang/thermal_placement/reports/stage3_tiled_matmul_os_baseline_hotspot_traceback.md)
  Top proxy-power grid bin 到实例/module 的反查报告。

### Stage 4

- [stage4_tiled_matmul_os_baseline_preflight_plan.md](/home/lisihang/thermal_placement/reports/stage4_tiled_matmul_os_baseline_preflight_plan.md)
  Phase 4 正式执行前计划：Phase 3 验收 handoff、PACT/HotSpot 工具 smoke、线程能力边界、输入/输出路径和开发步骤。
- [stage4_tiled_matmul_os_baseline_pact_thermal_report.md](/home/lisihang/thermal_placement/reports/stage4_tiled_matmul_os_baseline_pact_thermal_report.md)
  Phase 4 PACT 主线报告：steady SuperLU、transient serial Xyce、兼容修复和温度范围。
- [stage4_tiled_matmul_os_baseline_hotspot_report.md](/home/lisihang/thermal_placement/reports/stage4_tiled_matmul_os_baseline_hotspot_report.md)
  Phase 4 HotSpot 粗对照报告：五个 coarse block、ttrace 结果和趋势说明。
- [stage4_tiled_matmul_os_baseline_summary.md](/home/lisihang/thermal_placement/reports/stage4_tiled_matmul_os_baseline_summary.md)
  Phase 4 总结报告：阶段验收、热点位置、温升行为、PACT/HotSpot 对照和 caveats。
- [stage4_tiled_matmul_os_baseline_standard_cell_context.md](/home/lisihang/thermal_placement/reports/stage4_tiled_matmul_os_baseline_standard_cell_context.md)
  Phase 4 标准单元上下文展示报告：把 Stage 3 instance-grid map、region proxy power 和 PACT steady layer0 温度关联，生成 `artifacts/stage4/standard_cell_context/` 下的 SVG/CSV 展示产物。

## 辅助与参考文件

- [notes/gemmini_module_inventory.md](/home/lisihang/thermal_placement/reports/notes/gemmini_module_inventory.md)
  `inspect_gemmini_hierarchy.py` 生成的模块清单和 bucket 概览，用于缩 Stage 2 实现边界。
- [notes/stage3_fidelity_recovery_roadmap.md](/home/lisihang/thermal_placement/reports/notes/stage3_fidelity_recovery_roadmap.md)
  后续严谨标准单元级功耗/活动波形流程参考：Phase 2 recovery、Phase 2.5 gate activity、Phase 3B SPEF/SAIF-based power、Phase 4 输入等级。
- [notes/phase2_optional_sweep_notes.md](/home/lisihang/thermal_placement/reports/notes/phase2_optional_sweep_notes.md)
  后续可选 Phase 2 sweep 参数记录：200 MHz 目标、外层并发假设、detail route 8 轮上限、当前 proxy 跳过项和效率建议；不是强制开发计划。
- [stage1_mvin_mvout_baseline_manifest.txt](/home/lisihang/thermal_placement/reports/stage1_mvin_mvout_baseline_manifest.txt)
  官方 `mvin_mvout` threading smoke 的 manifest。它不是当前 GEMM baseline，只用于辅助核对 simulator / threading / trace 成本。

## 目录约定

- `reports/` 根目录：当前主线阶段报告和 manifest。
- `reports/notes/`：模块盘点、方法补充、临时但有保留价值的技术说明。
- `reports/figures/`、`reports/tables/`：后续 Stage 3/4 图表和表格输出预留目录。
- `reports/smoke/`、`reports/pact_validation/`：后续若需要单独保留 smoke 或 PACT 校验报告，再放到对应子目录；当前为空。

## 当前建议阅读顺序

1. `stage0_tiled_matmul_os_baseline_closure.md`
2. `stage1_tiled_matmul_os_baseline_stage_report.md`
3. `stage1_tiled_matmul_os_baseline_activity_summary.md`
4. `stage1_tiled_matmul_os_baseline_windows.md`
5. `stage2_cadence_asap7_phase2_handoff_20260513.md`
6. `stage2_tiled_matmul_os_baseline_input_checklist.md`
7. `stage2_tiled_matmul_os_baseline_impl_manifest.md`
8. `stage2_tiled_matmul_os_baseline_impl_summary.md`
9. `stage3_tiled_matmul_os_baseline_preflight_plan.md`
10. `stage1_tiled_matmul_os_baseline_target_windows.md`
11. `stage3_tiled_matmul_os_baseline_stage_report.md`
12. `stage3_tiled_matmul_os_baseline_power_trace_method.md`
13. `stage3_tiled_matmul_os_baseline_activity_mapping_manifest.md`
14. `stage4_tiled_matmul_os_baseline_preflight_plan.md`
15. `stage4_tiled_matmul_os_baseline_pact_thermal_report.md`
16. `stage4_tiled_matmul_os_baseline_hotspot_report.md`
17. `stage4_tiled_matmul_os_baseline_summary.md`
18. `stage4_tiled_matmul_os_baseline_standard_cell_context.md`
19. `notes/gemmini_module_inventory.md`
20. `notes/stage3_fidelity_recovery_roadmap.md`
21. `notes/phase2_optional_sweep_notes.md`
