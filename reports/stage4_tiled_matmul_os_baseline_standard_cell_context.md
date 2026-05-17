# Stage 4 Standard-Cell Context Visualization

Date: 2026-05-03

## Scope

本报告只基于已经完成的 Stage 2-4 baseline 结果，说明当前成果里“标准单元”与 grid 级热结果的关系。这里没有进行热优化、没有新增 workload，也没有重跑 PACT 或 HotSpot。

## Data Chain

1. Stage 2 生成 ASAP7 标准单元实现，得到 placed standard-cell instances 和 DEF 坐标。
2. Stage 3 将 `1,333,998` 个 active standard-cell components 映射到 `64 x 64` grid，并把目标 GEMM 窗口 RTL activity 按区域分配为 normalized proxy power。
3. Stage 4 在同一 grid 上运行 PACT steady/transient 和 HotSpot coarse comparison；本报告把 Stage 3 的 cell/grid 聚合结果与 PACT layer0 稳态温度叠加展示。
4. 2026-05-03 后处理修复后，本报告读取的是已经转换到 DEF 物理坐标的 PACT grid：`grid_y=0` 是 die bottom，`grid_y` 向上增加。PACT 原始 row-order 只保留在 `_pact_raw_order` 产物中，不再用于标准单元叠加。

## Main Findings

- 标准单元功耗来源不是随机 grid：每个 grid bin 的 power 来自落在该 bin 内的 placed standard-cell instances 聚合。
- 当前 peak-normalized proxy power 总量为 `1.000000` W；最大贡献区域是 `gemmini_other`，占 `40.85%`。
- **坐标已修复**：PACT steady layer0 热点在 DEF 物理 grid `(22, 16)`，温度 `333.720` K，平均温度 `327.003` K。这里的 `grid_y=0` 是 die bottom，和 Stage 3 标准单元 `grid_y` 一致。
- Stage 3 标准单元 proxy power 最大 grid 在 `(35, 19)`，该 grid 聚合功耗 `8.681559e-04` W，包含 `529` 个 active standard-cell components。
- 温度热点和瞬时/局部功耗最高 grid 不完全重合，这是正常现象：稳态热扩散会把周围区域、边界条件和材料热传导共同反映到温度场中。
- 当前按 master 类型汇总的 top 类型为 `INVx3_ASAP7_75t_R`；结合单实例 Top-N 中的 `INVx13/INVx11/INVx8` 等单元，可以看到 inverter/buffer 类标准单元在当前 proxy 功耗归因中较突出。

## Figures and How to Read Them

- `artifacts/stage4/standard_cell_context/standard_cell_region_share.svg` / `.png`: 比较每个逻辑区域的标准单元实例数、cell area 和 proxy power share。SVG 保留矢量版本，PNG 用于 VS Code 和报告快速预览。
- `artifacts/stage4/standard_cell_context/standard_cell_grid_context.svg` / `.png`: 四联图。左上是修复后的 PACT 物理坐标稳态温度；右上是标准单元聚合 proxy power；左下是标准单元密度；右下是 proxy power / cell area。白色星号是 PACT 稳态热点，青色 X 是 proxy power 最高 grid。
- `artifacts/stage4/standard_cell_context/standard_cell_hotspot_overlay.svg` / `.png`: 在 PACT 温度图上叠加 top standard-cell instances。点越大代表单元 proxy power 越高，底图颜色代表温度。
- `artifacts/stage4/standard_cell_context/standard_cell_master_power.svg` / `.png`: 展示 proxy power 贡献最高的标准单元 master 类型，可用于描述哪些门级单元族在当前 proxy 模型中更突出。

## Tables

- `artifacts/stage4/standard_cell_context/standard_cell_grid_context.csv`: 每个 `64 x 64` grid 的标准单元数量、cell area、proxy power、power rank 和 PACT steady temperature。
- `artifacts/stage4/standard_cell_context/standard_cell_hotspot_context.csv`: 修复后的 PACT top temperature physical grids 与同 grid / 邻域标准单元聚合信息的反查表。
- `artifacts/stage4/standard_cell_context/standard_cell_top_instances.csv`: 当前 proxy power Top standard-cell instances，用于从图回到具体实例名和 master 类型。
- `artifacts/stage4/standard_cell_context/standard_cell_master_power_top.csv`: proxy power 贡献最高的 master 类型。

## Caveats

- 这些结果是 `proxy / thermal-flow prototype`，不是 signoff power 或 timing-closed implementation。
- Stage 3 功耗为 normalized proxy power，尚未使用 gate-level SAIF/SPEF/Liberty 做严格门级功耗。
- 当前热图仍是 grid 级温度，不是每个标准单元单独一个温度节点；标准单元研究体现在“实例级物理映射、区域/单元功耗归因、grid 热点反查”。
- **严禁把 PACT raw row-order 坐标当作物理坐标解读**；标准单元上下文只应使用 `artifacts/stage4/pact_steady_layer0_grid.csv` 这类已修复的 physical-coordinate 产物。
- SRAM macro body 没有做精细热源建模，当前展示主要覆盖 PE array、控制和近邻 datapath 的标准单元逻辑。

## Recommended Group-Meeting Description

目前已经完成从 Gemmini GEMM workload activity 到 ASAP7 标准单元实现、再到标准单元聚合功耗 grid 和 PACT/HotSpot 热仿真的闭环。新增展示把 grid 级热图反向连接到 placed standard-cell instances：可以看到不同逻辑区域的标准单元功耗占比、局部标准单元密度和 PACT 稳态热点之间的关系。当前还没有进行热优化，因此这些图主要作为 baseline 热画像和后续优化/sweep 的输入依据。
