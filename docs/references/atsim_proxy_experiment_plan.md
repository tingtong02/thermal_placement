# ATSim v1 Proxy Experiment Plan

更新时间：2026-05-03

上下文恢复要求：如果本任务执行中发生上下文压缩、记忆丢失、长时间中断后恢复，继续前必须重新阅读本文件，以及 `AGENTS.md`、`docs/phase0tophase4_signoff_multiworkload_plan.md`、`docs/README.md`、`docs/atsim_tool_guide.md`。本要求仅适用于本次 ATSim proxy experiment；不要因此修改 `AGENTS.md`。

## 任务边界

用户要求在 `thermal/` 下新建目录，用 ATSim3D v1 对旧 proxy thermal 结果做一次重跑。ATSim3.5D v2 的完整输入 schema 尚未确认，本任务不使用 v2。

本任务使用旧 `stage4_tiled_matmul_os_baseline` proxy 数据，定位为独立运行记录，不改变当前 active Stage 0-4 signoff 计划，不把旧 proxy 结果表述为当前 signoff 验收结果。

## 输出目录

主目录：

```text
thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/
```

计划子目录：

```text
inputs/   # 由旧 proxy 数据转换出的 ATSim3D v1 输入
logs/     # ATSim3D v1 stdout/stderr 与检查日志
results/  # 复制或汇总 ATSim3D v1 .res 输出与统计
scripts/  # 本次转换和分析脚本
```

## 输入来源

- `thermal/pact/stage4_tiled_matmul_os_baseline/flp_stage4_tiled_matmul_os_baseline.csv`
- `thermal/pact/stage4_tiled_matmul_os_baseline/ptrace_stage4_tiled_matmul_os_baseline_steady.csv`
- `thermal/pact/stage4_tiled_matmul_os_baseline/config_stage4_tiled_matmul_os_baseline.config`
- `power/stage3_tiled_matmul_os_baseline_metadata.json`
- `third_party/ATSim3D_pub/{2DIC,Mono3D,TSV3D}` 示例结果，用于说明三类示例输出差异

## 执行步骤

1. 检查 ATSim3D v1 wrapper、旧 proxy 输入和示例结果是否存在。
2. 将旧 PACT proxy floorplan/power 转成 ATSim3D v1 2D-style 单 active Si layer 输入：
   - floorplan 保留 `UnitName,X,Y,Length (m),Width (m),ConfigFile,Label`。
   - steady power 从 `UnitName,Power` 转成 `UnitName,Power_dyn,Power_leak`，其中 `Power_dyn=Power`、`Power_leak=0`。
   - lcf 使用一个 `Si` active layer，厚度沿用 Stage 4 PACT 的 `0.0001 m`。
   - config 使用 PACT Si thermal resistivity 的倒数作为 ATSim conductivity，ambient/init 使用 `318.15 K`。
3. 先运行 ATSim3D v1 输入解析/求解 smoke；如果失败，记录错误和下一个最小修复，不继续伪造输出。
4. 如果成功，统计 `.res` 温度结果：形状、min/max/mean、热点坐标和温度范围。
5. 对 ATSim3D v1 自带 2DIC、Mono3D、TSV3D 已生成 `.res` 做统计，说明三类结构和结果差异。
6. 在本目录写 `README.md` 和详细结果文档，必要时同步 `docs/README.md` 或 `docs/atsim_tool_guide.md`。

## 预期注意事项

- ATSim3D v1 是 steady-state 工具；本次只跑 steady proxy peak，不跑 transient。
- 旧 proxy power 是 normalized proxy power，不是 signoff power。
- ATSim3D v1 的输入模型不同于 PACT，本次结果用于工具连通性和同一 proxy 数据的再仿真记录。

## 完成状态

2026-05-03 已完成本计划中的 ATSim3D v1 proxy rerun。

- 运行目录：`thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/`
- 运行记录：`thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/ATTEMPTS.md`
- 结果说明：`thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/README.md`
- 详细分析：`thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/RESULTS.md`
- ATSim3D v1 exit status：`0`
- v2：未运行

## Artifacts completion update

2026-05-03 已补充 Stage4-style artifacts：

- artifacts 目录：`artifacts/stage4/atsim3d_v1_proxy/`
- artifacts 说明：`artifacts/stage4/atsim3d_v1_proxy/README.md`
- 生成脚本：`thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/scripts/generate_atsim_stage4_artifacts.py`
- 生成日志：`thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/logs/generate_stage4_artifacts.log`
- 更新后的详细分析：`thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/RESULTS.md`
