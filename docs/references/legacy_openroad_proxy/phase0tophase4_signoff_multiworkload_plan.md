# Gemmini 16x16 多 workload 高可信 Stage 0-4 Signoff 计划

## 0. 文档定位

本文件是当前 active 执行目标，用于替代旧的 `docs/phase0tophase4_plan.md`。旧计划保留为历史参考，不再约束新开发。

当前目标是：

> 针对一个固定 Gemmini 硬件配置，完成三个固定 workload 的 Stage 0-4 高可信闭环：
> Stage 0 研究定义 -> Stage 1 RTL 活动波形 -> Stage 2 ASAP7 标准单元实现 -> Stage 3 grid 级功耗波形 -> Stage 4 PACT 主线热仿真 + ATSim3D v1 独立热仿真 + HotSpot 粗对照。

本轮结果目标是 `project-signoff/high-confidence`，不是 foundry signoff。原因是本仓库使用 reduced ASAP7 techlib、OpenROAD-flow-scripts、PACT/HotSpot 等研究工具链，不具备商业 STA/DRC/LVS/IR/EM signoff 的完整条件。本文中的 signoff 表示：流程不使用 proxy/fallback 结果，不跳过完整阶段，不使用已知质量降低开关冒充正式结果，并且每个阶段都有可复现输入、输出、日志、报告和失败停止记录。

## 1. 固定硬件配置

本轮只允许一个 Gemmini 硬件配置：当前仓库默认 `GemminiRocketConfig` + `DefaultGemminiConfig`。

已确认的配置字段：

| 字段 | 值 | 证据 |
| --- | --- | --- |
| Chipyard config | `GemminiRocketConfig` | `third_party/chipyard/generators/gemmini/chipyard/GemminiConfigs.scala` |
| Gemmini config | `DefaultGemminiConfig` | `third_party/chipyard/generators/gemmini/src/main/scala/gemmini/Configs.scala` |
| `tileRows` | 1 | 同上 |
| `tileColumns` | 1 | 同上 |
| `meshRows` | 16 | 同上 |
| `meshColumns` | 16 | 同上 |
| effective `DIM` | 16 | `software/gemmini-rocc-tests/include/gemmini_params.h` |
| input / weight type | int8 | `Configs.scala`, `gemmini_params.h` |
| accumulator type | int32 | 同上 |
| spatial output type | int20 | `Configs.scala` |
| dataflow support | `Dataflow.BOTH` | `Configs.scala` |
| scratchpad capacity | 256 KiB | `Configs.scala` |
| accumulator capacity | 64 KiB | `Configs.scala` |
| scratchpad banks | 4 | `Configs.scala`, `gemmini_params.h` |
| accumulator banks | 2 | `Configs.scala` |
| DMA max bytes | 64 | `Configs.scala`, `gemmini_params.h` |
| system bus width | 128-bit | `GemminiConfigs.scala` |

不得在本轮中切换到 8x8、32x32、FP32、LeanGemmini、custom Gemmini config 或多配置 sweep。若后续确实需要新配置，必须先复制本计划模板，换新 run 根目录，并重新执行 Stage 0-4。

## 2. 固定 workload 集合

本轮固定三个 workload，不再增加第四个 workload，也不把 workload 规模缩小来换取运行成功。

| workload | 类型 | 默认尺寸 / 行为 | 本轮用途 |
| --- | --- | --- | --- |
| `tiled_matmul_os` | output-stationary GEMM | `MAT_DIM_I=64`, `MAT_DIM_K=64`, `MAT_DIM_J=64`, `CHECK_RESULT=1`, `NO_BIAS=1` | PE 阵列持续高负载 baseline |
| `tiled_matmul_ws` | weight-stationary GEMM | `MAT_DIM_I=64`, `MAT_DIM_K=64`, `MAT_DIM_J=64`, `CHECK_RESULT=1`, `NO_BIAS=1` | 同规模 GEMM 的 dataflow 对照 |
| `mvin_mvout` | memory/control movement | `N=8`，移动 8 个 `DIM x DIM` 矩阵；本配置下为 8 个 16x16 矩阵 | load/store、DMA、scratchpad 周边和控制路径对照 |

`mvin_mvout` 不是 PE 高负载 GEMM，不得在报告中称为计算高负载 workload。它的作用是作为数据搬运/控制活动对照，帮助区分 PE compute 热图与周边数据通路热图。

后续候选但本轮不执行：`conv`, `conv_rect`, `conv_stride`, `conv_dw`, `tiled_matmul_ws_At`, `tiled_matmul_ws_Bt`, `tiled_matmul_ws_layernorm`, `tiled_matmul_ws_softmax`, `tiled_matmul_ws_perf`, `conv_perf`。这些只能在用户明确扩展计划后进入新一轮 run。

## 3. Run 命名和目录规范

### 3.1 当前 run 根目录

当前配置的所有新开发结果集中在：

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/
```

该名字只承载最关键的硬件结构和流程质量信息。dtype、容量、dataflow、workload、工具版本、输入输出路径必须写入 run 根目录 `README.md` 和 `config/run_manifest.json`，不要继续把目录名做成长串。

### 3.2 通用命名模板

未来相同流程的新配置必须使用同类模板：

```text
runs/<chipyard_config>__mesh<meshRows>x<meshColumns>_tile<tileRows>x<tileColumns>_dim<DIM>__<quality>/
```

示例：

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/
runs/CustomGemminiRocketConfig__mesh32x32_tile1x1_dim32__signoff/
runs/LeanGemminiRocketConfig__mesh8x8_tile1x1_dim8__exploratory/
```

### 3.3 必需目录结构

```text
runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/
  README.md
  config/
    run_manifest.json
    gemmini_config_snapshot.md
    workload_manifest.md
    environment_manifest.md
  rtl/
    generated/
    hierarchy/
    logs/
  physical/
    config/
    logs/
    reports/
    results/
  timing/
    reports/
  workloads/
    tiled_matmul_os/
    tiled_matmul_ws/
    mvin_mvout/
  sim/
    tiled_matmul_os/
    tiled_matmul_ws/
    mvin_mvout/
  activity/
    tiled_matmul_os/
    tiled_matmul_ws/
    mvin_mvout/
  gate_activity/
    tiled_matmul_os/
    tiled_matmul_ws/
    mvin_mvout/
  power/
    tiled_matmul_os/
    tiled_matmul_ws/
    mvin_mvout/
  thermal/
    tiled_matmul_os/
    tiled_matmul_ws/
    mvin_mvout/
  reports/
    config/
    tiled_matmul_os/
    tiled_matmul_ws/
    mvin_mvout/
  artifacts/
    tiled_matmul_os/
    tiled_matmul_ws/
    mvin_mvout/
```

综合、布局、布线、静态时序等与 workload 无关或可复用的产物必须放在配置根目录下的 `physical/`、`timing/`、`rtl/`、`config/` 中。仿真、activity、gate activity、power、thermal、workload-specific reports 必须按 workload 分目录。

### 3.4 Run README 必填内容

每个 run 根目录必须有 `README.md`，至少包含：

- run 目标和 signoff 级别定义
- Chipyard/Gemmini 配置名
- `meshRows`, `meshColumns`, `tileRows`, `tileColumns`, `DIM`
- dtype、scratchpad、accumulator、bank、DMA、dataflow 字段
- 三个 workload 的来源、尺寸、检查方式和角色
- Stage 0-4 输入、输出、命令入口和报告路径
- Stage 3/4 grid 坐标约定：所有主产物使用 DEF physical grid，`grid_y=0` 在 die bottom，`grid_y` 向上增加
- 工具版本、环境入口和关键环境变量
- 接受标准、失败停止条件和已知限制

## 4. Stage 0-4 执行目标

### 4.1 Stage 0: 研究定义和输入冻结

Stage 0 必须输出：

- run 根目录和 `README.md`
- `config/run_manifest.json`
- `config/gemmini_config_snapshot.md`
- `config/workload_manifest.md`
- `config/environment_manifest.md`
- Stage 1-4 预期输入/输出清单

Stage 0 不得运行大规模 VCD、综合、P&R 或热仿真。

### 4.2 Stage 1: RTL activity waveform

对三个 workload 分别执行完整 RTL 仿真和活动采集：

- `tiled_matmul_os`
- `tiled_matmul_ws`
- `mvin_mvout`

要求：

- 每个 workload 必须从完整 functional run 开始，不复用旧 proxy 结果作为当前验收。
- 每个 workload 必须记录 binary、stdout/stderr、VCD、activity CSV、window report、functional pass/fail。
- VCD 仍是本轮主格式。只有在文档更新并说明替代格式完整可消费后，才可增加 SAIF/FST 等辅助格式；不得用格式切换掩盖缺失的活动证据。
- 若任一 workload functional run 失败，立即停止并汇报，不继续后续 workload 或 stage。

### 4.3 Stage 2: ASAP7 标准单元实现

Stage 2 针对固定硬件配置只做一次可复用物理实现，输出供三个 workload 共用。

本轮 signoff 禁止使用旧 proxy 路线中的质量降低结果作为正式输入，包括但不限于：

- 旧 `noaddermap` proxy 结果
- `REMOVE_ABC_BUFFERS=1` 作为质量降低兜底
- `GPL_TIMING_DRIVEN=0` 作为质量降低兜底
- `SKIP_CTS_REPAIR_TIMING=1` 作为质量降低兜底
- `SKIP_REPORT_METRICS=1` 作为质量降低兜底
- capped detailed-route residual DRC 结果冒充 clean signoff
- 缺失关键报告但继续下游 signoff

允许使用 OpenROAD/ORFS 和 reduced ASAP7 完成 project-level high-confidence 实现，但必须把 reduced techlib 的限制写入报告。若 routed design 仍存在 DRC、缺失 SDF、缺失 SPEF、缺失 final report、或使用任何 proxy/fallback knob，则不得进入 Stage 3 signoff；必须停止并汇报。

Stage 2 必须输出至少：

- gate-level netlist
- DEF
- SPEF
- SDF 或明确说明当前工具链无法生成且用户重新确认是否降低目标；默认不接受无 SDF 继续 signoff
- ODB/GDS 或等价物理检查输入
- timing report
- DRC/global-route/detail-route/final report
- cell/area/utilization/placement/routing 统计
- Stage 2 signoff report

### 4.4 Stage 3: grid 级功耗波形

Stage 3 对三个 workload 分别生成 workload-specific power trace，复用同一个 Stage 2 physical implementation。

每个 workload 必须输出：

- activity-to-netlist/instance mapping manifest
- gate or mapped activity evidence
- instance-to-grid map
- grid power CSV
- transient power trace
- top-N power instance report
- top-N toggle/activity report
- region power summary
- method report

禁止用固定 1W proxy normalization 作为正式 signoff 功耗结果。若需要归一化用于可视化，只能作为附加视图，不能替代物理/活动驱动的 power trace。

### 4.5 Stage 4: PACT + ATSim3D v1 thermal simulation + HotSpot coarse comparison

Stage 4 对三个 workload 分别执行：

- PACT steady thermal simulation
- PACT transient thermal simulation, if the Stage 3 transient power trace is available
- ATSim3D v1 steady thermal simulation, using inputs converted from the same Stage 3 physical power grid and die/floorplan geometry
- HotSpot coarse comparison
- heatmap/curve/table/report generation

PACT 是主线 transient/steady 热仿真；ATSim3D v1 是必须执行的独立 steady thermal solver 对照；HotSpot 只能作为 coarse comparison，不能替代 PACT 或 ATSim3D v1。ATSim3.5D v2 `ATSim3_5D` 在 XML/config schema 未由本项目验证前不纳入强制 Stage 4 验收。

Stage 4 的统一坐标标准必须沿用 Stage 3/DEF 的事实物理分布：所有主 thermal grid、rank、heatmap、standard-cell overlay 和跨工具对比都必须使用 DEF physical coordinates，`grid_y=0` 是 die bottom，`grid_y` 向上增加。若 PACT 输出文件的 raw row order 与该物理坐标相反，后处理必须转换为：

```text
physical_grid_y = grid - 1 - pact_raw_row_y
```

PACT raw row-order 文件只能作为审计产物保留，文件名必须带 `_pact_raw_order` 或等价明确后缀。不得把 raw PACT row index 报告为物理 `grid_y`，也不得用 raw-order PACT 图与 Stage 3 标准单元分布、ATSim 或其它 physical-grid 产物做主结论。ATSim3D v1 的主对比也必须下采样或聚合到同一 DEF physical grid 后再与 PACT、Stage 3 standard-cell context 对齐。

图表产物的可查看性也是 Stage 4 artifact 要求：若生成 SVG 矢量图，必须同时生成同 basename 的 PNG companion，便于 VS Code、远程环境和报告快速预览。SVG 可保留用于矢量编辑或论文排版，PNG 是日常检查入口。

每个 workload 必须输出：

- PACT input LCF/config/modelParams
- PACT steady result
- PACT transient result或明确失败证据
- PACT coordinate manifest：说明主产物坐标约定、PACT raw row-order 是否需要转换、转换公式和 raw/fixed hotspot 位置
- 修复后的 PACT physical-coordinate grid/rank/heatmap 主产物，以及 raw row-order audit copy
- Standard-cell physical context overlay：把 Stage 3 placed-instance grid 分布、proxy power/density 和修复后的 PACT 温度放在同一 DEF physical grid 上检查
- ATSim3D v1 input LCF/config/simparams/floorplan/power/manifest
- ATSim3D v1 `.res` temperature result for the active layer, plus downsampled DEF physical-coordinate grid/rank/heatmap
- ATSim3D v1 vs corrected PACT physical-grid comparison table/heatmap；raw-order PACT comparison may exist only as diagnostic
- ATSim standard-cell context note：ATSim `.res` contains temperature samples, not standard-cell instance records; any standard-cell interpretation must join the ATSim physical grid with the Stage 3 placed instance grid map
- HotSpot flp/ptrace/ttrace
- thermal summary report
- heatmap/curve artifact；若输出 SVG，则必须同时输出同 basename PNG

## 5. 失败停止规则

本轮不做逐步恢复，不走 proxy fallback，不跳过失败阶段继续拼完整结果。

若任一阶段出现以下情况，必须立即停止并向用户汇报：

- 依赖缺失或工具不可用
- workload functional check 失败
- Stage 2 无法在无 proxy knob 条件下完成必要物理输出
- route/DRC/timing/final report 质量不足以支撑 project-signoff/high-confidence
- Stage 3 无法从当前 activity 与物理实现生成可信 power trace
- Stage 4 PACT、ATSim3D v1 或 HotSpot 输入不完整
- Stage 4 ATSim3D v1 run 失败、缺失 `.res`，或 ATSim 输出无法追溯到 DEF physical grid
- Stage 4 thermal grid 坐标无法追溯到 DEF physical grid，或把 PACT raw row-order 坐标当作物理坐标报告
- 任何结果需要从旧 proxy 输出继承才能继续

停止后必须先更新相关 active 文档、报告或 issue log，记录命令、失败证据、当前判断和下一步建议；未经用户确认不得继续绕路。

## 6. 验收标准

本轮最终 signoff 只有在以下条件全部满足时才能声明完成：

- 三个 workload 均完成 Stage 1 functional run 和 activity capture。
- 一个固定 Gemmini 配置完成 Stage 2 project-level high-confidence physical implementation。
- 三个 workload 均完成 Stage 3 grid-level power trace，且不是 proxy 1W normalization 结果。
- 三个 workload 均完成 Stage 4 PACT 主线热仿真、ATSim3D v1 独立 steady 热仿真和 HotSpot 粗对照。
- Stage 4 主 thermal artifacts 全部使用 DEF physical grid 坐标，并记录 PACT raw row-order 处理方式；raw-order 文件只作为 audit，不作为主结论。
- ATSim3D v1 `.res`、下采样 physical grid、热点排名和 ATSim-vs-PACT 对比均存在；若讨论标准单元级上下文，必须注明标准单元数据来自 Stage 3 placed instance grid map，而不是 ATSim `.res` 本身。
- Stage 4 SVG 图表均有同 basename PNG companion，便于 VS Code/远程环境预览。
- 所有产物集中在 `runs/GemminiRocketConfig__mesh16x16_tile1x1_dim16__signoff/` 下。
- run README、manifest、阶段报告和最终 signoff summary 均存在并能追溯输入输出。
- 旧 proxy 结果只作为参考，不作为当前验收证据。

## 7. 旧计划和旧结果的使用边界

`docs/phase0tophase4_plan.md`、`reports/stage*_tiled_matmul_os_baseline_*`、`physical/stage2_tiled_matmul_os_baseline_asap7/`、`power/stage3_tiled_matmul_os_baseline_*`、`thermal/pact/stage4_tiled_matmul_os_baseline/`、`thermal/hotspot/stage4_tiled_matmul_os_baseline/` 等旧产物只能用于理解脚本、路径、历史问题和方法参考。

不得把旧 proxy artifact 标记为当前 signoff artifact。若复用旧脚本，必须在新 run 目录下重新生成输出，并修正脚本默认路径，避免覆盖旧结果。
