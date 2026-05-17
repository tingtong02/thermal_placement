# Gemmini Config Notes

此前 Gemmini 热验证路线生成的 `hierarchy_map.yaml` 已归档到：

- [archive/gemmini_thermal_validation_2026-04-23/configs/gemmini/hierarchy_map.yaml](/home/lisihang/thermal_placement/archive/gemmini_thermal_validation_2026-04-23/configs/gemmini/hierarchy_map.yaml)

之所以从 active 路径移走，是因为旧开发计划已经冻结，避免新的开发路线继续沿用一份历史生成的层级映射。

如果后续仍需要 Gemmini 活动率提取映射，请重新运行：

```bash
source tools/env_gemmini_thermal.sh
scripts/run_gemmini_rtl_generation.sh
```

该脚本会重新生成：

- `configs/gemmini/hierarchy_map.yaml`
- `reports/notes/gemmini_module_inventory.md`
- `rtl_exports/generated-verilog/<CONFIG>/...`
