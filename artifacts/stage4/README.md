# Stage 4 Artifacts: tiled_matmul_os Baseline

更新时间：2026-05-03

## 坐标标准

**所有主产物统一使用 DEF 物理坐标：`grid_y=0` 是 die bottom，`grid_y` 向上增加。**

2026-05-03 发现 PACT 原始输出的 row order 与该物理坐标相反：PACT raw row `0` 对应物理 die top。修复后规则固定为：

```text
physical_grid_y = 64 - 1 - pact_raw_row_y
```

因此：

- `pact_steady_layer0_grid.csv`、`pact_hotspot_rank.csv`、PACT heatmap、standard-cell overlay 均是修复后的物理坐标产物。
- `*_pact_raw_order.csv` 只用于审计和复查，**不得作为物理坐标报告或图上位置使用**。
- HotSpot 是五个 coarse block 的趋势对照，不是 placed standard-cell 物理分布。

## 修复证据

| 检查项 | 结果 |
| --- | --- |
| PACT raw hotspot | `(22, 47)` |
| PACT corrected physical hotspot | `(22, 16)` |
| ATSim vs corrected PACT corr | `0.972619` |
| ATSim vs PACT raw-order corr | `-0.141279` |
| corrected ATSim-PACT abs mean | `1.326156 K` |
| raw-order ATSim-PACT abs mean | `2.771164 K` |

## 三类工具的输入、流程和输出

| 工具 | 依赖输入 | 当前流程 | 应使用的输出 | 坐标/物理分布检查 |
| --- | --- | --- | --- | --- |
| PACT | `thermal/pact/stage4_tiled_matmul_os_baseline/` 的 raw steady/transient 结果、Stage 4 manifest | 读取 raw row-order 温度矩阵，执行 `physical_grid_y = 64 - 1 - pact_raw_row_y`，再生成 rank、stats、heatmap 和 manifest | `pact_steady_layer0_grid.csv`、`pact_hotspot_rank.csv`、`heatmap_steady_pact_layer0.png` | 主输出已经是 DEF physical y-up；`*_pact_raw_order.csv` 只用于审计 |
| HotSpot | `thermal/hotspot/stage4_tiled_matmul_os_baseline/` 的 coarse block `.ttrace` | 汇总五个 block 的 transient min/mean/max、final/peak rank，并生成趋势图 | `hotspot_transient_stats.csv`、`hotspot_block_rank.csv`、`hotspot_block_final.png` | 只用于 coarse trend sanity，不代表 placed standard-cell 物理分布 |
| ATSim3D v1 proxy | ATSim proxy rerun 结果、修复后的 PACT physical grid、PACT raw-order audit grid、HotSpot stats/rank | 下采样 ATSim fine grid 到 64/256，对修复后 PACT 做主差值，对 raw-order 做诊断差值 | `atsim3d_v1_proxy/atsim_minus_pact_64_grid.csv`、`heatmap_atsim_minus_pact_64.png`、`atsim_pact_coordinate_delta_comparison.csv` | 主对比必须使用 corrected PACT；raw-order 仅用来证明旧坐标解释错误 |

标准单元分布检查不来自热仿真器本身，而来自 Stage 3 placed instance map：`power/stage3_tiled_matmul_os_baseline_instance_grid_map.csv`。`standard_cell_context/` 把这个物理分布与修复后的 PACT 温度场叠加，检查温度、proxy power、instance density 是否在同一 DEF physical grid 上解释。

## PACT 主产物

| 文件 | 内容 |
| --- | --- |
| `pact_coordinate_fix_manifest.json` / `.csv` | PACT y 坐标现象、修复公式、raw/fixed hotspot 位置。 |
| `pact_steady_layer0_grid.csv` | 修复后的 PACT steady layer0，DEF physical y-up。 |
| `pact_steady_layer1_grid.csv` | 修复后的 PACT steady layer1，DEF physical y-up。 |
| `pact_transient_final_layer0_grid.csv` | 修复后的 PACT transient final layer0，DEF physical y-up。 |
| `pact_hotspot_rank.csv` | 修复后的 PACT steady layer0 top temperature grids。 |
| `heatmap_steady_pact_layer0.png` | 修复后的 PACT steady layer0 heatmap。 |
| `heatmap_transient_final_pact_layer0.png` | 修复后的 PACT transient final heatmap。 |
| `pact_steady_layer0_grid_pact_raw_order.csv` | PACT raw row-order audit copy，不用于物理解释。 |
| `pact_steady_layer1_grid_pact_raw_order.csv` | PACT raw row-order audit copy，不用于物理解释。 |
| `pact_transient_final_layer0_grid_pact_raw_order.csv` | PACT raw row-order audit copy，不用于物理解释。 |

## 标准单元上下文

`standard_cell_context/` 已用修复后的 PACT grid 重建。标准单元图表同时保留 SVG 和同名 PNG：SVG 用于矢量编辑/论文排版，PNG 用于 VS Code 和报告快速预览。主要入口：

| 文件 | 内容 |
| --- | --- |
| `standard_cell_context/standard_cell_grid_context.csv` | 每个 physical grid 的标准单元数量、面积、proxy power、power rank 和修复后 PACT 温度。 |
| `standard_cell_context/standard_cell_hotspot_context.csv` | 修复后 PACT top temperature grids 的标准单元反查。 |
| `standard_cell_context/standard_cell_grid_context.svg` / `.png` | 修复后 PACT 温度、标准单元 power、density、power density 四联图；PNG 用于 VS Code 快速查看。 |
| `standard_cell_context/standard_cell_hotspot_overlay.svg` / `.png` | top standard-cell instances 叠加到修复后的 PACT 温度图；PNG 用于 VS Code 快速查看。 |
| `standard_cell_context/standard_cell_region_share.svg` / `.png` | 标准单元 region 的 instance、area、proxy power share；PNG 用于 VS Code 快速查看。 |
| `standard_cell_context/standard_cell_master_power.svg` / `.png` | top standard-cell master 类型 power 贡献；PNG 用于 VS Code 快速查看。 |

## ATSim 对比

`atsim3d_v1_proxy/` 已用修复后的 PACT 主产物重建主对比；raw-order 只作为诊断保留。

| 文件 | 内容 |
| --- | --- |
| `atsim3d_v1_proxy/atsim_minus_pact_64_grid.csv` | ATSim - corrected PACT，physical y-up。 |
| `atsim3d_v1_proxy/heatmap_atsim_minus_pact_64.png` | ATSim - corrected PACT heatmap。 |
| `atsim3d_v1_proxy/atsim_pact_delta_summary.csv` | ATSim - corrected PACT 差值统计。 |
| `atsim3d_v1_proxy/atsim_pact_coordinate_delta_comparison.csv` | corrected vs raw-order 对比，证明 y-flip 修复有效。 |
| `atsim3d_v1_proxy/atsim_minus_pact_raw_order_64_grid.csv` | ATSim - PACT raw-order 诊断矩阵。 |
| `atsim3d_v1_proxy/atsim_pact_raw_order_delta_summary.csv` | raw-order 诊断差值统计。 |
| `atsim3d_v1_proxy/heatmap_atsim_minus_pact_raw_order_64.png` | raw-order 诊断 heatmap。 |

旧的 `*_yflip_*` ATSim 对比文件已从主产物集合移除，避免再次把“修复动作”和“物理主视图”混在一起。

## 复现命令

```bash
/home/lisihang/miniconda3/envs/thermal_placement/bin/python scripts/report_stage4_thermal_results.py
/home/lisihang/miniconda3/envs/thermal_placement/bin/python scripts/report_stage4_standard_cell_context.py
/home/lisihang/miniconda3/envs/thermal_placement/bin/python thermal/atsim3d_v1_proxy_stage4_tiled_matmul_os_baseline/scripts/generate_atsim_stage4_artifacts.py
```

这些命令只重建 Stage 4 后处理产物和图表，不重跑 PACT、HotSpot 或 ATSim 求解器。
