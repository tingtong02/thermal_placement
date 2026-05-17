# Gemmini Thermal Validation Archive

归档日期：2026-04-23

## 归档原因

本目录冻结的是旧版 `docs/gemmini_thermal_validation_plan.md` 所驱动的一轮 Gemmini 热验证开发内容。由于后续开发路线已经变更，这批阶段性计划、手工总结、生成 RTL、仿真波形、活动率 CSV、HotSpot/PACT 输出和测试二进制不再放在仓库主干中继续演进，但需要保留为历史参考和复盘材料。

## 归档范围

- `configs/gemmini/hierarchy_map.yaml` 的旧版本
- `rtl_exports/generated-verilog/GemminiRocketConfig/` 下的导出 RTL 与 hierarchy JSON
- `sim/` 下的旧二进制、日志、波形、活动率 CSV
- `thermal/` 下的旧 `.flp`、`.ptrace`、`.ttrace`
- `reports/` 下的旧 smoke、small GEMM、PACT 和模块清点结果

## 与文档归档的对应关系

对应的说明文档在：

- [docs/archive/gemmini_thermal_validation_2026-04-23](/home/lisihang/thermal_placement/docs/archive/gemmini_thermal_validation_2026-04-23)

这些归档文档按“历史快照”保留，正文中的部分绝对路径链接仍反映归档前的活跃路径；需要对照本 archive 目录理解，不再把它们当成当前主干布局。

## 复用建议

- 如果只是参考旧结果，直接读取本归档目录即可。
- 如果后续还要复用旧 Gemmini 流程，请从主仓库脚本重新生成 active 产物，不要在 archive 目录上继续覆盖。
- 当前主仓库保留的重点是工具环境、安装记录和问题日志，而不是这轮旧路线的结果文件。
